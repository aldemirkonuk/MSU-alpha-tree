"""Reference identity assigner for config/identity_pack.yaml (spec tooling, not the production tracker).

Pipeline (each step is a section of the YAML):
  detections (no ids, with cue observations)
    -> tracklets   motion-only linking with the pair-swap and merge tests (pure by construction)
    -> chains      unambiguous continuations joined; other starts get a group mixture prior
    -> evidence    tempered cue log-likelihoods per detection and roster player
    -> solve       per frame and team, the exact joint label posterior under one-person-one-label,
                   with the identity state machine (lock, hold, re-confirm, alarm, release),
                   live (evidence so far) and offline (whole chain, change-point splits)
Every numeric parameter is read from the YAML at import (single source of truth).
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[3]
SPEC_PATH = ROOT / "config" / "identity_pack.yaml"

HOLD = -1
OFFICIAL = 2  # class index of officials / other people


# --------------------------------------------------------------------------------------
# Spec
# --------------------------------------------------------------------------------------
def load_spec(path=SPEC_PATH):
    return yaml.safe_load(Path(path).read_text())


def param_blocks(spec):
    """Yield (owner, params dict) for every params block in the spec."""
    for c in spec["cues"]:
        yield f"cues.{c['id']}", c.get("params") or {}
    for sec in ("cue_common", "tracklets", "chains", "assignment", "swap_catch", "confidence_and_abstention", "harness"):
        yield sec, spec[sec].get("params") or {}


def flat_params(spec):
    out = {}
    for owner, block in param_blocks(spec):
        for k, v in block.items():
            if k in out:
                raise ValueError(f"duplicate param name {k} ({owner})")
            out[k] = v["value"]
    return out


SPEC = load_spec()
P = flat_params(SPEC)


def frames(seconds, dt):
    return int(round(seconds / dt))


# --------------------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------------------
@dataclass
class Dets:
    """Detections of one game, sorted by frame. Cue arrays hold NaN / -1 where not observed."""
    dt: float
    n_frames: int
    frame: np.ndarray            # (D,) int
    xy: np.ndarray               # (D, 2) metres
    src: np.ndarray              # (D,) true person (roster index; -1 - k for official k) - harness truth only
    nocue: np.ndarray            # (D,) bool: merged or occluded box, no cue observations
    cls_obs: np.ndarray          # (D,) int: 0 / 1 team, 2 official, -1 none
    jersey: np.ndarray           # (D,) int code (see jersey_code), -1 none
    emb: np.ndarray | None       # (D, E) appearance sample or NaN
    height: np.ndarray | None    # (D,) height sample or NaN
    gait: np.ndarray | None      # (D, G) gait sample or NaN
    cut: np.ndarray              # (F,) bool: first frame after a camera cut / gap
    fov: np.ndarray              # (F, 2) x-range of the field of view (metres)
    fstart: np.ndarray = field(default=None)  # (F + 1,) offsets into the detection arrays

    def __post_init__(self):
        if self.fstart is None:
            self.fstart = np.searchsorted(self.frame, np.arange(self.n_frames + 1))

    @property
    def n(self):
        return len(self.frame)


@dataclass
class Game:
    """What the assigner knows: the reference pack and the lineup feed."""
    team: np.ndarray             # (N,) 0 / 1
    jersey: list                 # (N,) jersey number strings
    height_ref: np.ndarray       # (N,) m
    template: np.ndarray | None  # (N, E)
    gait_ref: np.ndarray | None  # (N, G)
    cand: np.ndarray             # (F, N) bool: candidate labels per frame (lineup, widened in substitution windows)

    @property
    def n(self):
        return len(self.team)


# --------------------------------------------------------------------------------------
# Jersey numbers
# --------------------------------------------------------------------------------------
NUMBERS = ["00"] + [str(i) for i in range(100)]
NUM_INDEX = {s: i for i, s in enumerate(NUMBERS)}
PARTIAL0 = 1000  # code of a partial read of digit d = PARTIAL0 + d
CONFUSABLE_DIGITS = {"1": "74", "7": "1", "3": "8", "8": "360", "6": "85", "5": "6", "0": "8", "4": "1"}


def confusables(num: str):
    """Numbers one confusable-digit substitution away from num (OCR shape pairs)."""
    out = set()
    for i, ch in enumerate(num):
        for alt in CONFUSABLE_DIGITS.get(ch, ""):
            cand = num[:i] + alt + num[i + 1:]
            if cand in NUM_INDEX and cand != num:
                out.add(cand)
    return sorted(out)


def jersey_code_full(num: str) -> int:
    return NUM_INDEX[num]


def jersey_ll_table(roster_numbers, e_ocr, share, e_partial):
    """LL[code, p] for every full code (0..100) and partial code (1000..1009), roster players p."""
    n = len(roster_numbers)
    full = np.zeros((len(NUMBERS), n))
    part = np.zeros((10, n))
    for p, num in enumerate(roster_numbers):
        conf = confusables(num)
        n_other = len(NUMBERS) - 1 - len(conf)
        for i, r in enumerate(NUMBERS):
            if r == num:
                full[i, p] = 1 - e_ocr
            elif r in conf:
                full[i, p] = e_ocr * share / len(conf)
            else:
                full[i, p] = e_ocr * (1 - share if conf else 1.0) / n_other
        digits = set(num)
        for d in range(10):
            part[d, p] = (1 - e_ocr) / len(digits) if str(d) in digits else e_partial
    return np.log(full), np.log(part)


# --------------------------------------------------------------------------------------
# Tracklets (YAML tracklets)
# --------------------------------------------------------------------------------------
@dataclass
class Tracklet:
    tid: int
    start: int
    dets: list
    end: int = -1
    reason: str = ""
    enc: list = field(default_factory=list)  # frames with another track within encounter_m
    amb: bool = False                         # an encounter segment (identity unknown inside; never labelled)
    group: int = -1                           # encounter group of an amb segment
    parents: list | None = None               # explicit parents (clean tracklet leaving an encounter group)


_STATS = {"pair_or_merge": 0, "newcomer": 0, "lead_guard": 0, "contested": 0, "jump": 0, "solo_nocue": 0, "unmatched_dets": 0, "unmatched_tracks": 0}


class _Groups:
    """Union-find of encounter groups; each root holds the clean tracklets (identities) that entered it."""

    def __init__(self):
        self.parent, self.entering = [], []

    def new(self, tids):
        self.parent.append(len(self.parent))
        self.entering.append(set(tids))
        return len(self.parent) - 1

    def root(self, g):
        while self.parent[g] != g:
            self.parent[g] = self.parent[self.parent[g]]
            g = self.parent[g]
        return g

    def union(self, a, b):
        ra, rb = self.root(a), self.root(b)
        if ra != rb:
            self.parent[rb] = ra
            self.entering[ra] |= self.entering[rb]
        return ra

    def members(self, g):
        return sorted(self.entering[self.root(g)])


def _near_fov_edge(x, fov_row, edge):
    return (x - fov_row[0] < edge) or (fov_row[1] - x < edge)


def build_tracklets(d: Dets, sigma_p: float, mode: str = "pure", prm=None, cues=("team",)):
    """Motion-only tracklets.

    mode 'pure' (YAML tracklets): a track that fails the pair-swap test, meets a merged / no-cue box or loses its
    detection next to another track enters an encounter group: its clean tracklet ends and an amb segment
    continues the motion; when it has passed every test for clear_s it leaves the group as a new clean tracklet
    whose parents are all identities that entered the group. No coasting.
    mode 'naive': a standard tracker - Hungarian through everything, coasting up to link_window_s.
    Returns (tracklets, det -> tracklet, groups).
    """
    prm = prm or P
    dt = d.dt
    sig0 = max(math.sqrt(2.0) * sigma_p, prm["sigma_floor_m"])
    pure = mode == "pure"
    CLb = class_evidence(d, set(cues), prm)  # opponent pairs are resolved by team colour, not cut
    log_pt = math.log(prm["p_team"] / (1 - prm["p_team"]))

    def cls_of(a):
        c = a["cls"]
        srt = np.sort(c)
        return int(np.argmax(c)) if srt[-1] - np.logaddexp(srt[0], srt[1]) >= log_pt else -1

    def opponents(a, b):
        ca, cb = cls_of(a), cls_of(b)
        return ca >= 0 and cb >= 0 and ca != cb
    coast_max = frames(prm["coast_max_s"], dt) if pure else frames(prm["link_window_s"], dt)
    clear_n = max(1, frames(prm["clear_s"], dt))
    det_trk = np.full(d.n, -1, dtype=np.int64)
    trks: list[Tracklet] = []
    G = _Groups()
    act = []  # dicts: tr, pos, vel, last, clear
    vanished = []  # recently ended tracks (pure): dicts tid, pos, vel, last, group
    W = frames(prm["link_window_s"], dt)

    def new_tracklet(j, f, amb=False, group=-1, parents=None):
        t = Tracklet(len(trks), f, [j] if j is not None else [], amb=amb, group=group, parents=parents)
        trks.append(t)
        if j is not None:
            det_trk[j] = t.tid
        return t

    def finish(t, last, reason, pos=None, a=None):
        if reason == "lost" and pos is not None and _near_fov_edge(pos[0], d.fov[last], prm["fov_edge_m"]):
            reason = "fov_exit"
        if pure and a is not None and not t.amb and reason in ("lost", "ambiguous", "fov_exit") and t.dets \
                and not _isolated_det(t.dets[-1]):
            # trailing guard: the last clear_s detections before a loss go to an amb segment (a swap made just
            # before the box was lost never reaches a labelled tracklet)
            tail = []
            while t.dets and d.frame[t.dets[-1]] > last - clear_n:
                tail.insert(0, t.dets.pop())
            if tail:
                g_ = a.get("group", -1)
                if g_ < 0:
                    g_ = G.new([t.tid] if t.dets else (t.parents or []))
                    a["group"] = g_
                seg = new_tracklet(None, int(d.frame[tail[0]]), amb=True, group=g_)
                seg.dets = tail
                det_trk[tail] = seg.tid
                seg.end, seg.reason = last, reason
                if t.dets:
                    t.end, t.reason = int(d.frame[t.dets[-1]]), reason
                else:
                    t.end, t.reason = last, "void"
                if reason != "fov_exit":
                    vanished.append({"tid": seg.tid, "pos": a["pos"].copy(), "vel": a["vel"].copy(), "last": last,
                                     "group": g_, "cls": cls_of(a)})
                return
        if pure and reason in ("lost", "ambiguous") and a is not None:
            vanished.append({"tid": t.tid, "pos": a["pos"].copy(), "vel": a["vel"].copy(), "last": last,
                             "group": t.group if t.amb else a.get("group", -1), "cls": cls_of(a)})
        t.end = last
        t.reason = reason

    def _isolated_det(j):
        f_ = d.frame[j]
        lo_, hi_ = d.fstart[f_], d.fstart[f_ + 1]
        oth = [k for k in range(lo_, hi_) if k != j]
        return not oth or np.min(np.hypot(*(d.xy[oth] - d.xy[j]).T)) > prm["isolation_m"]

    def a_tid(i):
        return act[i]["tr"].tid

    def enter_amb(a, f, j_now):
        """Switch track a into an amb segment from frame f (detection j_now joins the segment)."""
        t = a["tr"]
        if t.amb:
            return
        moved = []
        while t.dets and d.frame[t.dets[-1]] >= f - clear_n:  # decision delay: the last clear_s frames go with it
            moved.insert(0, t.dets.pop())
        if j_now is not None and j_now not in moved:
            moved.append(j_now)
        if t.dets:
            finish(t, int(d.frame[t.dets[-1]]), "ambiguous")
            g = G.new([t.tid])
        else:  # empty clean tracklet (started this frame): drop it, inherit its explicit parents
            t.reason, t.end = "void", f
            g = G.new(t.parents or [])
        seg = new_tracklet(None, int(d.frame[moved[0]]) if moved else f, amb=True, group=g)
        seg.dets = moved
        det_trk[moved] = seg.tid
        a["tr"], a["clear"] = seg, 0
        a["cls"] = CLb[moved].sum(0) if moved else np.zeros(3)
        return g

    for f in range(d.n_frames):
        lo, hi = d.fstart[f], d.fstart[f + 1]
        if d.cut[f] and act:
            for a in act:
                finish(a["tr"], a["last"], "cut")
            act = []
        if d.cut[f]:
            vanished.clear()
        vanished[:] = [v for v in vanished if f - v["last"] <= W]
        idx = np.arange(lo, hi)
        T, M = len(act), len(idx)
        matched = {}
        C = None
        if T and M:
            gap = np.array([f - a["last"] for a in act], dtype=float)
            pred = np.array([a["pos"] + a["vel"] * g * dt for a, g in zip(act, gap)])
            sig = sig0 * (1.0 + 0.5 * (gap - 1.0))
            gate = prm["gate_base_m"] * gap + prm["gate_k"] * sig
            C = ((pred[:, None, :] - d.xy[idx][None, :, :]) ** 2).sum(-1)
            feas = C <= gate[:, None] ** 2
            r, c = linear_sum_assignment(np.where(feas, C, 1e9))
            for i, j in zip(r, c):
                if feas[i, j]:
                    matched[i] = j
        elif T:
            gap = np.array([f - a["last"] for a in act], dtype=float)
            pred = np.array([a["pos"] + a["vel"] * g * dt for a, g in zip(act, gap)])
            sig = sig0 * (1.0 + 0.5 * (gap - 1.0))
        bad_pairs, solo_bad, contested, jumped = [], set(), {}, set()
        if pure and T:
            I = np.array(sorted(matched))
            if len(I) > 1:
                J = np.array([matched[i] for i in I])
                Cs = C[np.ix_(I, J)]
                dg = np.diag(Cs)
                s2 = 0.5 * (sig[I][:, None] ** 2 + sig[I][None, :] ** 2)
                llr = (Cs + Cs.T - dg[:, None] - dg[None, :]) / (2 * s2)
                np.fill_diagonal(llr, np.inf)
                for u, v in np.argwhere(np.triu(llr < prm["swap_llr_min"], 1)):
                    iu, iv = int(I[u]), int(I[v])
                    if not opponents(act[iu], act[iv]):
                        bad_pairs.append((iu, iv))
                    else:  # colour veto: a detection whose observed class contradicts its track's class
                        for x in (iu, iv):
                            co = d.cls_obs[idx[matched[x]]]
                            if co >= 0 and co != cls_of(act[x]):
                                bad_pairs.append((iu, iv))
                                break
            for i, jj in matched.items():  # jump test: an innovation no motion noise explains
                if C[i, jj] > (prm["jump_k"] * sig[i]) ** 2 and f - act[i]["last"] == 1:
                    solo_bad.add(i)
                    jumped.add(i)
            for i in range(T):
                nocue_hit = i in matched and d.nocue[idx[matched[i]]]
                if i in matched and not nocue_hit:
                    continue
                rad = prm["merge_base_m"] + prm["merge_k"] * sig[i]
                ref = d.xy[idx[matched[i]]] if i in matched else pred[i]
                dtr = np.hypot(*(pred - ref).T)
                near = [int(k) for k in np.where(dtr < rad)[0] if k != i and not opponents(act[i], act[k])]
                if near:
                    bad_pairs.extend((i, k) for k in near)
                elif nocue_hit:
                    solo_bad.add(i)
            # contested detection: a matched detection within reach of a person who vanished < contest_s ago
            CW = frames(prm["contest_s"], dt)
            for i, jj in matched.items():
                ci = cls_of(act[i])
                for v in vanished:
                    g_ = f - v["last"]
                    if g_ > CW or v["tid"] == a_tid(i) or act[i]["born"] > v["last"] or \
                            (ci >= 0 and v["cls"] >= 0 and v["cls"] != ci):
                        continue
                    tg = g_ * dt
                    sv = sig0 + (prm["v_err_mps"] * tg + 0.5 * prm["a_max_mps2"] * tg**2) / 3.0
                    di2 = C[i, jj]
                    dv2 = float(np.sum((d.xy[idx[jj]] - (v["pos"] + v["vel"] * tg)) ** 2))
                    llr = (-di2 / (2 * sig[i] ** 2) - 2 * math.log(sig[i])) - (-dv2 / (2 * sv**2) - 2 * math.log(sv)) \
                        + prm["contest_prior_nats"]
                    if llr < prm["swap_llr_min"]:
                        contested.setdefault(i, []).append(v)
            solo_bad.update(contested)
        # apply: matched tracks extend (clean or amb); ambiguity moves tracks into amb segments
        newly_bad = {i for pr in bad_pairs for i in pr} | solo_bad
        if pure:
            _STATS["pair_or_merge"] += len({i for pr in bad_pairs for i in pr})
            _STATS["solo_nocue"] += len(solo_bad - set(contested))
            _STATS["contested"] += len(contested)
            _STATS["jump"] += len(jumped)
            _STATS["unmatched_dets"] += M - len(matched)
            _STATS["unmatched_tracks"] += T - len(matched)
        for i, a in enumerate(act):
            if i in matched:
                j = idx[matched[i]]
                res = d.xy[j] - pred[i]
                a["pos"] = pred[i] + prm["pos_alpha"] * res
                a["vel"] = a["vel"] + prm["vel_beta"] * res / ((f - a["last"]) * dt)
                a["last"] = f
                a["tr"].dets.append(j)
                a["cls"] = a.get("cls", np.zeros(3)) + CLb[j]
                det_trk[j] = a["tr"].tid
        for i in sorted(newly_bad):
            a = act[i]
            j = idx[matched[i]] if i in matched else None
            if i in matched:
                enter_amb(a, f, j)
            else:
                t = a["tr"]
                if not t.amb:
                    finish(t, a["last"], "ambiguous", a=a)
                    if a.get("group", -1) < 0:
                        a["group"] = G.new([t.tid])
        for u, v in bad_pairs:
            gu = act[u]["tr"].group if act[u]["tr"].amb else act[u].get("group", -1)
            gv = act[v]["tr"].group if act[v]["tr"].amb else act[v].get("group", -1)
            if gu >= 0 and gv >= 0:
                G.union(gu, gv)
        if pure:
            for i in jumped:
                gi = act[i]["tr"].group
                for v in vanished:
                    g_ = f - v["last"]
                    reach = prm["reach_base_m"] + prm["v_max_mps"] * g_ * dt + 3 * sig0
                    if np.hypot(*(v["pos"] - d.xy[idx[matched[i]]])) <= reach:
                        gv = v["group"] if v["group"] >= 0 else G.new([v["tid"]])
                        v["group"] = gv
                        gi = G.union(gi, gv)
            for i, vs in contested.items():
                gi = act[i]["tr"].group if act[i]["tr"].amb else act[i].get("group", -1)
                for v in vs:
                    gv = v["group"] if v["group"] >= 0 else G.new([v["tid"]])
                    v["group"] = gv
                    if gi >= 0:
                        gi = G.union(gi, gv)
        new_act, used = [], set(matched.values())
        for i, a in enumerate(act):
            t = a["tr"]
            if i not in matched:
                if t.amb:
                    finish(t, a["last"], "lost", a=a)
                elif t.reason != "ambiguous":
                    finish(t, a["last"], "lost", a["pos"], a=a) if (f - a["last"]) > coast_max else None
                if t.reason == "" and (f - a["last"]) <= coast_max:
                    new_act.append(a)
                continue
            if t.amb and i not in newly_bad:
                a["clear"] += 1
                if a["clear"] >= clear_n:  # leaves the encounter group as a new clean tracklet
                    k = a["clear"]
                    tail = t.dets[-k:]
                    del t.dets[-k:]
                    finish(t, int(d.frame[t.dets[-1]]) if t.dets else f, "ambiguous")
                    nt = new_tracklet(None, int(d.frame[tail[0]]), parents=G.members(t.group))
                    nt.dets = list(tail)
                    det_trk[tail] = nt.tid
                    a["tr"] = nt
                    a["cls"] = CLb[tail].sum(0)
            elif t.amb:
                a["clear"] = 0
            new_act.append(a)
        act = new_act
        for jj in range(M):
            if jj in used:
                continue
            j = idx[jj]
            na = {"tr": None, "pos": d.xy[j].copy(), "vel": np.zeros(2), "last": f, "clear": 0, "cls": CLb[j].copy(), "born": f}
            nb = []
            if pure:  # newcomer test: a person appearing next to a tracked one makes both ambiguous
                rad = prm["merge_base_m"] + prm["merge_k"] * sig0
                nb = [a for a in act if a["last"] == f and np.hypot(*(a["pos"] - d.xy[j])) < rad]
            if pure and not nb and not _isolated_det(j):
                _STATS["lead_guard"] += 1
                g0 = G.new([])
                for v in vanished:  # who could this be: identities that vanished within reach
                    g_ = f - v["last"]
                    reach = prm["reach_base_m"] + prm["v_max_mps"] * g_ * dt + 3 * sig0
                    if np.hypot(*(v["pos"] - d.xy[j])) <= reach:
                        gv = v["group"] if v["group"] >= 0 else G.new([v["tid"]])
                        v["group"] = gv
                        g0 = G.union(g0, gv)
                na["tr"] = new_tracklet(j, f, amb=True, group=g0)
            elif nb:
                _STATS["newcomer"] += 1
                gs = [enter_amb(a, f, None) if not a["tr"].amb else a["tr"].group for a in nb]
                g0 = gs[0]
                for g_ in gs[1:]:
                    g0 = G.union(g0, g_)
                for v in vanished:  # identities that vanished within reach may be the newcomer
                    g_ = f - v["last"]
                    reach = prm["reach_base_m"] + prm["v_max_mps"] * g_ * dt + 3 * sig0
                    if np.hypot(*(v["pos"] - d.xy[j])) <= reach:
                        gv = v["group"] if v["group"] >= 0 else G.new([v["tid"]])
                        v["group"] = gv
                        g0 = G.union(g0, gv)
                seg = new_tracklet(j, f, amb=True, group=g0)
                na["tr"] = seg
            else:
                na["tr"] = new_tracklet(j, f)
            act.append(na)
        cur = [a for a in act if a["last"] == f]
        if len(cur) > 1:
            pos = np.array([a["pos"] for a in cur])
            dd = np.hypot(pos[:, None, 0] - pos[None, :, 0], pos[:, None, 1] - pos[None, :, 1])
            np.fill_diagonal(dd, np.inf)
            for u in np.where((dd < prm["encounter_m"]).any(1))[0]:
                cur[u]["tr"].enc.append(f)
    for a in act:
        if a["tr"].reason == "":
            finish(a["tr"], a["last"], "end")
    trks = [t for t in trks if t.dets]
    remap = {t.tid: k for k, t in enumerate(trks)}
    for t in trks:
        t.tid = remap[t.tid]
        if t.parents is not None:
            t.parents = sorted({remap[p] for p in t.parents if p in remap})
    for k, t in enumerate(trks):
        det_trk[t.dets] = k
    groups = {t.tid: sorted({remap[p] for p in G.members(t.group) if p in remap}) for t in trks if t.amb}
    return trks, det_trk, groups


# --------------------------------------------------------------------------------------
# Chains (YAML chains)
# --------------------------------------------------------------------------------------
@dataclass
class Chain:
    cid: int
    dets: np.ndarray            # detection indices in frame order
    parents: list               # chain ids whose identities form this chain's mixture prior ([] = uniform)
    enc: list                   # encounter frames (candidate split points)
    kind: str = "root"          # root | group | split


def link_chains(trks, det_trk, d: Dets, sigma_p, mode="pure", prm=None, groups=None):
    """Chains: unique continuations joined, group children get mixture parents, amb segments stay unlabelled."""
    prm = prm or P
    groups = groups or {}
    dt = d.dt
    W = frames(prm["link_window_s"], dt)
    sig_pair = max(math.sqrt(2.0) * sigma_p, prm["sigma_floor_m"])
    ncut = np.cumsum(d.cut.astype(int))
    order = sorted(range(len(trks)), key=lambda t: (trks[t].start, t))
    start_xy = {t.tid: d.xy[t.dets[0]] for t in trks}
    end_xy = {t.tid: d.xy[t.dets[-1]] for t in trks}
    ended = sorted(trks, key=lambda t: t.end)
    parents_of = {}
    ptr = 0
    recent = []

    def resolve(tids, s, seen=None):
        """Identities behind parent candidates: amb segments resolve to their group's members; only tracklets
        that ended before s can be parents."""
        seen = set() if seen is None else seen
        out = set()
        for x in tids:
            if x in seen:
                continue
            seen.add(x)
            if trks[x].amb:
                out |= resolve(groups.get(x, []), s, seen)
            elif trks[x].end < s:
                out.add(x)
        return out

    for t in order:
        tr = trks[t]
        if tr.amb:
            parents_of[t] = []
            continue
        if tr.parents is not None:
            parents_of[t] = sorted(resolve(tr.parents, tr.start))
            continue
        s = tr.start
        while ptr < len(ended) and ended[ptr].end < s:
            recent.append(ended[ptr])
            ptr += 1
        recent = [u for u in recent if u.end >= s - W]
        cands = []
        entry = mode == "pure" and _near_fov_edge(start_xy[t][0], d.fov[s], prm["fov_edge_m"])
        if not entry:
            for u in recent:
                if u.reason == "cut" or ncut[s] != ncut[u.end]:
                    continue
                if mode == "pure" and u.reason == "fov_exit":
                    continue
                reach = prm["reach_base_m"] + prm["v_max_mps"] * (s - u.end) * dt + 3 * sig_pair
                if np.hypot(*(end_xy[u.tid] - start_xy[t])) <= reach:
                    cands.append(u.tid)
        parents_of[t] = sorted(resolve(cands, s))
    children = {}
    for t, ps in parents_of.items():
        for u in ps:
            children.setdefault(u, []).append(t)

    def isolated(j, xy):
        f = d.frame[j]
        lo, hi = d.fstart[f], d.fstart[f + 1]
        others = [k for k in range(lo, hi) if k != j]
        return not others or np.min(np.hypot(*(d.xy[others] - xy).T)) > prm["isolation_m"]

    chain_of = {}
    chains: list[Chain] = []
    tdets = {}
    taken = set()
    for t in order:
        tr = trks[t]
        ps = parents_of[t]
        joined = None
        if tr.amb:
            cid = len(chains)
            chains.append(Chain(cid, None, [], list(tr.enc), "amb"))
            tdets[cid] = list(tr.dets)
            chain_of[t] = cid
            continue
        if mode == "pure":
            if (tr.parents is None and len(ps) == 1 and ps[0] in chain_of and children.get(ps[0]) == [t]
                    and trks[ps[0]].reason == "lost"
                    and isolated(tr.dets[0], start_xy[t]) and isolated(trks[ps[0]].dets[-1], end_xy[ps[0]])):
                joined = ps[0]
        else:  # naive: nearest free parent, inherit
            free = [u for u in ps if u not in taken and u in chain_of]
            if free:
                joined = min(free, key=lambda u: np.hypot(*(end_xy[u] - start_xy[t])))
                taken.add(joined)
        if joined is not None:
            cid = chain_of[joined]
            tdets[cid].extend(tr.dets)
            chains[cid].enc.extend(tr.enc)
            chains[cid].enc.append(int(tr.start))  # every join is a candidate split point
        else:
            cid = len(chains)
            pc = sorted({chain_of[u] for u in ps if u in chain_of})
            chains.append(Chain(cid, None, pc, list(tr.enc), "group" if pc else "root"))
            tdets[cid] = list(tr.dets)
        chain_of[t] = cid
    for c in chains:
        c.dets = np.array(sorted(tdets[c.cid], key=lambda j: d.frame[j]), dtype=np.int64)
    return chains


# --------------------------------------------------------------------------------------
# Evidence (YAML cues)
# --------------------------------------------------------------------------------------
def class_evidence(d: Dets, cues, prm=None):
    prm = prm or P
    CL = np.zeros((d.n, 3))
    if "team" not in cues:
        return CL
    e = prm["e_team"]
    lt, lf = math.log(1 - e), math.log(e / 2)
    m = d.cls_obs >= 0
    CL[m] = lf
    CL[np.where(m)[0], d.cls_obs[m]] = lt
    return CL * prm["tau_team"]


def confusable_pairs(g: Game, cues, prm=None):
    """(N, N) bool: teammates whose appearance + height evidence separates them slower than confusable_rate.

    Expected log-likelihood ratio per second between a and b: appearance tau x kappa x (1 - cos(t_a, t_b)) plus height
    tau x (dh / sigma_h)^2 / 2, per cue sample, divided by cue_stride_s. This is the per-game confusion list of the
    reference pack (same-team same-build pairs).
    """
    prm = prm or P
    N = g.n
    rate = np.zeros((N, N))
    if "appearance" in cues and g.template is not None:
        rate += prm["tau_app"] * prm["kappa_app"] * (1 - g.template @ g.template.T)
    if "height" in cues:
        dh = g.height_ref[:, None] - g.height_ref[None, :]
        rate += prm["tau_height"] * (1 - prm["outlier_h"]) * 0.5 * (dh / prm["sigma_h"]) ** 2
    rate /= prm["cue_stride_s"]
    same = (g.team[:, None] == g.team[None, :]) & ~np.eye(N, dtype=bool)
    return same & (rate < prm["confusable_rate"])


def own_evidence(d: Dets, g: Game, cues, prm=None):
    """Tempered LL (D, N) of appearance, height and gait (jersey added per chain, see jersey_evidence)."""
    prm = prm or P
    EV = np.zeros((d.n, g.n))
    if "appearance" in cues and d.emb is not None and g.template is not None:
        m = ~np.isnan(d.emb[:, 0])
        EV[m] += prm["tau_app"] * prm["kappa_app"] * (d.emb[m] @ g.template.T)
    if "height" in cues and d.height is not None:
        m = ~np.isnan(d.height)
        z = (d.height[m, None] - g.height_ref[None, :]) / prm["sigma_h"]
        dens = (1 - prm["outlier_h"]) * np.exp(-0.5 * z**2) / (prm["sigma_h"] * math.sqrt(2 * math.pi)) \
            + prm["outlier_h"] / (prm["h_hi"] - prm["h_lo"])
        EV[m] += prm["tau_height"] * np.log(dens)
    if "gait" in cues and d.gait is not None and g.gait_ref is not None:
        m = ~np.isnan(d.gait[:, 0])
        EV[m] += prm["tau_gait"] * prm["kappa_gait"] * (d.gait[m] @ g.gait_ref.T)
    return EV


def jersey_evidence(d: Dets, g: Game, chains, cues, prm=None, cap=True):
    """Jersey LL (D, N): each sighting (run of reads on one chain, gaps <= sighting_gap_s) counts once.

    cap=True limits each sighting's contrast to sighting_cap_nats (used for locking); the uncapped version is
    used by the offline change-point test, where more evidence can only add splits (HOLD), never labels.
    """
    prm = prm or P
    J = np.zeros((d.n, g.n))
    if "jersey" not in cues:
        return J
    full, part = jersey_ll_table(g.jersey, prm["e_ocr"], prm["confusable_share"], prm["e_partial"])
    gapf = max(1, frames(prm["sighting_gap_s"], d.dt))
    for c in chains:
        rd = c.dets[d.jersey[c.dets] >= 0]
        if len(rd) == 0:
            continue
        fr = d.frame[rd]
        brk = np.where(np.diff(fr) > gapf)[0] + 1
        for run in np.split(rd, brk):
            w = prm["tau_jersey"] / len(run)
            rows = np.array([full[c_] if c_ < PARTIAL0 else part[c_ - PARTIAL0] for c_ in d.jersey[run]])
            # one sighting may favour a label by at most sighting_cap_nats (one misread never locks an identity)
            if cap:
                rows = np.maximum(rows - rows.max(1, keepdims=True), -prm["sighting_cap_nats"])
            J[run] = w * rows
    return J


# --------------------------------------------------------------------------------------
# Joint posterior (YAML assignment)
# --------------------------------------------------------------------------------------
@lru_cache(maxsize=None)
def _maps(m, n):
    return np.array(list(itertools.permutations(range(m), n)), dtype=np.int64).reshape(-1, n)


def n_maps(m, n):
    return math.perm(m, n) if n <= m else 0


def joint_marginals(S, max_enum):
    """S (n, m) chain-label scores, n <= m. Exact marginals of injective maps; independent softmax if too many maps."""
    n, m = S.shape
    if n_maps(m, n) > max_enum:
        Z = S - S.max(1, keepdims=True)
        E = np.exp(Z)
        return E / E.sum(1, keepdims=True), False
    Pm = _maps(m, n)
    tot = S[np.arange(n)[None, :], Pm].sum(1)
    w = np.exp(tot - tot.max())
    w /= w.sum()
    marg = np.zeros((n, m))
    np.add.at(marg, (np.tile(np.arange(n), len(Pm)), Pm.ravel()), np.repeat(w, n))
    return marg, True


# --------------------------------------------------------------------------------------
# Solver with the identity state machine
# --------------------------------------------------------------------------------------
@dataclass
class Result:
    label: np.ndarray            # (D,) emitted label or HOLD
    post: np.ndarray             # (D,) posterior of the emitted label (or of the best label when HOLD)
    log: list                    # switch log rows (dicts)
    chains: list
    det_chain: np.ndarray
    stats: dict


def _cum_tables(chains, EV, CL, n_dets):
    """Per chain cumulative own evidence; returns det -> (chain, k) maps and stacked cumsums."""
    det_chain = np.full(n_dets, -1, dtype=np.int64)
    det_k = np.full(n_dets, -1, dtype=np.int64)
    ptr = np.zeros(len(chains) + 1, dtype=np.int64)
    for c in chains:
        ptr[c.cid + 1] = len(c.dets)
    ptr = np.cumsum(ptr)
    order = np.concatenate([c.dets for c in chains]) if chains else np.zeros(0, dtype=np.int64)
    CUM = np.zeros((len(order), EV.shape[1]))
    CUMC = np.zeros((len(order), 3))
    for c in chains:
        a, b = ptr[c.cid], ptr[c.cid + 1]
        CUM[a:b] = np.cumsum(EV[c.dets], 0)
        CUMC[a:b] = np.cumsum(CL[c.dets], 0)
        det_chain[c.dets] = c.cid
        det_k[c.dets] = np.arange(b - a)
    return det_chain, det_k, ptr, CUM, CUMC


def split_chains(chains, d: Dets, EV, CL, g: Game, prm=None):
    """Offline change-point splits at encounters (YAML swap_catch rule 3)."""
    prm = prm or P
    out, log = [], []
    nid = 0

    def best_split(dets, enc, team_lab):
        """Best change point at an encounter: label evidence within the team, or class evidence (opponent swap).

        Returns (gain, k_lo, k_hi): every encounter whose gain is within split_tie_nats of the best lies in
        [k_lo, k_hi]; the swap happened somewhere there, so that interval is left unlabelled.
        """
        cum = np.cumsum(EV[np.ix_(dets, team_lab)], 0)
        cumc = np.cumsum(CL[dets], 0)
        tot, totc = cum[-1], cumc[-1]
        fr = d.frame[dets]
        ks, gs = [], []
        for e in sorted(set(enc)):
            k = int(np.searchsorted(fr, e))
            if k < 1 or k > len(dets) - 1:
                continue
            gl = cum[k - 1].max() + (tot - cum[k - 1]).max() - tot.max()
            gc = cumc[k - 1].max() + (totc - cumc[k - 1]).max() - totc.max()
            ks.append(k)
            gs.append(max(gl, gc))
        if not ks:
            return 0.0, None, None
        gs = np.array(gs)
        best = float(gs.max())
        near = [k for k, g_ in zip(ks, gs) if g_ >= best - prm["split_tie_nats"]]
        return best, min(near), max(near)

    for c in chains:
        cls = int(np.argmax(CL[c.dets].sum(0)))
        if cls == OFFICIAL or not c.enc or c.kind == "amb":
            parts = [(c.dets, c.parents, c.kind)]
        else:
            team_lab = np.where(g.team == cls)[0]
            parts, todo, nsplit = [], [(c.dets, c.parents, c.kind)], 0
            while todo:
                dets, par, kind = todo.pop(0)
                encs = [e for e in c.enc if d.frame[dets[0]] < e <= d.frame[dets[-1]]]
                gain, k, k2 = best_split(dets, encs, team_lab) if (encs and nsplit < prm["max_splits"]) else (0.0, None, None)
                if k is not None and gain >= prm["split_llr_min"]:
                    nsplit += 1
                    log.append({"kind": "offline_split", "chain": c.cid, "frame": int(d.frame[dets[k]]),
                                "frame_last": int(d.frame[dets[k2]]), "gain_nats": round(float(gain), 2)})
                    todo.insert(0, (dets[k2:], [], "split"))
                    if k2 > k:
                        parts.append((dets[k:k2], [], "amb"))  # where in this interval the swap happened is unknown
                    todo.insert(0, (dets[:k], par, kind))
                else:
                    parts.append((dets, par, kind))
        for dets, par, kind in parts:
            out.append((c.cid, dets, par, kind))
    # renumber, mapping parent ids to the last part of each original chain
    last_part = {}
    newc = []
    for oc, dets, par, kind in out:
        newc.append(Chain(nid, dets, par, [e for e in chains[oc].enc if d.frame[dets[0]] < e <= d.frame[dets[-1]]], kind))
        last_part[oc] = nid
        nid += 1
    for c in newc:
        c.parents = sorted({last_part[p] for p in c.parents})
    return newc, log


def _restricted_prior(mixv, cand, eps):
    """(1 - eps) x mixture restricted to the candidates (renormalised) + eps x uniform; uniform when no mixture."""
    m = len(cand)
    if mixv is None:
        return np.full(m, 1.0 / m)
    mv = mixv[cand]
    tot = mv.sum()
    return (1 - eps) * (mv / tot) + eps / m if tot > 1e-12 else np.full(m, 1.0 / m)


def directional_mixtures(chains, d: Dets, EV, CL, g: Game, prm=None):
    """Offline forward and backward identity messages through the chain graph (YAML chains, DP7).

    fwd_mix[c] = mean over parents of their forward posterior; bwd_mix[c] = mean over children of their backward
    posterior. Each directional posterior uses only that direction's prior and the chain's own evidence, so the
    final score log fwd + log bwd + own counts every cue once.
    """
    prm = prm or P
    eps = prm["leak_eps"]
    nC = len(chains)
    team, cands, own_tot = [None] * nC, [None] * nC, [None] * nC
    for c in chains:
        if c.kind == "amb":
            continue
        k = int(np.argmax(CL[c.dets].sum(0)))
        if k == OFFICIAL:
            continue
        fr = d.frame[c.dets]
        cm = g.cand[fr].any(0) & (g.team == k)
        if not cm.any():
            continue
        team[c.cid], cands[c.cid], own_tot[c.cid] = k, np.where(cm)[0], EV[c.dets].sum(0)
    children = [[] for _ in range(nC)]
    for c in chains:
        for p_ in c.parents:
            children[p_].append(c.cid)

    def post(cid, mixv):
        cand = cands[cid]
        sc = np.log(_restricted_prior(mixv, cand, eps)) + own_tot[cid][cand]
        e = np.exp(sc - sc.max())
        out = np.zeros(g.n)
        out[cand] = e / e.sum()
        return out

    def mixture(ids, posts):
        vec = [posts[i] if posts[i] is not None else np.full(g.n, 1.0 / g.n) for i in ids]
        return np.mean(vec, 0) if vec else None

    order = sorted(range(nC), key=lambda i: d.frame[chains[i].dets[0]])
    fwd_mix, fwd_post = [None] * nC, [None] * nC
    for cid in order:
        fwd_mix[cid] = mixture(chains[cid].parents, fwd_post)
        if team[cid] is not None:
            fwd_post[cid] = post(cid, fwd_mix[cid])
    bwd_mix, bwd_post = [None] * nC, [None] * nC
    for cid in reversed(order):
        bwd_mix[cid] = mixture(children[cid], bwd_post)
        if team[cid] is not None:
            bwd_post[cid] = post(cid, bwd_mix[cid])
    return fwd_mix, bwd_mix


def solve(d: Dets, g: Game, chains, EV, CL, cfg, mode="live", prm=None, J=None, conf=None):
    """Run the identity state machine frame by frame. mode 'live' (evidence so far) or 'offline' (whole chain)."""
    prm = prm or P
    abstain, alarms = cfg.get("abstain", True), cfg.get("alarms", True)
    det_chain, det_k, ptr, CUM, CUMC = _cum_tables(chains, EV, CL, d.n)
    nC = len(chains)
    has_cue = np.any(EV != 0, axis=1)  # the detection carries at least one identity cue sample
    order = np.concatenate([c.dets for c in chains]) if chains else np.zeros(0, dtype=np.int64)
    CUMN = np.zeros(len(order), dtype=np.int64)
    for c in chains:
        CUMN[ptr[c.cid]:ptr[c.cid + 1]] = np.cumsum(has_cue[c.dets])
    own_min = prm["own_margin_nats"]
    conf = np.zeros((g.n, g.n), dtype=bool) if conf is None else conf
    CUMJ = None
    if conf.any() and J is not None:  # jersey-only cumulative evidence, needed to lock against a confusable teammate
        CUMJ = np.zeros((len(order), g.n), dtype=np.float32)
        for c in chains:
            CUMJ[ptr[c.cid]:ptr[c.cid + 1]] = np.cumsum(J[c.dets], 0)

    def twin_ok(cid, k, L, cand):
        """A label with a confusable teammate among the candidates needs jersey evidence against that teammate."""
        tw = [t for t in cand if conf[L, t]]
        if not tw:
            return True
        if CUMJ is None:
            return False
        a = ptr[cid]
        jv = CUMJ[ptr[cid + 1] - 1] if mode == "offline" else CUMJ[a + k] - (CUMJ[a + k_off[cid] - 1] if k_off[cid] > 0 else 0)
        return all(jv[L] - jv[t] >= prm["twin_jersey_nats"] for t in tw)

    label = np.full(d.n, HOLD, dtype=np.int64)
    post = np.zeros(d.n)
    log = []
    starts = {}
    for c in chains:
        starts.setdefault(int(d.frame[c.dets[0]]), []).append(c.cid)
    last_marg = [None] * nC          # live: (N,) joint marginal of the chain at its latest team frame
    mix = [None] * nC                # live: parent mixture (None = uniform)
    locked = np.full(nC, -1, dtype=np.int64)
    k_off = np.zeros(nC, dtype=np.int64)  # live alarm split: evidence restarts at this k
    eps, p_lock, p_unlock = prm["leak_eps"], prm["p_lock"], prm["p_unlock"]
    log_dummy = math.log(prm["dummy_eps"])
    log_pt = math.log(prm["p_team"] / (1 - prm["p_team"]))
    cw = max(1, frames(prm["class_window_s"], d.dt))
    stats = {"enum_fallback_frames": 0, "alarms": 0, "class_alarms": 0, "dup_guard": 0, "releases": 0, "colour_hold": 0}
    cues_used = set(cfg.get("cues", ["team", "jersey", "appearance", "height", "gait"]))
    enc_sets = [np.array(sorted(set(c.enc))) for c in chains]
    if mode == "offline":
        fwd_mix, bwd_mix = directional_mixtures(chains, d, EV, CL, g, prm)
        mean_marg = np.zeros((nC, g.n))
        MARGF = np.zeros((d.n, g.n), dtype=np.float32)
        SNEF = np.full((d.n, g.n), -np.inf, dtype=np.float32)
        OWNF = np.full((d.n, g.n), -np.inf, dtype=np.float32)
        in_team = np.zeros(d.n, dtype=bool)

    def own(cid, k):
        a = ptr[cid]
        if mode == "offline":
            return CUM[ptr[cid + 1] - 1], CUMC[ptr[cid + 1] - 1]
        o, oc = CUM[a + k], CUMC[a + k]
        if k_off[cid] > 0:
            o = o - CUM[a + k_off[cid] - 1]
            oc = oc - CUMC[a + k_off[cid] - 1]
        return o, oc

    def alarm(cid, j, f, kind, extra):
        locked_from = int(locked[cid])
        locked[cid] = -1
        enc = enc_sets[cid]
        enc = enc[enc <= f]
        k_split = det_k[j]
        if len(enc):
            fr = d.frame[chains[cid].dets]
            k_split = max(1, int(np.searchsorted(fr, enc[-1])))
        k_off[cid] = k_split
        mix[cid] = None
        log.append({"kind": kind, "frame": f, "chain": int(cid), "from": locked_from,
                    "split_frame": int(d.frame[chains[cid].dets[k_split]]), **extra})

    for f in range(d.n_frames):
        if mode == "live":
            for cid in starts.get(f, []):
                ps = chains[cid].parents
                if ps:
                    vecs = [last_marg[p_] if last_marg[p_] is not None else np.full(g.n, 1.0 / g.n) for p_ in ps]
                    mix[cid] = np.mean(vecs, 0)
        lo, hi = d.fstart[f], d.fstart[f + 1]
        if hi == lo:
            continue
        per_team = {0: [], 1: []}
        seen = {0: 0, 1: 0}  # detections of each team in this frame (for the adaptive leak)
        for j in range(lo, hi):
            cid = det_chain[j]
            if cid < 0 or chains[cid].kind == "amb" or d.nocue[j]:  # merged / occluded boxes carry HOLD
                if 0 <= d.cls_obs[j] < 2:
                    seen[int(d.cls_obs[j])] += 1
                continue
            o, oc = own(cid, det_k[j])
            if mode == "live" and alarms and locked[cid] >= 0 and det_k[j] - k_off[cid] >= cw:
                a0 = ptr[cid]
                rc = CUMC[a0 + det_k[j]] - CUMC[a0 + det_k[j] - cw]  # recent class window
                kr = int(np.argmax(rc))
                srt = np.sort(rc)
                if kr != g.team[locked[cid]] and srt[-1] - np.logaddexp(srt[0], srt[1]) >= log_pt:
                    stats["class_alarms"] += 1
                    alarm(cid, j, f, "class_alarm", {"recent_class": kr})
                    o, oc = own(cid, det_k[j])
            srt = np.sort(oc)
            cls = int(np.argmax(oc))
            if cls != OFFICIAL and srt[-1] - np.logaddexp(srt[0], srt[1]) >= log_pt:
                if "team" in cues_used and d.cls_obs[j] >= 0 and d.cls_obs[j] != cls:
                    stats["colour_hold"] += 1  # this box shows another class than its chain: HOLD (swap or misread)
                    continue
                per_team[cls].append((j, cid, o))
        for team, items in per_team.items():
            if not items:
                continue
            cand = np.where(g.cand[f] & (g.team == team))[0]
            if len(cand) == 0:
                continue
            bench = np.where(~g.cand[f] & (g.team == team))[0]
            n, m = len(items), len(cand)
            S = np.zeros((n, m))
            dummy = np.zeros(n)
            unseen = max(0, m - n - seen[team])  # candidates not visible anywhere in this frame could be hiding
            eps_f = prm["leak_min"] + prm["leak_eps"] * unseen / m
            for r, (j, cid, o) in enumerate(items):
                if mode == "live":
                    lp = np.log(_restricted_prior(mix[cid], cand, eps_f))
                else:
                    lp = np.log(_restricted_prior(fwd_mix[cid], cand, eps_f)) + np.log(_restricted_prior(bwd_mix[cid], cand, eps_f))
                S[r] = lp + o[cand]
                ref = (np.logaddexp.reduce(o[bench]) - math.log(len(bench))) if len(bench) else o[cand].max()
                dummy[r] = log_dummy + ref + math.log(1.0 / m)
            D_ = max(0, n - m)
            Sx = np.hstack([S, np.repeat(dummy[:, None], D_, 1)]) if D_ else S
            marg, exact = joint_marginals(Sx, prm["max_enum"])
            if not exact:
                stats["enum_fallback_frames"] += 1
            marg = marg[:, :m]
            map_lab = None
            if not abstain:
                Sm = Sx.copy()
                for r, (j, cid, o) in enumerate(items):
                    if mode == "live" and locked[cid] >= 0 and locked[cid] in cand:
                        Sm[r] = -1e9
                        Sm[r, int(np.where(cand == locked[cid])[0][0])] = 1e9
                rr, cc = linear_sum_assignment(-Sm)
                map_lab = {int(r_): int(cand[c_]) if c_ < m else HOLD for r_, c_ in zip(rr, cc)}
            for r, (j, cid, o) in enumerate(items):
                mrow = marg[r]
                full = np.zeros(g.n)
                full[cand] = mrow
                b = int(np.argmax(mrow))
                srt = np.sort(S[r])
                margin = S[r, b] - (srt[-2] if m > 1 else -np.inf)  # chain evidence margin (no elimination)
                if mode == "offline":
                    mean_marg[cid] += full
                    MARGF[j] = full
                    SNEF[j, cand] = S[r]
                    OWNF[j, cand] = o[cand]
                    in_team[j] = True
                    continue
                last_marg[cid] = full
                L0 = locked[cid]
                if L0 >= 0:
                    if L0 not in cand:
                        locked[cid] = -1
                        stats["releases"] += 1
                        log.append({"kind": "release_substitution", "frame": f, "chain": int(cid), "from": int(L0)})
                    elif (not alarms) or full[L0] >= p_unlock:
                        label[j], post[j] = L0, full[L0]
                        continue
                    else:
                        stats["alarms"] += 1
                        alarm(cid, j, f, "alarm", {"posterior": round(float(full[L0]), 4)})
                        post[j] = mrow[b]
                        continue
                oc_ = o[cand]
                n_cue = CUMN[ptr[cid] + det_k[j]] - (CUMN[ptr[cid] + k_off[cid] - 1] if k_off[cid] > 0 else 0)
                oth_ = np.delete(oc_, b)
                own_ok = n_cue >= 1 and (len(oth_) == 0 or oc_[b] - oth_.max() >= own_min)  # own cues must favour it
                if mrow[b] >= p_lock and margin >= prm["min_evidence_nats"] and own_ok and twin_ok(cid, det_k[j], cand[b], cand):
                    locked[cid] = cand[b]
                    label[j], post[j] = cand[b], mrow[b]
                elif not abstain:
                    label[j], post[j] = map_lab.get(r, HOLD), mrow[b]
                else:
                    post[j] = mrow[b]
        if mode == "live":  # ID-INV-1 guard (reachable only through the non-exact fallback or forced MAP)
            lab = label[lo:hi]
            vals, cnt = np.unique(lab[lab >= 0], return_counts=True)
            for v in vals[cnt > 1]:
                stats["dup_guard"] += 1
                label[lo:hi][lab == v] = HOLD

    if mode == "offline":
        for c in chains:
            if mean_marg[c.cid].sum() == 0:
                continue
            L = int(np.argmax(mean_marg[c.cid]))
            js = c.dets[in_team[c.dets]]
            if len(js) == 0:
                continue
            sL = SNEF[js, L].astype(float)
            oth = SNEF[js].astype(float)
            oth[:, L] = -np.inf
            margin = sL - oth.max(1)
            pL = MARGF[js, L].astype(float)
            post[js] = pL
            ow = OWNF[js].astype(float)
            ow_oth = ow.copy()
            ow_oth[:, L] = -np.inf
            own_ok = (ow[:, L] - ow_oth.max(1) >= own_min) & (CUMN[ptr[c.cid + 1] - 1] >= 1)
            if abstain:
                cand_c = np.where(np.isfinite(SNEF[js]).any(0))[0]
                ok = np.isfinite(sL) & (pL >= p_lock) & (margin >= prm["min_evidence_nats"]) & own_ok \
                    & twin_ok(c.cid, 0, L, cand_c)
            else:
                ok = np.isfinite(sL)
            label[js[ok]] = L
        for f in range(d.n_frames):
            lo, hi = d.fstart[f], d.fstart[f + 1]
            lab = label[lo:hi]
            vals, cnt = np.unique(lab[lab >= 0], return_counts=True)
            for v in vals[cnt > 1]:
                stats["dup_guard"] += 1
                label[lo:hi][lab == v] = HOLD
    return Result(label, post, log, chains, det_chain, stats)


# --------------------------------------------------------------------------------------
# One call
# --------------------------------------------------------------------------------------
def run(d: Dets, g: Game, cfg: dict, sigma_p: float, prm=None):
    """Full pipeline -> {'live': Result, 'offline': Result, 'n_tracklets': .., ...}."""
    prm = prm or P
    mode = cfg.get("tracklets", "pure")
    cues = set(cfg.get("cues", ["team", "jersey", "appearance", "height", "gait"]))
    trks, det_trk, groups = build_tracklets(d, sigma_p, mode, prm, cues)
    chains = link_chains(trks, det_trk, d, sigma_p, mode, prm, groups)
    CL = class_evidence(d, cues, prm)
    OWN = own_evidence(d, g, cues, prm)
    J = jersey_evidence(d, g, chains, cues, prm)
    EV = OWN + J
    conf = confusable_pairs(g, cues, prm)
    live = solve(d, g, chains, EV, CL, cfg, "live", prm, J, conf)
    split_log = []
    off_chains = chains
    if cfg.get("splits", True):
        EV_raw = OWN + jersey_evidence(d, g, chains, cues, prm, cap=False)
        del OWN
        off_chains, split_log = split_chains(chains, d, EV_raw, CL, g, prm)
        del EV_raw
    off = solve(d, g, off_chains, EV, CL, cfg, "offline", prm, J, conf)
    off.log = split_log + off.log
    reasons = {}
    for t in trks:
        reasons[t.reason] = reasons.get(t.reason, 0) + 1
    return {"live": live, "offline": off, "n_tracklets": len(trks), "n_chains": len(chains), "confusable_pairs": int(conf.sum() // 2),
            "n_chains_offline": len(off_chains), "end_reasons": reasons}
