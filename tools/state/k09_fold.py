"""K09 stored truth from play-by-play: type CBBD rows into state transitions, fold them into
state segments, and check both against config/state_machine.yaml and the rulebook invariants.

pbp_only pass (no video). Keys are (period, game_clock_ds, order_index). Nothing here reads the
network; inputs are files already pulled into private storage. Outputs that contain licensed rows
go to private storage only; the repo gets counts.

Library functions are pure (tested in tests/state/); `main()` runs the two pilot games.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SM_PATH = REPO / "config" / "state_machine.yaml"
INV_PATH = REPO / "config" / "invariants.yaml"

FG_TYPES = {"JumpShot", "LayUpShot", "DunkShot", "TipShot", "HookShot"}
LIVE = {"S3", "S4", "S4a", "S4b", "S4c", "S5", "S6"}
PBP_DIMS = None  # filled by load_machine


def load_machine(path: Path = SM_PATH) -> dict:
    sm = yaml.safe_load(path.read_text())
    global PBP_DIMS
    PBP_DIMS = {d for d, spec in sm["dimensions"].items()
                if spec.get("stored") == "segment" and "pbp" in spec.get("sources", [])}
    return sm


def load_constants(path: Path = INV_PATH) -> dict:
    return yaml.safe_load(path.read_text())["constants"]


def other(side: str) -> str:
    return {"home": "away", "away": "home"}.get(side, "none")


def tid(*parts) -> str:
    return "tr-" + hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16]


class LogCounter(Counter):
    """Counter that also records where each break happened (row index of the play being typed)."""

    def __init__(self, owner=None):
        super().__init__()
        self.owner, self.where = owner, defaultdict(list)

    def __setitem__(self, k, v):
        if self.owner is not None:
            self.where[k].append(getattr(self.owner, "cur", None))
        super().__setitem__(k, v)


@dataclass
class Transition:
    ttype: str
    subtype: str | None
    period: int
    gc_ds: int
    team: str
    changes: dict
    flow_from: str
    flow_to: str
    source_event_id: str | None
    inferred: bool = False
    player_ids: list = field(default_factory=list)
    order_index: int = 0
    transition_id: str = ""
    snapshot: dict = field(default_factory=dict)   # full state after the transition (reference for the view test)


@dataclass
class FoldResult:
    transitions: list
    segments: list
    breaks: Counter
    notes: Counter
    checks: dict


# ----------------------------------------------------------------------------------------------
# Typing
# ----------------------------------------------------------------------------------------------

def side_of(row) -> str:
    v = row.get("isHomeTeam")
    return "home" if v is True else "away" if v is False else "none"


def lineups(row, home_name: str) -> tuple[str, str]:
    h, a = [], []
    for p in row.get("onFloor") or []:
        (h if p["team"] == home_name else a).append(str(p["id"]))
    return "|".join(sorted(h)), "|".join(sorted(a))


def ft_k_of_n(text: str):
    m = re.search(r"(\d) of (\d)", text or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def is_missed_try(p) -> bool:
    return (p["playType"] in FG_TYPES and not p["scoringPlay"]) or p["playType"] == "Block Shot"


def reorder(plays: list, notes: Counter) -> list:
    """ORD-03: CBBD source order inside one game-clock second is unreliable (free throws listed 2-of-2 before
    1-of-2, substitutions before the whistle that stopped play, End Game before the last rebound). Inside each
    instant, sort by the row's score total (post-event scores never decrease), then by event logic, then by the
    free-throw number, then by source order. See config/state_machine.yaml pbp_mapping.ordering_fixes."""
    out, i = [], 0
    while i < len(plays):
        j = i
        key = (plays[i]["period"], plays[i]["secondsRemaining"])
        while j < len(plays) and (plays[j]["period"], plays[j]["secondsRemaining"]) == key:
            j += 1
        grp = plays[i:j]
        prev_live = [p for p in out if p["playType"] not in ("Substitution", "OfficialTVTimeOut", "ShortTimeOut", "RegularTimeOut")]
        pending_try = bool(prev_live) and is_missed_try(prev_live[-1]) and prev_live[-1]["period"] == key[0]
        pending_team = side_of(prev_live[-1]) if pending_try else None
        if pending_try and prev_live[-1]["playType"] == "Block Shot":
            pending_team = other(side_of(prev_live[-1]))
        def score(p):
            return int(p.get("homeScore") or 0) + int(p.get("awayScore") or 0)
        ft_teams_by_score = defaultdict(set)
        missed_last = defaultdict(int)
        for p in grp:
            if p["playType"] == "MadeFreeThrow":
                ft_teams_by_score[score(p)].add(side_of(p))
                kn = ft_k_of_n(p.get("playText")) or (1, 1)
                if not p["scoringPlay"] and kn[0] == kn[1]:
                    missed_last[score(p)] += 1
        first_reb_done = False
        cls = {}
        reb_order = sorted((idx for idx, p in enumerate(grp)
                            if p["playType"] in ("Offensive Rebound", "Defensive Rebound", "Dead Ball Rebound")),
                           key=lambda idx: (score(grp[idx]), idx))
        first_reb = reb_order[0] if (pending_try and reb_order) else None
        late_reb_teams = defaultdict(set)     # score -> teams with a rebound of a missed last free throw
        max_n = max(((ft_k_of_n(p.get("playText")) or (1, 1))[1] for p in grp if p["playType"] == "MadeFreeThrow"), default=0)
        for idx, p in enumerate(grp):
            pt = p["playType"]
            if pt == "Jumpball":
                c = 0
            elif pt in FG_TYPES:
                c = 1
            elif pt == "Block Shot":
                c = 2
            elif pt in ("Offensive Rebound", "Defensive Rebound", "Dead Ball Rebound"):
                if idx == first_reb and (pt != "Offensive Rebound" or side_of(p) == pending_team):
                    # resolves the try left open by the previous instant; a putback/tip comes after it
                    c = 0.5 if (pt == "Offensive Rebound" and any(q["playType"] in FG_TYPES and side_of(q) == side_of(p) for q in grp)) else 3
                    first_reb_done = True
                elif missed_last[score(p)]:
                    c = 8
                    late_reb_teams[score(p)].add(side_of(p))
                else:
                    c = 3
            elif pt in ("Steal", "Lost Ball Turnover"):
                c = 4
            elif pt in ("PersonalFoul", "Technical Foul"):
                fts = ft_teams_by_score[score(p)]
                # a foul whose free throws are not in this score group, while the other team shoots here, belongs after them
                c = 8.5 if (fts and other(side_of(p)) not in fts and side_of(p) in fts) else 5
            elif pt == "Substitution" and max_n:
                # post-event scores place substitutions between or after the attempts; with equal scores they come
                # after a made last attempt and before a missed one (after a missed last attempt the ball is live)
                c = 7 if missed_last[score(p)] else 7.9
            elif pt in ("OfficialTVTimeOut", "ShortTimeOut", "RegularTimeOut", "Substitution") or pt.startswith("Coach's Challenge"):
                c = 6
            elif pt == "MadeFreeThrow":
                c = 7
            elif pt == "End Period":
                c = 9
            elif pt == "End Game":
                c = 10
            else:
                c = 6
            cls[idx] = c
        for idx, p in enumerate(grp):
            # a team timeout by the team that rebounded a missed last free throw comes after that rebound
            if p["playType"] in ("ShortTimeOut", "RegularTimeOut") and side_of(p) in late_reb_teams[score(p)]:
                cls[idx] = 8.2
        def sk(ip):
            idx, p = ip
            if p["playType"] == "MadeFreeThrow":
                k = (ft_k_of_n(p.get("playText")) or (1, 1))[0]
            elif p["playType"] == "Substitution" and max_n and missed_last[score(p)]:
                k = max_n - 0.5
            else:
                k = 0
            return (score(p), cls[idx], k, idx)
        srt = [p for _, p in sorted(enumerate(grp), key=sk)]
        moved = sum(1 for a, b in zip(grp, srt) if a is not b)
        if moved:
            notes["ORD-03 rows moved inside an instant"] += moved
        out.extend(srt)
        i = j
    return out


class Typer:
    """Walks the play-by-play once, keeping the full state, and emits typed transitions."""

    def __init__(self, sm: dict, const: dict, home_name: str):
        self.sm, self.const, self.home_name = sm, const, home_name
        self.T: list[Transition] = []
        self.breaks: Counter = LogCounter(self)
        self.notes: Counter = LogCounter(self)
        self.cur = None
        self.state: dict = {}
        self.flow = "none"
        self.resume = "S2"          # flow to return to after a timeout or review
        self.ap_pending = False     # restart is an alternating-possession throw-in
        self.to_left = {}           # side -> {to30, to60}
        self.pending_poss_after_trip = None

    # -- emit ---------------------------------------------------------------------------------
    def emit(self, ttype, row, changes, team="none", subtype=None, flow_to=None, inferred=False, players=()):
        spec = self.sm["transitions"][ttype]
        allowed = spec["allowed_from"]
        if allowed not in ("any",) and self.flow not in allowed and not (ttype == "T00"):
            self.breaks[f"TRN-03 {ttype} from {self.flow}"] += 1
        listed = spec["changes"]
        clean = {}
        for dim, val in changes.items():
            base = dim.split(":")[0]
            if base not in PBP_DIMS:
                continue
            if listed != "all" and base not in listed:
                self.breaks[f"TRN-02 {ttype} changes {base}"] += 1
            if self.state.get(dim) != val:
                clean[dim] = val
        if flow_to is not None and flow_to != self.flow:
            clean["flow_state"] = flow_to
        for d, v in clean.items():
            self.state[d] = v
        f_from, self.flow = self.flow, flow_to or self.flow
        t = Transition(ttype, subtype, row["period"], int(row["secondsRemaining"]) * 10, team, clean, f_from, self.flow,
                       str(row.get("id")) if row.get("id") is not None else None, inferred, list(players))
        t.snapshot = dict(self.state)
        self.T.append(t)
        return t

    # -- helpers --------------------------------------------------------------------------------
    def new_possession(self, side, ch=None):
        ch = ch if ch is not None else {}
        ch["possession_team"] = side
        ch["possession_seq"] = self.state.get("possession_seq", 0) + 1
        ch["chance_seq"] = self.state.get("chance_seq", 0) + 1
        return ch

    def resume_if_paused(self, row):
        if self.flow in ("S9", "S10"):
            target = self.resume
            self.emit("T26", row, {"stoppage": "none" if target == "S2" else self.state.get("stoppage"),
                                   "restart_pending": {"S2": "throw_in", "S8": "free_throw"}.get(target, self.state.get("restart_pending"))},
                      flow_to=target, inferred=True)
            self.notes["T26 inferred"] += 1

    def go_live(self, row):
        """Infer T15 (throw-in completed) when a live-play event follows a pending throw-in."""
        self.resume_if_paused(row)
        if self.flow in ("S2", "S7"):
            ch = {"ball_status": "live", "restart_pending": "none", "stoppage": "none",
                  "team_control": self.state.get("possession_team", "none"), "game_clock_running": "running"}
            if self.ap_pending:
                ch["arrow"] = other(self.state.get("possession_team", "none"))
                self.ap_pending = False
            if self.flow == "S7":
                self.breaks["TRN-03 T15 from S7 (no restart typed before live play)"] += 1
                self.flow = "S2"
            self.emit("T15", row, ch, team=self.state.get("possession_team", "none"), flow_to="S3", inferred=True)
            self.notes["T15 inferred"] += 1

    # -- main walk --------------------------------------------------------------------------------
    def run(self, plays: list, final_scores: tuple[int, int]):
        plays = reorder(plays, self.notes)
        tos = self.const["timeouts"]["at_least_3_media"]
        first = plays[0]
        h, a = lineups(first, self.home_name)
        self.to_left = {s: {"to30": tos["to30_per_game"], "to60": tos["to60_per_game"]} for s in ("home", "away")}
        total = tos["to30_per_game"] + tos["to60_per_game"]
        init = {"period_phase": "pregame", "period": 0, "ball_status": "dead", "team_control": "none",
                "possession_team": "none", "possession_seq": 0, "chance_seq": 0, "restart_pending": "jump_ball",
                "stoppage": "none", "game_clock_running": "stopped", "score_home": 0, "score_away": 0,
                "team_fouls_home": 0, "team_fouls_away": 0, "timeouts_left_home": total, "timeouts_left_away": total,
                "challenge_available_home": True, "challenge_available_away": True, "arrow": "none",
                "lineup_home": h, "lineup_away": a}
        self.emit("T00", {"period": 1, "secondsRemaining": first["secondsRemaining"], "id": None}, init, flow_to="S0")
        cur_period = 1
        n = len(plays)
        self.plays = plays
        groups = defaultdict(list)
        for p in plays:
            groups[(p["period"], p["secondsRemaining"])].append(p)
        self.lu = {"home": set(h.split("|")) if h else set(), "away": set(a.split("|")) if a else set()}
        for i, row in enumerate(plays):
            self.cur = i
            pt, side, text = row["playType"], side_of(row), row.get("playText") or ""
            grp = groups[(row["period"], row["secondsRemaining"])]
            same = grp[grp.index(row) + 1:]
            if row["period"] != cur_period:
                self._period_start(row, cur_period)
                cur_period = row["period"]
            if pt == "Jumpball":
                if text.startswith("Start game"):
                    self.emit("T01", row, {"period_phase": "period", "period": 1, "ball_status": "live", "restart_pending": "none",
                                           "game_clock_running": "running"}, subtype="opening_tip", flow_to="S1")
                elif "won by" in text:
                    self.emit("T02", row, {**self.new_possession(side), "team_control": side, "arrow": other(side)},
                              team=side, flow_to="S4")
                else:
                    self.notes["annotation jump_ball_result"] += 1
            elif pt in FG_TYPES:
                self._shot(row, side, same)
            elif pt == "MadeFreeThrow":
                self._free_throw(row, side, text, same)
            elif pt in ("Offensive Rebound", "Defensive Rebound") and not row.get("participants"):
                self._team_rebound(row, side, grp)
            elif pt == "Offensive Rebound":
                self.resume_if_paused(row)
                if side != self.state.get("possession_team"):
                    self.breaks["IV offensive rebound by the team without the ball"] += 1
                self.emit("T06", row, {"team_control": side, "chance_seq": self.state["chance_seq"] + 1,
                                       "game_clock_running": "running", "ball_status": "live"}, team=side, flow_to="S4")
            elif pt == "Defensive Rebound":
                self.resume_if_paused(row)
                ch = {"team_control": side, "game_clock_running": "running", "ball_status": "live"}
                if side != self.state.get("possession_team"):
                    self.new_possession(side, ch)
                else:
                    self.breaks["IV defensive rebound by the team with the ball"] += 1
                self.emit("T08", row, ch, team=side, flow_to="S3")
            elif pt == "Dead Ball Rebound":
                self._team_rebound(row, side, grp)
            elif False:
                if self.flow == "S8":
                    self.notes["annotation team_rebound_credit"] += 1
                else:
                    ch = {"ball_status": "dead", "restart_pending": "throw_in", "team_control": "none", "stoppage": "violation",
                          "game_clock_running": "stopped"}
                    if side in ("home", "away") and side != self.state.get("possession_team"):
                        self.new_possession(side, ch)
                    self.emit("T13", row, ch, team=side, subtype="out_of_bounds_after_try", flow_to="S2")
            elif pt == "Block Shot":
                self.notes["annotation block"] += 1
            elif pt == "Steal":
                self.go_live(row)
                self.emit("T03", row, {**self.new_possession(side), "team_control": side}, team=side, flow_to="S3")
            elif pt == "Lost Ball Turnover":
                stolen = any(p["playType"] == "Steal" and side_of(p) == other(side) for p in grp)
                if stolen:
                    self.notes["annotation turnover credited to a steal"] += 1
                else:
                    self.go_live(row)
                    if side != self.state.get("possession_team"):
                        self.breaks["IV turnover by the team without the ball"] += 1
                    ch = {"ball_status": "dead", "stoppage": "violation", "team_control": "none", "restart_pending": "throw_in",
                          "game_clock_running": "stopped"}
                    self.emit("T13", row, self.new_possession(other(side), ch), team=side, flow_to="S2")
            elif pt in ("PersonalFoul", "Technical Foul"):
                self._foul(row, side, grp, same)
            elif pt in ("OfficialTVTimeOut", "ShortTimeOut", "RegularTimeOut"):
                self._timeout(row, side, pt)
            elif pt.startswith("Coach's Challenge"):
                self._challenge(row, side, text, pt)
            elif pt == "Substitution":
                self._sub_row(row, side, text)
                nxt = plays[i + 1] if i + 1 < n else None
                if any(p["playType"] == "Substitution" for p in same):
                    continue    # one T22 per instant, written at its last substitution row
                if self.flow in LIVE:
                    self.breaks["TRN-03 T22 during live play (dead ball missing from PBP)"] += 1
                for s in ("home", "away"):
                    if len(self.lu[s]) != self.const["players_per_team_on_court"]:
                        self.breaks["IV lineup not 5 players after a substitution group"] += 1
                h2, a2 = "|".join(sorted(self.lu["home"])), "|".join(sorted(self.lu["away"]))
                # CBBD onFloor is the lineup at the start of an instant, so compare with the next instant's first row
                nxt = next((p for p in plays[i + 1:] if (p["period"], p["secondsRemaining"]) != (row["period"], row["secondsRemaining"])), None)
                if nxt is not None:
                    if lineups(nxt, self.home_name) != (h2, a2):
                        self.notes["lineup from substitution rows differs from the next row's onFloor"] += 1
                keep = self.flow
                self.flow = self.flow if self.flow not in LIVE else "S7"   # checked above; keep the walk going
                self.emit("T22", row, {"lineup_home": h2, "lineup_away": a2}, team=side, flow_to=self.flow)
                if keep in LIVE:
                    self.flow = keep
            elif pt == "End Period":
                self.resume_if_paused(row)
                self.emit("T20", row, {"ball_status": "dead", "stoppage": "period_end", "team_control": "none",
                                       "restart_pending": "none", "possession_team": "none", "game_clock_running": "stopped"},
                          flow_to="S11")
            elif pt == "End Game":
                self.emit("T24", row, {"period_phase": "final"}, flow_to="final")
            else:
                self.breaks[f"TRN-01 untyped playType {pt}"] += 1
            # lineup drift: at the first row of an instant, onFloor must equal the lineup built from substitution rows
            if grp[0] is row and pt != "Substitution":
                h3, a3 = lineups(row, self.home_name)
                if (h3, a3) != (self.state.get("lineup_home"), self.state.get("lineup_away")) and h3 and a3:
                    self.breaks["IV onFloor at an instant start differs from the substitution-row lineup"] += 1
        self._final_checks(final_scores)
        return self.T

    # -- event handlers ---------------------------------------------------------------------------
    def _period_start(self, row, prev_period):
        if self.flow != "S11":
            self.breaks["IV period changed without End Period"] += 1
        ch = {"period_phase": "intermission", "stoppage": "intermission"}
        if row["period"] == 2:
            ch.update(team_fouls_home=0, team_fouls_away=0)
            carry = self.const["timeouts"]["at_least_3_media"]["to30_carry_max_into_h2"]
            for s in ("home", "away"):
                self.to_left[s]["to30"] = min(self.to_left[s]["to30"], carry)
                ch[f"timeouts_left_{s}"] = self.to_left[s]["to30"] + self.to_left[s]["to60"]
        else:
            for s in ("home", "away"):
                self.to_left[s]["to30"] += 1
                ch[f"timeouts_left_{s}"] = self.to_left[s]["to30"] + self.to_left[s]["to60"]
        fake = {"period": prev_period, "secondsRemaining": 0, "id": None}
        self.emit("T21", fake, ch, flow_to="S0", inferred=True)
        start = {"period": row["period"], "secondsRemaining": 1200 if row["period"] == 2 else 300, "id": None}
        if row["period"] == 2:
            side = self.state.get("arrow", "none")
            ch = {"period_phase": "period", "period": 2, "restart_pending": "throw_in", "stoppage": "none"}
            self.new_possession(side, ch)
            self.ap_pending = True
            self.emit("T01", start, ch, team=side, subtype="second_half_ap_throw_in", flow_to="S2", inferred=True)
        else:
            self.emit("T01", start, {"period_phase": "period", "period": row["period"], "ball_status": "live",
                                     "restart_pending": "none", "game_clock_running": "running"},
                      subtype="extra_period_tip", flow_to="S1", inferred=True)

    def _sub_row(self, row, side, text):
        ids = [str(p["id"]) for p in row.get("participants") or []]
        if side not in ("home", "away") or not ids:
            self.breaks["IV substitution row without team or player"] += 1
            return
        if "subbing in" in text:
            self.lu[side].add(ids[0])
        elif "subbing out" in text:
            if ids[0] not in self.lu[side]:
                self.notes["player subbed out who was not on the floor"] += 1
            self.lu[side].discard(ids[0])
        else:
            self.breaks["IV substitution text without in/out"] += 1

    def _team_rebound(self, row, side, grp):
        """Team rebound (no player): credit only, or the ball went out of bounds after a try (T13)."""
        missed_nonlast = any(p["playType"] == "MadeFreeThrow" and not p["scoringPlay"] and side_of(p) == side
                             and (ft_k_of_n(p.get("playText")) or (1, 1))[0] < (ft_k_of_n(p.get("playText")) or (1, 1))[1]
                             for p in grp)
        if self.flow == "S8" or missed_nonlast or self.flow not in ("S5", "S6"):
            self.notes["annotation team_rebound_credit"] += 1
            return
        ch = {"ball_status": "dead", "restart_pending": "throw_in", "team_control": "none", "stoppage": "violation",
              "game_clock_running": "stopped"}
        if side in ("home", "away") and side != self.state.get("possession_team"):
            self.new_possession(side, ch)
        elif side == self.state.get("possession_team"):
            ch["chance_seq"] = self.state["chance_seq"] + 1      # ball out off the defense after a try: new chance (K08)
        self.emit("T13", row, ch, team=side, subtype="out_of_bounds_after_try", flow_to="S2")

    def _shot(self, row, side, same):
        self.go_live(row)
        if self.flow in ("S5",):
            self.notes["shot follows an unresolved try (tip-in or putback)"] += 1
            self.flow = "S4"
        if side != self.state.get("possession_team"):
            self.breaks["IV shot by the team without the ball"] += 1
        self.emit("T04", row, {"team_control": "none"}, team=side, flow_to="S5", players=[p["id"] for p in row.get("participants") or []])
        if row["scoringPlay"]:
            sh, sa = int(row["homeScore"]), int(row["awayScore"])
            delta = (sh - self.state["score_home"]) + (sa - self.state["score_away"])
            if delta not in (1, 2, 3) or delta != int(row.get("scoreValue") or delta):
                self.breaks["IV score change not 1/2/3 or not the shot value"] += 1
            ch = {"score_home": sh, "score_away": sa, "ball_status": "dead", "restart_pending": "throw_in",
                  "team_control": "none"}
            if row["period"] >= 2 and row["secondsRemaining"] * 10 <= 599:
                ch["game_clock_running"] = "stopped"
            and_one = any(p["playType"] == "MadeFreeThrow" and side_of(p) == side for p in same)
            if not and_one:
                self.new_possession(other(side), ch)
            sub = {3: "three", 2: "two"}.get(int(row.get("scoreValue") or 0), "two")
            self.emit("T05", row, ch, team=side, subtype=sub, flow_to="S2")

    def _free_throw(self, row, side, text, same):
        self.resume_if_paused(row)
        kn = ft_k_of_n(text)
        more = any(p["playType"] == "MadeFreeThrow" and side_of(p) == side for p in same)
        last = (kn[0] == kn[1]) if kn else not more
        if kn and kn[0] < kn[1] and not more:
            self.notes["free-throw trip ends early (missed front end of one-and-one or rows missing)"] += 1
            last = True
        ch = {}
        if row["scoringPlay"]:
            sh, sa = int(row["homeScore"]), int(row["awayScore"])
            if (sh - self.state["score_home"]) + (sa - self.state["score_away"]) != 1:
                self.breaks["IV free throw changed the score by other than 1"] += 1
            ch.update(score_home=sh, score_away=sa)
        if last and row["scoringPlay"]:
            ch.update(restart_pending="throw_in", ball_status="dead")
            self.new_possession(other(side), ch)
            flow_to = "S2"
        elif last:
            ch.update(restart_pending="none", ball_status="live")
            flow_to = "S6"
        else:
            flow_to = "S8"
        self.emit("T12", row, ch, team=side, subtype="made" if row["scoringPlay"] else "missed", flow_to=flow_to)

    def _foul(self, row, fouler, grp, same):
        self.resume_if_paused(row)
        fouled = other(fouler)
        pid = str((row.get("participants") or [{}])[0].get("id", "team"))
        key = f"team_fouls_{fouler}"
        ch = {key: self.state.get(key, 0) + 1, f"player_fouls:{pid}": self.state.get(f"player_fouls:{pid}", 0) + 1,
              "ball_status": "dead", "stoppage": "foul", "team_control": "none", "game_clock_running": "stopped"}
        PBP_DIMS.add("player_fouls")
        subtype = "technical_class_a" if row["playType"] == "Technical Foul" else "personal"
        self.emit("T09", row, ch, team=fouler, subtype=subtype, flow_to="S7", players=[pid])
        fts = [p for p in same if p["playType"] == "MadeFreeThrow" and side_of(p) == fouled]
        shot = [p for p in grp if p["playType"] in FG_TYPES and side_of(p) == fouled]
        if not shot and fts and max((ft_k_of_n(p.get("playText")) or (1, 1))[1] for p in fts) == 1:
            # and-one whose made basket sits one second earlier
            prev = [p for p in self.plays[max(0, self.cur - 6):self.cur]
                    if p["period"] == row["period"] and p["secondsRemaining"] - row["secondsRemaining"] <= 1
                    and p["playType"] in FG_TYPES and p["scoringPlay"] and side_of(p) == fouled]
            if prev:
                shot = prev[-1:]
                self.notes["and-one with the basket one second before the foul"] += 1
        offensive = any(p["playType"] == "Lost Ball Turnover" and side_of(p) == fouler for p in grp) or \
            (fouler == self.state.get("possession_team") and self.flow in LIVE | {"S7"})
        nf = self.state[key]
        if fts:
            nmax = max((ft_k_of_n(p.get("playText")) or (1, 1))[1] for p in fts)
            if shot:
                sub = "and_one" if shot[-1]["scoringPlay"] else ("shooting_3" if int(shot[-1].get("scoreValue") or 2) == 3 else "shooting_2")
            elif nf < self.const["bonus_team_foul"]:
                # a fouled missed try is not recorded as a field-goal attempt, so a 2- or 3-shot trip with no shot row
                # before the bonus is a shooting foul on a missed try
                if nmax in (2, 3):
                    sub = "shooting_3" if nmax == 3 else "shooting_2"
                    self.notes["shooting foul on a missed try (no shot row, as scoring rules require)"] += 1
                else:
                    sub = "technical"
                    self.breaks["IV single free throw before the bonus with no shot (technical not typed?)"] += 1
            else:
                sub = "double_bonus" if nf >= self.const["double_bonus_team_foul"] else "one_and_one"
            self.emit("T10", row, {"restart_pending": "free_throw"}, team=fouled, subtype=sub, flow_to="S8")
        else:
            ch2 = {"restart_pending": "throw_in"}
            if offensive:
                if fouler == self.state.get("possession_team"):
                    self.new_possession(fouled, ch2)
            else:
                if nf >= self.const["bonus_team_foul"] and not shot:
                    self.notes["defensive foul at or above 7 team fouls with no free throws (team-control or rows missing)"] += 1
                ch2["chance_seq"] = self.state["chance_seq"] + 1   # K08: defensive foul resets the shot clock
                self.notes["K08 new chance after a defensive foul (inferred)"] += 1
            self.emit("T11", row, ch2, team=fouled, flow_to="S2")

    def _timeout(self, row, side, pt):
        if self.flow in ("S9", "S10"):
            self.notes["timeout directly after another stoppage"] += 1
        else:
            self.resume = self.flow if self.flow in ("S2", "S7", "S8") else "S2"
        ch = {"stoppage": "timeout_media" if pt == "OfficialTVTimeOut" else "timeout_team", "game_clock_running": "stopped"}
        sub = {"OfficialTVTimeOut": "media", "ShortTimeOut": "to30", "RegularTimeOut": "to60"}[pt]
        if pt != "OfficialTVTimeOut":
            kind = "to30" if pt == "ShortTimeOut" else "to60"
            if self.to_left[side][kind] > 0:
                self.to_left[side][kind] -= 1
            else:
                other_kind = "to60" if kind == "to30" else "to30"
                self.to_left[side][other_kind] -= 1
                self.notes[f"{kind} called with none left (counted as {other_kind})"] += 1
            left = self.to_left[side]["to30"] + self.to_left[side]["to60"]
            if left < 0:
                self.breaks["IV timeouts left below 0"] += 1
            ch[f"timeouts_left_{side}"] = left
            if self.flow in LIVE:
                ch.update(ball_status="dead", team_control="none")
        if self.flow in LIVE and "ball_status" in ch:
            pass
        flow_from_ok = self.flow
        if flow_from_ok in ("S5", "S6"):
            self.breaks["TRN-03 timeout during a try or loose ball"] += 1
        self.emit("T16", row, {k: v for k, v in ch.items() if k not in ("ball_status", "team_control")}, team=side,
                  subtype=sub, flow_to="S9")

    def _challenge(self, row, side, text, pt):
        overturned = "(Overturned)" in text
        if overturned != ("Overturned" in pt):
            self.notes["challenge outcome: playType and playText disagree (text used)"] += 1
        if self.flow not in ("S9", "S10"):
            self.resume = self.flow if self.flow in ("S2", "S7", "S8") else "S2"
        ch = {"stoppage": "challenge"}
        if not overturned:
            ch[f"challenge_available_{side}"] = False
            kind = "to30" if self.to_left[side]["to30"] > 0 else "to60"
            self.to_left[side][kind] -= 1
            ch[f"timeouts_left_{side}"] = self.to_left[side]["to30"] + self.to_left[side]["to60"]
        self.emit("T17", row, ch, team=side, subtype="challenge_overturned" if overturned else "challenge_stands", flow_to="S10")

    def _final_checks(self, final_scores):
        if (self.state.get("score_home"), self.state.get("score_away")) != final_scores:
            self.breaks["IV final score differs from the games record"] += 1
        if self.flow != "final":
            self.breaks["IV game did not end in final"] += 1


# ----------------------------------------------------------------------------------------------
# Order, IDs, fold
# ----------------------------------------------------------------------------------------------

def finalise_ids(T: list, game_id: str, pass_: str = "pbp_only"):
    counter = defaultdict(int)
    for t in T:
        k = (t.period, t.gc_ds)
        t.order_index = counter[k]
        counter[k] += 1
        t.transition_id = tid(game_id, pass_, t.ttype, t.period, t.gc_ds, t.order_index, t.source_event_id)
    ids = [t.transition_id for t in T]
    assert len(ids) == len(set(ids)), "transition IDs collide"
    return T


def key(t) -> tuple:
    return (t.period, -t.gc_ds, t.order_index)


def fold(T: list) -> list:
    """Transitions -> half-open segments per (dimension, dim_key). The last segment ends at the last transition."""
    end = T[-1]
    open_: dict = {}
    segs: list = []
    for t in T:
        for dim, val in t.changes.items():
            base, _, dk = dim.partition(":")
            cur = open_.get(dim)
            if cur is not None:
                if cur["value"] == str(val):
                    continue
                cur.update(to_period=t.period, to_gc_ds=t.gc_ds, to_order=t.order_index)
            seg = {"dimension": base, "dim_key": dk, "value": str(val), "from_period": t.period, "from_gc_ds": t.gc_ds,
                   "from_order": t.order_index, "to_period": end.period, "to_gc_ds": end.gc_ds, "to_order": end.order_index,
                   "opened_by_transition_id": t.transition_id, "src": "pbp", "dq": "inferred" if t.inferred else "observed"}
            segs.append(seg)
            open_[dim] = seg
    return segs


def as_of(segs_by_dim: dict, k: tuple) -> dict:
    """State at transition key k from segments (the view): value of the segment with from <= k < to, or the one closing at k's end."""
    out = {}
    for dim, rows in segs_by_dim.items():
        val = None
        for s in rows:
            fk = (s["from_period"], -s["from_gc_ds"], s["from_order"])
            if fk <= k:
                val = s["value"]
            else:
                break
        if val is not None:
            out[dim] = val
    return out


def check_segments(segs: list, T: list) -> Counter:
    br = Counter()
    by = defaultdict(list)
    for s in segs:
        by[(s["dimension"], s["dim_key"])].append(s)
    tids = Counter(t.transition_id for t in T)
    for rows in by.values():
        rows.sort(key=lambda s: (s["from_period"], -s["from_gc_ds"], s["from_order"]))
        for a, b in zip(rows, rows[1:]):
            ak = (a["to_period"], -a["to_gc_ds"], a["to_order"])
            bk = (b["from_period"], -b["from_gc_ds"], b["from_order"])
            if ak > bk:
                br["SEG-01 overlap"] += 1
            if ak < bk:
                br["SEG-02 gap"] += 1
        for s in rows:
            if (s["from_period"], s["from_gc_ds"], s["from_order"]) == (s["to_period"], s["to_gc_ds"], s["to_order"]) and s is not rows[-1]:
                br["SEG-03 zero-length"] += 1
            if tids.get(s["opened_by_transition_id"]) != 1:
                br["SEG-04 boundary without exactly one transition"] += 1
    return br


def view_equals_reference(segs: list, T: list) -> tuple[int, int]:
    """N-MD-01 acceptance on the pbp axis: the as-of view at every transition equals the state the walk held."""
    by = defaultdict(list)
    for s in segs:
        by[s["dimension"] + (":" + s["dim_key"] if s["dim_key"] else "")].append(s)
    for rows in by.values():
        rows.sort(key=lambda s: (s["from_period"], -s["from_gc_ds"], s["from_order"]))
    diff = 0
    cells = 0
    for t in T:
        v = as_of(by, key(t))
        for dim, val in t.snapshot.items():
            if dim == "flow_state" or dim.split(":")[0] not in PBP_DIMS:
                continue
            cells += 1
            if v.get(dim) != str(val):
                diff += 1
    return diff, cells


def possession_balance(T: list) -> dict:
    out = {}
    for half in (1, 2):
        c = Counter()
        for t in T:
            if t.period == half and "possession_seq" in t.changes and t.changes.get("possession_team") in ("home", "away"):
                c[t.changes["possession_team"]] += 1
        out[half] = (c["home"], c["away"], abs(c["home"] - c["away"]))
    return out


# ----------------------------------------------------------------------------------------------
# Clock map
# ----------------------------------------------------------------------------------------------

def clock_to_s(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        if ":" in s:
            m, sec = s.split(":")
            return int(m) * 60 + float(sec)
        return float(s)
    except ValueError:      # "HALFTIME", "FINAL" and other text in the clock slot
        return None


def clock_map_from_ocr(samples: list, tol: float, min_gap: float) -> tuple[list, Counter]:
    """Classify each stretch between consecutive readable scorebug samples in the same period."""
    rows, stats = [], Counter()
    pts = []
    for r in samples:
        if r.get("game_clock_present") == "y" and r.get("period_present") == "y" and r.get("game_clock"):
            per = {"1ST": 1, "2ND": 2, "OT": 3}.get(r["period"].strip().upper(), None)
            gc = clock_to_s(r["game_clock"])
            if per and gc is not None:
                pts.append((float(r["video_time_s"]), per, gc))
    for (v0, p0, g0), (v1, p1, g1) in zip(pts, pts[1:]):
        dv, dg = v1 - v0, g0 - g1
        if p0 != p1:
            status, rate = "cut", None
            stats["period boundary"] += 1
        elif dv < min_gap:
            status, rate = "unknown", None
        elif dg < -0.05:
            status, rate = "unknown", dg / dv
            stats["clock went up (T18 correction or OCR error)"] += 1
        elif abs(dg - dv) <= tol * dv:
            status, rate = "running", dg / dv
        elif dg > dv * (1 + tol):
            status, rate = "cut", dg / dv
        elif dg <= 0.05:
            status, rate = "stopped", 0.0
        else:
            status, rate = "unknown", dg / dv     # running and stopped inside one stretch; denser anchors needed
        stats[status] += 1
        stats[f"{status} video s"] += dv
        if status in ("unknown", "stopped") and p0 == p1 and dg >= 0:
            stats["clock stopped, video s (estimated: video minus clock)"] += round(dv - dg, 1)
        if status == "cut" and p0 == p1:
            stats["game clock skipped by cuts, s"] += round(dg - dv, 1)
        rows.append({"clock": "game", "period": p0, "from_video_ms": int(v0 * 1000), "to_video_ms": int(v1 * 1000),
                     "from_gc_ds": int(round(g0 * 10)), "to_gc_ds": int(round(g1 * 10)), "anchor_ds": int(round(g0 * 10)),
                     "running": status == "running", "status": status, "rate": rate, "n_anchors": 2,
                     "err_ds": 10 if g0 >= 60 else 1, "src": "ocr", "dq": "observed"})
    stats["anchors"] = len(pts)
    stats["samples"] = len(samples)
    return rows, stats


def utc_from_wallclock(plays: list) -> tuple[list, dict]:
    """Monotone fix of CBBD wallclock (cumulative max), per PBP instant; returns clock_map rows on the game-clock axis."""
    seen, rows = {}, []
    back, max_back, run_max = 0, 0.0, None
    for p in plays:
        w = p.get("wallclock")
        if not w:
            continue
        t = datetime.fromisoformat(w.replace("Z", "+00:00"))
        if run_max is not None and t < run_max:
            back += 1
            max_back = max(max_back, (run_max - t).total_seconds())
        run_max = t if run_max is None or t > run_max else run_max
        k = (p["period"], int(p["secondsRemaining"]) * 10)
        if k not in seen:
            seen[k] = (run_max, (run_max - t).total_seconds())
    keys = sorted(seen, key=lambda k: (k[0], -k[1]))
    for a, b in zip(keys, keys[1:]):
        if a[0] != b[0]:
            continue
        ua, ea = seen[a]
        rows.append({"clock": "game", "period": a[0], "from_video_ms": -1, "to_video_ms": -1, "from_gc_ds": a[1], "to_gc_ds": b[1],
                     "anchor_ds": a[1], "running": None, "status": "unknown", "rate": None, "n_anchors": 2, "err_ds": 10,
                     "utc_at_from": ua.isoformat(), "utc_err_s": ea, "src": "pbp", "dq": "inferred" if ea else "observed"})
    return rows, {"wallclock_rows_earlier_than_a_time_already_seen": back, "max_backward_s": max_back, "instants": len(keys)}


# ----------------------------------------------------------------------------------------------
# Scorebug cross-check (OCR blind reads vs the PBP fold)
# ----------------------------------------------------------------------------------------------

FOUL_DISPLAY_CAP = 10   # both broadcasts stop the team-foul number at 10 (double bonus); measured 19 Oct


def ocr_vs_fold(samples: list, T: list, msu_side: str, window_s: float = 1.0) -> Counter:
    """Blind scorebug reads vs the play-by-play fold at the same game-clock instant.

    strict: the read equals the state after every event at that clock reading.
    window: the read equals the state at some point within +-window_s of game clock. This absorbs whole-second
    PBP clocks (CBBD gives secondsRemaining as an integer while the bug shows tenths under 60 s) and dead-ball
    instants where several events (foul, free throws) share one clock reading.
    Remaining differences are classified by the game-clock distance to the nearest change of that field.
    """
    c = Counter()
    opp = other(msu_side)
    keyed = [((t.period, -t.gc_ds, t.order_index), t.snapshot) for t in T]

    def states_between(per, lo_ds, hi_ds):
        """States held at any point with game clock in [lo_ds, hi_ds] (deciseconds remaining) of period per."""
        out, before = [], None
        for (p, ngc, _), snap in keyed:
            if (p, ngc) < (per, -hi_ds):
                before = snap
            elif p == per and -ngc >= lo_ds:
                out.append(snap)
        return ([before] if before else []) + out

    fields = {
        "score": lambda st: (st[f"score_{msu_side}"], st[f"score_{opp}"]),
        "team fouls": lambda st: (min(st[f"team_fouls_{msu_side}"], FOUL_DISPLAY_CAP), min(st[f"team_fouls_{opp}"], FOUL_DISPLAY_CAP)),
        "timeouts": lambda st: (st[f"timeouts_left_{msu_side}"], st[f"timeouts_left_{opp}"]),
    }
    cols = {"score": ("score_msu", "score_opp", "score_present"), "team fouls": ("fouls_msu", "fouls_opp", "team_fouls_present"),
            "timeouts": ("timeouts_left_msu", "timeouts_left_opp", "timeouts_present")}
    for r in samples:
        if r.get("game_clock_present") != "y":
            continue
        per = {"1ST": 1, "2ND": 2}.get((r.get("period") or "").strip().upper())
        gc = clock_to_s(r.get("game_clock"))
        if not per or gc is None:
            continue
        gds = int(round(gc * 10))
        strict = states_between(per, gds, gds)
        strict = strict[-1:] if strict else []
        wide = states_between(per, max(0, gds - int(window_s * 10)), gds + int(window_s * 10))
        for name, f in fields.items():
            a, b, present = cols[name]
            if r.get(present) != "y" or not ((r.get(a) or "").strip().isdigit() and (r.get(b) or "").strip().isdigit()):
                continue
            read = (int(r[a]), int(r[b]))
            c[f"{name}: compared"] += 1
            if strict and f(strict[0]) == read:
                c[f"{name}: agree strict"] += 1
            if any(f(s) == read for s in wide):
                c[f"{name}: agree within ±{window_s:g} s"] += 1
                continue
            # distance to the nearest change of this field in the fold
            dist = min((abs(t.gc_ds - gds) / 10 for t in T if t.period == per and any(
                k.startswith(("score_" if name == "score" else "team_fouls_" if name == "team fouls" else "timeouts_left_"))
                for k in t.changes)), default=999)
            c[f"{name}: differ, nearest change <= 3 s (scorebug lag)" if dist <= 3 else f"{name}: differ, nearest change > 3 s"] += 1
    return c


# ----------------------------------------------------------------------------------------------
# Run
# ----------------------------------------------------------------------------------------------

def run_game(game: dict, plays: list, samples: list, sm: dict, const: dict) -> dict:
    home = game["homeTeam"]
    msu_side = "home" if home == "Michigan State" else "away"
    ty = Typer(sm, const, home)
    T = ty.run(plays, (game["homePoints"], game["awayPoints"]))
    finalise_ids(T, game["sourceId"])
    segs = fold(T)
    seg_breaks = check_segments(segs, T)
    diff, cells = view_equals_reference(segs, T)
    cm_ocr, cm_stats = clock_map_from_ocr(samples, sm["constants"]["clock_rate_tolerance"], sm["constants"]["running_min_anchor_gap_s"])
    cm_pbp, utc_stats = utc_from_wallclock(plays)
    return {
        "game": game, "msu_side": msu_side, "transitions": T, "segments": segs, "clock_map_ocr": cm_ocr, "clock_map_pbp": cm_pbp,
        "summary": {
            "game_id": game["sourceId"], "home": home, "away": game["awayTeam"],
            "final": f"{game['homePoints']}-{game['awayPoints']}",
            "pbp_rows": len(plays),
            "transitions": len(T),
            "transitions_inferred": sum(t.inferred for t in T),
            "transitions_by_type": dict(sorted(Counter(t.ttype for t in T).items())),
            "segments": len(segs),
            "segments_by_dimension": dict(sorted(Counter(s["dimension"] for s in segs).items())),
            "breaks": dict(ty.breaks + seg_breaks),
            "notes": dict(ty.notes),
            "view_vs_reference": {"cells": cells, "differ": diff},
            "possessions_by_half": {str(k): {"home": v[0], "away": v[1], "diff": v[2]} for k, v in possession_balance(T).items()},
            "final_state": {k: ty.state.get(k) for k in ("score_home", "score_away", "team_fouls_home", "team_fouls_away",
                                                          "timeouts_left_home", "timeouts_left_away", "possession_seq", "chance_seq")},
            "clock_map_ocr": dict(cm_stats),
            "clock_map_pbp_utc": utc_stats,
            "ocr_vs_fold": dict(ocr_vs_fold(samples, T, msu_side)),
        },
    }


def write_private(res: dict, out_root: Path, state_version: str):
    import pyarrow as pa
    import pyarrow.parquet as pq
    gid = res["game"]["sourceId"]
    d = out_root / gid / "pbp_only" / state_version
    d.mkdir(parents=True, exist_ok=True)
    tr = [{"game_id": gid, "pass": "pbp_only", "state_version": state_version, "transition_id": t.transition_id, "ttype": t.ttype,
           "subtype": t.subtype, "period": t.period, "game_clock_ds": t.gc_ds, "order_index": t.order_index, "team": t.team,
           "flow_from": t.flow_from, "flow_to": t.flow_to, "changes": json.dumps(t.changes, sort_keys=True),
           "player_ids": json.dumps(t.player_ids), "source_event_id": t.source_event_id,
           "dq": "inferred" if t.inferred else "observed"} for t in res["transitions"]]
    sg = [{"game_id": gid, "pass": "pbp_only", "state_version": state_version, **s} for s in res["segments"]]
    cm = [{"game_id": gid, "pass": p, "state_version": state_version, **{k: (None if v is None else v) for k, v in r.items()}}
          for p, rows in (("blind", res["clock_map_ocr"]), ("pbp_only", res["clock_map_pbp"])) for r in rows]
    for name, rows in (("state_transitions", tr), ("state_segments", sg), ("clock_map", cm)):
        pq.write_table(pa.Table.from_pylist(rows), d / f"{name}.parquet")
    return d


def main():
    import csv
    priv = Path.home() / "MSU-Alpha-3-private"
    cb = priv / "data" / "licensed" / "cbbd"
    games = {g["sourceId"]: g for g in json.loads((cb / "2026-10-18" / "02_games_msu.json").read_text())}
    inputs = {
        "401856571": (cb / "2026-10-18" / "03_plays_game.json", priv / "raw_video/2025-26/_audit/uconn/scorebug_samples.csv"),
        "401856531": (cb / "2026-10-19" / "21_plays_game_louisville.json", priv / "raw_video/2025-26/_audit/louisville/scorebug_samples.csv"),
    }
    sm, const = load_machine(), load_constants()
    cfg_hash = hashlib.sha256(SM_PATH.read_bytes() + INV_PATH.read_bytes()).hexdigest()[:12]
    out = {}
    for gid, (pf, sf) in inputs.items():
        plays = json.loads(pf.read_text())
        samples = list(csv.DictReader(sf.open()))
        sv = "sv-" + hashlib.sha256(pf.read_bytes() + cfg_hash.encode()).hexdigest()[:12]
        res = run_game(games[gid], plays, samples, sm, const)
        path = write_private(res, priv / "processed", sv)
        res["summary"]["state_version"] = sv
        res["summary"]["private_output"] = str(path).replace(str(Path.home()), "~")
        out[gid] = res["summary"]
    dest = REPO / "results" / "state_machine_test"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "summary.json").write_text(json.dumps(out, indent=2, sort_keys=False))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
