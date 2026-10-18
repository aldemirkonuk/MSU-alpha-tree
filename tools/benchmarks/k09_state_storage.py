"""K09 benchmark: where game state is stored (segments vs per-frame), on SYNTHETIC data only.

Question (docs/requirements_review/synthesis.md K09): store game state
  A) once, as validity intervals per dimension (state_segments + clock_segments, opened by typed
     state_transitions), with per-frame state as an as-of view, or
  B) as a wide per-frame table (state_frame, the 102 columns of schema/tables/state_frame.yaml,
     plus flow_state) on every frame of every pass.

What it does
  1. Simulates one game shaped like the first two pilot videos (155,000 frames at 29.97 fps,
     condensed replay, two halves) as a list of typed transitions. Nothing is read from any real
     game, video or licensed source.
  2. Builds A (transitions, long state_segments, clock_segments) and B (state_frame, reference
     built independently in numpy by forward fill), plus the per-frame tables both options share
     (frames, ball_states, detections).
  3. Measures Parquet size, query times, correction cost, pass-diff cost and checks that the A
     view equals B on every frame and every column.

Run:  python tools/benchmarks/k09_state_storage.py --out <scratch dir> [--seed 7] [--reps 5]
Needs: duckdb, pyarrow, numpy, pandas, pyyaml (only to read the state_frame column list).
Output files go to --out (default: a temporary directory), never into the repo.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

FPS_NUM, FPS_DEN = 30000, 1001          # 29.97 fps
N_FRAMES = 155_000
DS_PER_FRAME_NUM = 10 * FPS_DEN          # deciseconds elapsed after k frames = k*10010 // 30000
GAME_ID, SEASON, GAME_TYPE, VIDEO_ID = "SYN0001", "2026-27", "big_ten", "SYNV0001"
MODEL_VERSION = "bench-0.1.0"
CREATED_UTC = pd.Timestamp("2026-10-18T00:00:00Z")

# --------------------------------------------------------------------------------------------
# Dimensions stored as segments (team-neutral: home/away). Type: i=int, b=bool, f=float, s=str
DIMS = {
    "period": "i", "live_ball": "b", "score_home": "i", "score_away": "i", "last_score_event_id": "s",
    "team_fouls_home": "i", "team_fouls_away": "i",
    "to30_home": "i", "to60_home": "i", "to75_home": "i", "to30_away": "i", "to60_away": "i", "to75_away": "i",
    "challenge_home": "b", "challenge_away": "b", "stoppage_kind": "s",
    "team_in_possession": "s", "possession_id": "i", "chance_id": "i", "chance_number": "i",
    "possession_arrow": "s", "ball_control_state": "s", "ball_handler_player_id": "s",
    "ring_contact_this_try": "s", "inbound_side": "s", "lineup_home": "s", "lineup_away": "s",
    "defense_scheme_state": "s", "defense_scheme_confidence": "f", "flow_state": "s",
}
SRCS = ["OCR", "PBP", "CV", "derived"]
DQS = ["observed", "inferred", "carried"]


def ds_elapsed(k):
    """Deciseconds of clock elapsed after k frames (integer, identical in numpy and SQL)."""
    return (k * DS_PER_FRAME_NUM) // FPS_NUM


def frames_for_s(seconds: float) -> int:
    return int(round(seconds * FPS_NUM / FPS_DEN))


# --------------------------------------------------------------------------------------------
# 1. Simulate the game as typed transitions
class Sim:
    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)
        self.f = 0
        self.transitions = []  # dicts: transition_id, frame, ttype, changes{dim:(val,src,conf,dq)}, clocks{}, payload{}
        self.score_seq = 0

    def prov(self, src=None):
        r = self.rng
        return (src or SRCS[r.integers(0, 3)], round(float(r.uniform(0.7, 1.0)), 2), DQS[r.integers(0, 3)] if r.random() < 0.2 else "observed")

    def T(self, ttype, changes=None, clocks=None, payload=None, frame=None):
        fr = self.f if frame is None else frame
        ch = {k: (v, *self.prov()) for k, v in (changes or {}).items()}
        ck = {k: (*v, *self.prov("OCR")) for k, v in (clocks or {}).items()}
        self.transitions.append(dict(transition_id=len(self.transitions), frame=fr, ttype=ttype,
                                     changes=ch, clocks=ck, payload=payload or {}))

    def adv(self, seconds):
        self.f += max(1, frames_for_s(seconds))

    def run(self):
        r = self.rng
        home = [f"H{i:02d}" for i in range(1, 14)]
        away = [f"A{i:02d}" for i in range(1, 14)]
        lu = {"home": sorted(r.choice(home, 5, replace=False)), "away": sorted(r.choice(away, 5, replace=False))}
        score = {"home": 0, "away": 0}
        fouls = {"home": 0, "away": 0}
        to = {("home", 30): 3, ("home", 60): 1, ("home", 75): 0, ("away", 30): 3, ("away", 60): 1, ("away", 75): 0}
        poss_id, chance_id = 0, 0
        other = {"home": "away", "away": "home"}
        # initial state at frame 0
        init = {d: None for d in DIMS}
        init.update(period=1, live_ball=False, score_home=0, score_away=0, team_fouls_home=0, team_fouls_away=0,
                    to30_home=3, to60_home=1, to75_home=0, to30_away=3, to60_away=1, to75_away=0,
                    challenge_home=True, challenge_away=True, stoppage_kind="other_dead", team_in_possession="none",
                    possession_arrow="none", ball_control_state="dead", ring_contact_this_try="none", inbound_side="none",
                    lineup_home=",".join(lu["home"]), lineup_away=",".join(lu["away"]), flow_state="S0",
                    chance_number=None)
        self.T("T00_pregame", init, clocks={"game": (12000, False, "on"), "shot": (300, False, "off")})
        self.adv(20)
        gc = 12000
        sc = 300
        for period in (1, 2):
            if period == 2:
                fouls = {"home": 0, "away": 0}
                self.T("T21_period_start", {"period": 2, "team_fouls_home": 0, "team_fouls_away": 0, "flow_state": "S2",
                                             "stoppage_kind": "none", "inbound_side": "baseline"},
                       clocks={"game": (12000, False, "on"), "shot": (300, False, "off")})
                gc = 12000
                self.adv(3)
                off = "away"
            else:
                self.T("T01_jump_ball", {"flow_state": "S1", "stoppage_kind": "none"})
                self.adv(2)
                off = "home" if r.random() < 0.5 else "away"
                self.T("T23_arrow_set", {"possession_arrow": other[off]})
            media_marks = [9600, 7200, 4800, 2400]
            poss_id += 1
            chance_id += 1
            self.T("T02_control", {"team_in_possession": off, "possession_id": poss_id, "chance_id": chance_id,
                                   "chance_number": 1, "ball_control_state": f"{off}_ball",
                                   "ball_handler_player_id": str(r.choice(lu[off])), "live_ball": True, "flow_state": "S3",
                                   "defense_scheme_state": str(r.choice(["man", "zone_23", "press"], p=[.8, .15, .05])),
                                   "defense_scheme_confidence": round(float(r.uniform(.5, .95)), 2)},
                   clocks={"game": (gc, True, "on"), "shot": (300, True, "on")})
            sc = 300
            chance_no = 1
            while gc > 0:
                # ---- live stretch: passes, shots, rebounds until a whistle
                whistle = False
                while not whistle and gc > 0:
                    step_s = float(r.uniform(1.0, 3.5))
                    step_ds = int(step_s * 10)
                    if gc - step_ds <= 0:   # period ends on the horn
                        self.adv(gc / 10)
                        gc = 0
                        break
                    self.adv(step_s)
                    gc -= ds_elapsed(frames_for_s(step_s))
                    sc -= ds_elapsed(frames_for_s(step_s))
                    if sc <= 0:   # shot-clock violation
                        whistle = True
                        kind = "violation"
                        break
                    u = r.random()
                    if u < 0.62:
                        self.T("T15_handler_change", {"ball_handler_player_id": str(r.choice(lu[off])),
                                                      "flow_state": "S4"})
                    elif u < 0.80:  # try
                        self.T("T04_try_release", {"ball_control_state": "in_flight", "ball_handler_player_id": None,
                                                   "team_in_possession": "none", "flow_state": "S5",
                                                   "ring_contact_this_try": "unknown"})
                        self.adv(1.0)
                        gc -= 10
                        sc -= 10
                        if r.random() < 0.48:  # make
                            pts = 3 if r.random() < 0.35 else 2
                            score[off] += pts
                            self.score_seq += 1
                            # clock keeps running after a made FG except the last 59.9 s of period 2 (5-11.9)
                            stop = period == 2 and gc <= 599
                            self.T("T05_made_fg", {f"score_{off}": score[off], "last_score_event_id": f"SE{self.score_seq:04d}",
                                                   "ball_control_state": "inbound_pending", "live_ball": False,
                                                   "ring_contact_this_try": "yes", "flow_state": "S2",
                                                   "inbound_side": "baseline", "stoppage_kind": "none"},
                                   clocks={"game": (gc, not stop, "on"), "shot": (sc, False, "on")},
                                   payload={"team": off, "points": pts})
                            self.adv(3.0)
                            if not stop:
                                gc -= ds_elapsed(frames_for_s(3.0))
                            off = other[off]
                            poss_id += 1
                            chance_id += 1
                            chance_no = 1
                            sc = 300
                            self.T("T02_control", {"team_in_possession": off, "possession_id": poss_id, "chance_id": chance_id,
                                                   "chance_number": 1, "ball_control_state": f"{off}_ball", "live_ball": True,
                                                   "ball_handler_player_id": str(r.choice(lu[off])), "flow_state": "S3",
                                                   "inbound_side": "none", "ring_contact_this_try": "none",
                                                   "defense_scheme_state": str(r.choice(["man", "zone_23", "press"], p=[.8, .15, .05])),
                                                   "defense_scheme_confidence": round(float(r.uniform(.5, .95)), 2)},
                                   clocks={"game": (gc, True, "on"), "shot": (sc, True, "on")})
                        else:
                            ring = r.random() < 0.9
                            self.T("T06a_miss_loose", {"ball_control_state": "contested", "flow_state": "S6",
                                                       "ring_contact_this_try": "yes" if ring else "no"})
                            self.adv(0.8)
                            gc -= 8
                            sc -= 8
                            if r.random() < 0.72:   # defensive rebound
                                off = other[off]
                                poss_id += 1
                                chance_id += 1
                                chance_no = 1
                                sc = 300
                                self.T("T08_def_rebound", {"team_in_possession": off, "possession_id": poss_id,
                                                           "chance_id": chance_id, "chance_number": 1,
                                                           "ball_control_state": f"{off}_ball",
                                                           "ball_handler_player_id": str(r.choice(lu[off])), "flow_state": "S3",
                                                           "defense_scheme_state": str(r.choice(["man", "zone_23", "press"], p=[.8, .15, .05])),
                                                           "defense_scheme_confidence": round(float(r.uniform(.5, .95)), 2)},
                                       clocks={"shot": (sc, True, "on")})
                            else:   # offensive rebound: new chance, same possession
                                chance_id += 1
                                chance_no += 1
                                sc = 200 if ring else sc
                                self.T("T06_off_rebound", {"team_in_possession": off, "chance_id": chance_id,
                                                           "chance_number": chance_no, "ball_control_state": f"{off}_ball",
                                                           "ball_handler_player_id": str(r.choice(lu[off])), "flow_state": "S4"},
                                       clocks={"shot": (sc, True, "on")})
                    elif u < 0.84:  # live-ball turnover
                        off = other[off]
                        poss_id += 1
                        chance_id += 1
                        chance_no = 1
                        sc = 300
                        self.T("T03_steal", {"team_in_possession": off, "possession_id": poss_id, "chance_id": chance_id,
                                             "chance_number": 1, "ball_control_state": f"{off}_ball",
                                             "ball_handler_player_id": str(r.choice(lu[off])), "flow_state": "S3",
                                             "defense_scheme_state": str(r.choice(["man", "zone_23", "press"], p=[.8, .15, .05])),
                                             "defense_scheme_confidence": round(float(r.uniform(.5, .95)), 2)},
                               clocks={"shot": (sc, True, "on")})
                    elif u < 0.93:
                        whistle = True
                        kind = r.choice(["foul", "violation", "timeout"], p=[.6, .3, .1])
                if gc <= 0:
                    break
                # ---- dead ball after a whistle
                deff = other[off]
                if kind == "foul":
                    fouls[deff] += 1
                    self.T("T09_foul", {f"team_fouls_{deff}": fouls[deff], "live_ball": False, "ball_control_state": "dead",
                                        "team_in_possession": "none", "ball_handler_player_id": None,
                                        "stoppage_kind": "other_dead", "flow_state": "S7"},
                           clocks={"game": (gc, False, "on"), "shot": (sc, False, "on")},
                           payload={"foul_by": deff, "period": period})
                    self.adv(float(r.uniform(4, 9)))
                    if fouls[deff] >= 7:   # bonus / double bonus free throws (8-2.1, 8-2.2)
                        n = 2 if fouls[deff] >= 10 else (1 + (r.random() < 0.7))
                        self.T("T10_ft_pending", {"flow_state": "S8"})
                        for _ in range(n):
                            self.adv(float(r.uniform(6, 12)))
                            if r.random() < 0.72:
                                score[off] += 1
                                self.score_seq += 1
                                self.T("T12_ft_made", {f"score_{off}": score[off], "last_score_event_id": f"SE{self.score_seq:04d}"},
                                       payload={"team": off, "points": 1})
                        off = other[off]   # simplification: ball goes to the other side after the FTs
                        poss_id += 1
                        chance_id += 1
                        chance_no = 1
                        sc = 300
                    else:
                        sc = max(sc, 200)
                elif kind == "violation":
                    self.T("T13_violation", {"live_ball": False, "ball_control_state": "dead", "team_in_possession": "none",
                                             "ball_handler_player_id": None, "stoppage_kind": "other_dead", "flow_state": "S7"},
                           clocks={"game": (gc, False, "on"), "shot": (sc, False, "on")})
                    self.adv(float(r.uniform(3, 8)))
                    off = other[off]
                    poss_id += 1
                    chance_id += 1
                    chance_no = 1
                    sc = 300
                else:
                    k = (off, 30) if to[(off, 30)] > 0 else (off, 60)
                    to[k] = max(0, to[k] - 1)
                    self.T("T19_timeout", {f"to{k[1]}_{k[0]}": to[k], "live_ball": False, "ball_control_state": "dead",
                                           "team_in_possession": "none", "ball_handler_player_id": None,
                                           "stoppage_kind": "team_timeout", "flow_state": "S9"},
                           clocks={"game": (gc, False, "on"), "shot": (sc, False, "on")})
                    self.adv(float(r.uniform(10, 25)))   # condensed replay keeps a short huddle shot
                # media timeout at the first dead ball at or after a mark (5-14.10.c)
                if media_marks and gc <= media_marks[0]:
                    while media_marks and gc <= media_marks[0]:
                        media_marks.pop(0)
                    self.T("T20_media_timeout", {"stoppage_kind": "media_timeout", "flow_state": "S9"})
                    self.adv(float(r.uniform(8, 20)))
                # substitutions only at dead balls (3-6)
                for team, roster in (("home", home), ("away", away)):
                    if r.random() < 0.35:
                        out_p = r.choice(lu[team])
                        bench = [p for p in roster if p not in lu[team]]
                        lu[team] = sorted([p for p in lu[team] if p != out_p] + [str(r.choice(bench))])
                        self.T("T22_substitution", {f"lineup_{team}": ",".join(lu[team])})
                # rare held ball: arrow flips
                if r.random() < 0.02:
                    self.T("T14_held_ball_arrow", {"possession_arrow": off})
                # throw-in, then the ball becomes live on the inbound touch
                self.T("T11_throw_in_pending", {"ball_control_state": "inbound_pending", "flow_state": "S2",
                                                "inbound_side": str(r.choice(["sideline", "baseline"])), "stoppage_kind": "none"})
                self.adv(float(r.uniform(1.5, 4)))
                self.T("T02_control", {"team_in_possession": off, "possession_id": poss_id, "chance_id": chance_id,
                                       "chance_number": chance_no, "ball_control_state": f"{off}_ball", "live_ball": True,
                                       "ball_handler_player_id": str(r.choice(lu[off])), "flow_state": "S3", "inbound_side": "none",
                                       "ring_contact_this_try": "none",
                                       "defense_scheme_state": str(r.choice(["man", "zone_23", "press"], p=[.8, .15, .05])),
                                       "defense_scheme_confidence": round(float(r.uniform(.5, .95)), 2)},
                       clocks={"game": (gc, True, "on"), "shot": (sc, True, "on")})
            # end of period
            self.T("T24_period_end", {"live_ball": False, "ball_control_state": "dead", "team_in_possession": "none",
                                      "ball_handler_player_id": None, "flow_state": "S11", "stoppage_kind": "intermission"},
                   clocks={"game": (0, False, "on"), "shot": (0, False, "off")})
            self.adv(180 if period == 1 else 30)   # condensed halftime ~3 min
            if period == 1:
                self.T("T00_intermission", {"flow_state": "S0"})
                self.adv(5)
        return self


# --------------------------------------------------------------------------------------------
# 2. Build Option A tables (segments) and the shared per-frame tables
def scale_to_n(transitions, n_frames):
    """Rescale frame stamps so the game fills exactly n_frames (keeps order, strictly increasing)."""
    last = max(t["frame"] for t in transitions) + 1
    ratio = (n_frames - 1) / last
    prev = -1
    for t in transitions:
        f = int(t["frame"] * ratio)
        t["frame"] = max(f, prev)  # several transitions may share a frame
        prev = t["frame"]
    return transitions


def build_segments(transitions, n_frames, pass_name):
    """Fold transitions into per-dimension validity intervals [from_frame, to_frame)."""
    open_ = {}
    rows = []
    copen = {}
    crows = []
    for t in transitions:
        f = t["frame"]
        for d, (v, src, conf, dq) in t["changes"].items():
            cur = open_.get(d)
            if cur is not None and cur["value"] == v and cur["from_frame"] == f:
                continue
            if cur is not None:
                if cur["value"] == v:
                    continue   # no change of value: segment continues
                if cur["from_frame"] == f:     # replaced in the same frame: drop the empty one
                    rows.remove(cur)
                else:
                    cur["to_frame"] = f
            seg = dict(game_id=GAME_ID, pass_=pass_name, dimension=d, value=None if v is None else str(v),
                       from_frame=f, to_frame=n_frames, src=src, conf=conf, dq=dq, opened_by=t["transition_id"])
            rows.append(seg)
            open_[d] = seg
        for c, (anchor, running, status, src, conf, dq) in t["clocks"].items():
            cur = copen.get(c)
            if cur is not None:
                if cur["from_frame"] == f:
                    crows.remove(cur)
                else:
                    cur["to_frame"] = f
            seg = dict(game_id=GAME_ID, pass_=pass_name, clock=c, from_frame=f, to_frame=n_frames,
                       anchor_ds=int(anchor), running=bool(running), status=status, src=src, conf=conf, dq=dq,
                       opened_by=t["transition_id"])
            crows.append(seg)
            copen[c] = seg
    seg = pd.DataFrame(rows).rename(columns={"pass_": "pass"})
    clk = pd.DataFrame(crows).rename(columns={"pass_": "pass"})
    return seg, clk


def build_transitions_table(transitions, pass_name):
    rows = []
    for t in transitions:
        rows.append(dict(game_id=GAME_ID, pass_=pass_name, transition_id=t["transition_id"], frame_index=t["frame"],
                         video_ts_ms=int(round(t["frame"] * 1000 * FPS_DEN / FPS_NUM)), ttype=t["ttype"],
                         changes=json.dumps({k: v[0] for k, v in t["changes"].items()}),
                         payload=json.dumps(t["payload"]), supersedes_id=None))
    return pd.DataFrame(rows).rename(columns={"pass_": "pass"})


def build_per_frame_tables(n, rng, poss_ff, period_ff):
    """frames (broadcast state) and ball_states (ball per frame): exist in both options."""
    fi = np.arange(n, dtype=np.int64)
    # camera shot type as runs (cuts every 2-15 s)
    cam = np.empty(n, dtype=object)
    i = 0
    kinds = ["main_wide", "close_up", "replay", "bench", "crowd", "graphic"]
    p = [.78, .1, .06, .03, .02, .01]
    while i < n:
        L = int(rng.integers(60, 450))
        cam[i:i + L] = kinds[rng.choice(6, p=p)]
        i += L
    frames = pd.DataFrame({
        "video_id": VIDEO_ID, "frame_index": fi,
        "video_ts_ms": np.round(fi * 1000 * FPS_DEN / FPS_NUM).astype(np.int64),
        "camera_shot_type": cam,
        "reverse_angle": rng.random(n) < 0.01,
        "replay_flag": cam == "replay",
        "court_visible_frac": np.round(rng.uniform(0.3, 1.0, n), 3),
        "court_mapping_conf": np.round(rng.uniform(0.5, 1.0, n), 3),
        "scorebug_visible": cam != "replay",
        "coverage_score": np.round(rng.uniform(0, 1, n), 3),
        "broadcast_src": "CV", "broadcast_conf": np.round(rng.uniform(0.6, 1.0, n), 2), "broadcast_dq": "observed",
    })
    bx = np.clip(np.cumsum(rng.normal(0, 0.08, n)), -8.6, 8.6)
    by = np.clip(np.abs(np.cumsum(rng.normal(0, 0.1, n))) % 28, -2.6, 28.0)
    bz = np.round(np.abs(rng.normal(1.2, 0.6, n)), 2)
    vis = rng.random(n) < 0.9
    home_north = np.where(period_ff == 1, "north", "south")
    away_north = np.where(period_ff == 1, "south", "north")
    attacked = np.where(poss_ff == "home", home_north, np.where(poss_ff == "away", away_north, "north"))
    ball = pd.DataFrame({
        "video_id": VIDEO_ID, "frame_index": fi,
        "ball_x_m": np.round(bx, 2), "ball_y_m": np.round(by, 2), "ball_z_m": bz,
        "ball_r_m": np.round(np.hypot(bx, by), 2), "ball_theta_deg": np.round(np.degrees(np.arctan2(by, bx)) % 360, 1),
        "ball_visible": vis, "ball_inferred": ~vis, "try_in_flight": rng.random(n) < 0.03,
        "basket_attacked": attacked,
        "ball_src": "CV", "ball_conf": np.round(rng.uniform(0.5, 1.0, n), 2), "ball_dq": np.where(vis, "observed", "inferred"),
    })
    return frames, ball


def build_detections(frames, rng):
    n = len(frames)
    k = np.clip(rng.poisson(11, n), 6, 14)
    fi = np.repeat(frames["frame_index"].to_numpy(), k)
    m = len(fi)
    det_id = np.concatenate([np.arange(c) for c in k])
    return pd.DataFrame({"video_id": VIDEO_ID, "frame_index": fi, "det_id": det_id.astype(np.int16),
                         "cls": rng.choice(np.array(["player", "official", "ball"]), m, p=[.86, .1, .04]),
                         "x_px": rng.uniform(0, 1920, m).astype(np.float32), "y_px": rng.uniform(0, 1080, m).astype(np.float32),
                         "w_px": rng.uniform(20, 120, m).astype(np.float32), "h_px": rng.uniform(60, 300, m).astype(np.float32),
                         "conf": rng.uniform(0.3, 1.0, m).astype(np.float32)})


# --------------------------------------------------------------------------------------------
# 3. Option B reference: forward fill in numpy (independent of the SQL view)
def ffill(seg_d, n, dtype=object):
    """Value per frame from a dimension's segments (searchsorted on from_frame)."""
    starts = seg_d["from_frame"].to_numpy()
    idx = np.searchsorted(starts, np.arange(n), side="right") - 1
    out = {}
    for col in [c for c in seg_d.columns if c not in ("from_frame", "to_frame")]:
        vals = seg_d[col].astype(object).where(seg_d[col].notna(), None).to_numpy(dtype=object)
        arr = np.empty(n, dtype=object)
        ok = idx >= 0
        arr[ok] = vals[idx[ok]]
        arr[~ok] = None
        out[col] = arr
    return out


def bonus_np(f):
    f = np.asarray(f, dtype=np.int64)
    return np.where(f >= 10, "double_bonus", np.where(f >= 7, "bonus", "none")).astype(object)


def build_state_frame_reference(seg, clk, frames, ball, n, pass_name, column_order):
    fi = np.arange(n, dtype=np.int64)
    S = {}
    for d in DIMS:
        sd = seg[seg.dimension == d].sort_values("from_frame")[["from_frame", "to_frame", "value", "src", "conf", "dq"]]
        S[d] = ffill(sd, n)

    def typed(d):
        v = S[d]["value"]
        t = DIMS[d]
        if t == "i":
            return pd.array([None if x is None else int(x) for x in v], dtype="Int64")
        if t == "b":
            return pd.array([None if x is None else x == "True" for x in v], dtype="boolean")
        if t == "f":
            return pd.array([None if x is None else float(x) for x in v], dtype="Float64")
        return v

    C = {}
    for c in ("game", "shot"):
        cd = clk[clk.clock == c].sort_values("from_frame")[["from_frame", "to_frame", "anchor_ds", "running", "status", "src", "conf", "dq"]]
        starts = cd["from_frame"].to_numpy()
        idx = np.searchsorted(starts, fi, side="right") - 1
        a = cd["anchor_ds"].to_numpy()[idx]
        run = cd["running"].to_numpy()[idx]
        k = fi - starts[idx]
        val = np.where(run, np.maximum(0, a - (k * DS_PER_FRAME_NUM) // FPS_NUM), a)
        C[c] = dict(ds=val, running=run, status=cd["status"].to_numpy()[idx], src=cd["src"].to_numpy()[idx],
                    conf=cd["conf"].to_numpy()[idx], dq=cd["dq"].to_numpy()[idx])
    team_map = {"home": "msu", "away": "opponent", "none": "none", None: None}
    tip = np.array([team_map[x] for x in S["team_in_possession"]["value"]], dtype=object)
    arrow = np.array([team_map[x] for x in S["possession_arrow"]["value"]], dtype=object)
    sh, sa = typed("score_home"), typed("score_away")
    fh, fa = typed("team_fouls_home"), typed("team_fouls_away")
    msu_b, opp_b = bonus_np(fa), bonus_np(fh)
    bonus = np.where(tip == "msu", msu_b, np.where(tip == "opponent", opp_b, "none")).astype(object)
    sc_on = C["shot"]["status"] == "on"
    lh = S["lineup_home"]["value"]
    la = S["lineup_away"]["value"]
    players = [a.split(",") + b.split(",") for a, b in zip(lh, la)]
    confs = np.vstack([S["period"]["conf"], C["game"]["conf"], S["score_home"]["conf"], S["team_fouls_home"]["conf"],
                       S["to30_home"]["conf"], S["team_in_possession"]["conf"], S["lineup_home"]["conf"]]).astype(float)
    out = {
        "game_id": GAME_ID, "season": SEASON, "game_type": GAME_TYPE, "video_id": VIDEO_ID, "frame_index": fi,
        "video_ts_ms": frames["video_ts_ms"].to_numpy(), "pass": pass_name,
        "period": typed("period"), "game_clock_s": C["game"]["ds"] / 10.0, "clock_running": C["game"]["running"].astype(bool),
        "clock_inferred": ~frames["scorebug_visible"].to_numpy(), "shot_clock_status": C["shot"]["status"],
        "shot_clock_s": pd.array(np.where(sc_on, C["shot"]["ds"] / 10.0, np.nan), dtype="Float64"),
        "live_ball": typed("live_ball"),
        "period_src": S["period"]["src"], "period_conf": S["period"]["conf"].astype(float), "period_dq": S["period"]["dq"],
        "game_clock_src": C["game"]["src"], "game_clock_conf": C["game"]["conf"].astype(float), "game_clock_dq": C["game"]["dq"],
        "shot_clock_src": C["shot"]["src"], "shot_clock_conf": C["shot"]["conf"].astype(float), "shot_clock_dq": C["shot"]["dq"],
        "live_ball_src": S["live_ball"]["src"], "live_ball_conf": S["live_ball"]["conf"].astype(float), "live_ball_dq": S["live_ball"]["dq"],
        "score_msu": sh, "score_opp": sa, "margin": sh - sa, "last_score_event_id": S["last_score_event_id"]["value"],
        "score_src": S["score_home"]["src"], "score_conf": S["score_home"]["conf"].astype(float), "score_dq": S["score_home"]["dq"],
        "team_fouls_msu": fh, "team_fouls_opp": fa, "bonus_state": bonus, "msu_bonus_state": msu_b, "opp_bonus_state": opp_b,
        "fouls_src": S["team_fouls_home"]["src"], "fouls_conf": S["team_fouls_home"]["conf"].astype(float), "fouls_dq": S["team_fouls_home"]["dq"],
        "timeouts_msu": typed("to30_home") + typed("to60_home") + typed("to75_home"),
        "timeouts_opp": typed("to30_away") + typed("to60_away") + typed("to75_away"),
        "to30_left_msu": typed("to30_home"), "to60_left_msu": typed("to60_home"), "to75_left_msu": typed("to75_home"),
        "to30_left_opp": typed("to30_away"), "to60_left_opp": typed("to60_away"), "to75_left_opp": typed("to75_away"),
        "challenge_available_msu": typed("challenge_home"), "challenge_available_opp": typed("challenge_away"),
        "stoppage_kind": S["stoppage_kind"]["value"],
        "timeouts_src": S["to30_home"]["src"], "timeouts_conf": S["to30_home"]["conf"].astype(float), "timeouts_dq": S["to30_home"]["dq"],
        "team_in_possession": tip, "possession_id": typed("possession_id"), "chance_id": typed("chance_id"),
        "chance_number": typed("chance_number"), "possession_arrow": arrow,
        "possession_src": S["team_in_possession"]["src"], "possession_conf": S["team_in_possession"]["conf"].astype(float),
        "possession_dq": S["team_in_possession"]["dq"],
        "ball_control_state": np.array([None if x is None else x.replace("home_ball", "msu_ball").replace("away_ball", "opponent_ball")
                                        for x in S["ball_control_state"]["value"]], dtype=object),
        "ball_handler_player_id": S["ball_handler_player_id"]["value"],
        "ring_contact_this_try": S["ring_contact_this_try"]["value"], "inbound_side": S["inbound_side"]["value"],
        "players_on_floor": players,
        "players_src": S["lineup_home"]["src"], "players_conf": S["lineup_home"]["conf"].astype(float), "players_dq": S["lineup_home"]["dq"],
        "defense_scheme_state": S["defense_scheme_state"]["value"], "defense_scheme_confidence": typed("defense_scheme_confidence"),
        "invariant_breaks": [[] for _ in range(n)], "flag_ids": [[] for _ in range(n)], "correction_ids": [[] for _ in range(n)],
        "model_version": MODEL_VERSION, "source": "fused", "confidence": confs.min(axis=0),
        "created_utc": CREATED_UTC, "flow_state": S["flow_state"]["value"],
    }
    for c in frames.columns:
        if c not in ("video_id", "frame_index", "video_ts_ms"):
            out[c] = frames[c].to_numpy()
    for c in ball.columns:
        if c not in ("video_id", "frame_index"):
            out[c] = ball[c].to_numpy()
    df = pd.DataFrame(out)
    missing = [c for c in column_order if c not in df.columns]
    assert not missing, f"reference lacks columns {missing}"
    return df[column_order + ["flow_state"]]


# --------------------------------------------------------------------------------------------
# 4. SQL: compound runs (wide segments) and the per-frame as-of view (Option A view)
SQL_CAST = {"i": "BIGINT", "b": "BOOLEAN", "f": "DOUBLE", "s": "VARCHAR"}


def sql_runs(pass_name):
    """One row per change point of any dimension: the full wide state, typed (a few thousand rows)."""
    joins, cols = [], []
    for j, (d, t) in enumerate(DIMS.items()):
        a = f"d{j}"
        joins.append(f"ASOF LEFT JOIN (SELECT from_frame, value, src, conf, dq FROM seg WHERE pass = '{pass_name}' AND dimension = '{d}') {a} ON b.f >= {a}.from_frame")
        cols.append(f"CAST({a}.value AS {SQL_CAST[t]}) AS {d}")
        cols += [f"{a}.src AS {d}__src", f"{a}.conf AS {d}__conf", f"{a}.dq AS {d}__dq"]
    for c in ("game", "shot"):
        a = f"c_{c}"
        joins.append(f"ASOF LEFT JOIN (SELECT from_frame AS {c}_from, anchor_ds AS {c}_anchor, running AS {c}_running, status AS {c}_status, src AS {c}__src, conf AS {c}__conf, dq AS {c}__dq FROM clk WHERE pass = '{pass_name}' AND clock = '{c}') {a} ON b.f >= {a}.{c}_from")
        cols += [f"{a}.{c}_from", f"{a}.{c}_anchor", f"{a}.{c}_running", f"{a}.{c}_status", f"{a}.{c}__src", f"{a}.{c}__conf", f"{a}.{c}__dq"]
    return f"""
    WITH b AS (SELECT DISTINCT from_frame AS f FROM seg WHERE pass = '{pass_name}'
               UNION SELECT DISTINCT from_frame FROM clk WHERE pass = '{pass_name}')
    SELECT b.f AS from_frame, LEAD(b.f, 1, {N_FRAMES}) OVER (ORDER BY b.f) AS to_frame, {", ".join(cols)}
    FROM b {" ".join(joins)} ORDER BY b.f"""


def bonus_sql(x):
    return f"CASE WHEN {x} >= 10 THEN 'double_bonus' WHEN {x} >= 7 THEN 'bonus' ELSE 'none' END"


def tm(x):
    return f"CASE {x} WHEN 'home' THEN 'msu' WHEN 'away' THEN 'opponent' ELSE {x} END"


def sql_view(runs_table, pass_name, column_order, frame_filter=""):
    gc = f"CASE WHEN r.game_running THEN greatest(0, r.game_anchor - ((f.frame_index - r.game_from) * {DS_PER_FRAME_NUM}) // {FPS_NUM}) ELSE r.game_anchor END"
    sc = f"CASE WHEN r.shot_running THEN greatest(0, r.shot_anchor - ((f.frame_index - r.shot_from) * {DS_PER_FRAME_NUM}) // {FPS_NUM}) ELSE r.shot_anchor END"
    expr = {
        "game_id": f"'{GAME_ID}'", "season": f"'{SEASON}'", "game_type": f"'{GAME_TYPE}'", "video_id": "f.video_id",
        "frame_index": "f.frame_index", "video_ts_ms": "f.video_ts_ms", "pass": f"'{pass_name}'",
        "period": "r.period", "game_clock_s": f"({gc}) / 10.0", "clock_running": "r.game_running",
        "clock_inferred": "NOT f.scorebug_visible", "shot_clock_status": "r.shot_status",
        "shot_clock_s": f"CASE WHEN r.shot_status = 'on' THEN ({sc}) / 10.0 END", "live_ball": "r.live_ball",
        "period_src": "r.period__src", "period_conf": "r.period__conf", "period_dq": "r.period__dq",
        "game_clock_src": "r.game__src", "game_clock_conf": "r.game__conf", "game_clock_dq": "r.game__dq",
        "shot_clock_src": "r.shot__src", "shot_clock_conf": "r.shot__conf", "shot_clock_dq": "r.shot__dq",
        "live_ball_src": "r.live_ball__src", "live_ball_conf": "r.live_ball__conf", "live_ball_dq": "r.live_ball__dq",
        "score_msu": "r.score_home", "score_opp": "r.score_away", "margin": "r.score_home - r.score_away",
        "last_score_event_id": "r.last_score_event_id",
        "score_src": "r.score_home__src", "score_conf": "r.score_home__conf", "score_dq": "r.score_home__dq",
        "team_fouls_msu": "r.team_fouls_home", "team_fouls_opp": "r.team_fouls_away",
        "bonus_state": f"CASE r.team_in_possession WHEN 'home' THEN {bonus_sql('r.team_fouls_away')} WHEN 'away' THEN {bonus_sql('r.team_fouls_home')} ELSE 'none' END",
        "msu_bonus_state": bonus_sql("r.team_fouls_away"), "opp_bonus_state": bonus_sql("r.team_fouls_home"),
        "fouls_src": "r.team_fouls_home__src", "fouls_conf": "r.team_fouls_home__conf", "fouls_dq": "r.team_fouls_home__dq",
        "timeouts_msu": "r.to30_home + r.to60_home + r.to75_home", "timeouts_opp": "r.to30_away + r.to60_away + r.to75_away",
        "to30_left_msu": "r.to30_home", "to60_left_msu": "r.to60_home", "to75_left_msu": "r.to75_home",
        "to30_left_opp": "r.to30_away", "to60_left_opp": "r.to60_away", "to75_left_opp": "r.to75_away",
        "challenge_available_msu": "r.challenge_home", "challenge_available_opp": "r.challenge_away",
        "stoppage_kind": "r.stoppage_kind",
        "timeouts_src": "r.to30_home__src", "timeouts_conf": "r.to30_home__conf", "timeouts_dq": "r.to30_home__dq",
        "team_in_possession": tm("r.team_in_possession"), "possession_id": "r.possession_id", "chance_id": "r.chance_id",
        "chance_number": "r.chance_number", "possession_arrow": tm("r.possession_arrow"),
        "possession_src": "r.team_in_possession__src", "possession_conf": "r.team_in_possession__conf",
        "possession_dq": "r.team_in_possession__dq",
        "ball_control_state": "replace(replace(r.ball_control_state, 'home_ball', 'msu_ball'), 'away_ball', 'opponent_ball')",
        "ball_handler_player_id": "r.ball_handler_player_id", "ring_contact_this_try": "r.ring_contact_this_try",
        "inbound_side": "r.inbound_side",
        "players_on_floor": "list_concat(string_split(r.lineup_home, ','), string_split(r.lineup_away, ','))",
        "players_src": "r.lineup_home__src", "players_conf": "r.lineup_home__conf", "players_dq": "r.lineup_home__dq",
        "defense_scheme_state": "r.defense_scheme_state", "defense_scheme_confidence": "r.defense_scheme_confidence",
        "invariant_breaks": "[]::VARCHAR[]", "flag_ids": "[]::VARCHAR[]", "correction_ids": "[]::VARCHAR[]",
        "model_version": f"'{MODEL_VERSION}'", "source": "'fused'",
        "confidence": "least(r.period__conf, r.game__conf, r.score_home__conf, r.team_fouls_home__conf, r.to30_home__conf, r.team_in_possession__conf, r.lineup_home__conf)",
        "created_utc": f"TIMESTAMPTZ '{CREATED_UTC.isoformat()}'", "flow_state": "r.flow_state",
    }
    frame_cols = ["camera_shot_type", "reverse_angle", "replay_flag", "court_visible_frac", "court_mapping_conf",
                  "scorebug_visible", "coverage_score", "broadcast_src", "broadcast_conf", "broadcast_dq"]
    ball_cols = ["ball_x_m", "ball_y_m", "ball_z_m", "ball_r_m", "ball_theta_deg", "ball_visible", "ball_inferred",
                 "try_in_flight", "basket_attacked", "ball_src", "ball_conf", "ball_dq"]
    for c in frame_cols:
        expr[c] = f"f.{c}"
    for c in ball_cols:
        expr[c] = f"bs.{c}"
    sel = ", ".join(f"{expr[c]} AS \"{c}\"" for c in column_order + ["flow_state"])
    return f"""SELECT {sel} FROM frames f
        JOIN ball_states bs ON bs.frame_index = f.frame_index
        ASOF JOIN {runs_table} r ON f.frame_index >= r.from_frame
        {frame_filter} ORDER BY f.frame_index"""


# --------------------------------------------------------------------------------------------
def timeit(fn, reps):
    ts = []
    out = None
    for _ in range(reps):
        t0 = time.perf_counter()
        out = fn()
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts), out


def write_parquet(df, path, compression="zstd"):
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), path, compression=compression)
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--reps", type=int, default=5)
    args = ap.parse_args()
    out = Path(args.out or tempfile.mkdtemp(prefix="k09_"))
    out.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[2]
    import yaml
    column_order = [c["name"] for c in yaml.safe_load(open(repo / "schema/tables/state_frame.yaml"))["columns"]]
    R = {"n_frames": N_FRAMES, "fps": "30000/1001", "seed": args.seed, "reps": args.reps, "state_frame_columns": len(column_order)}

    # ---- simulate
    t0 = time.perf_counter()
    sim = Sim(args.seed).run()
    trans = scale_to_n(sim.transitions, N_FRAMES)
    seg, clk = build_segments(trans, N_FRAMES, "anchored")
    ttab = build_transitions_table(trans, "anchored")
    rng = np.random.default_rng(args.seed + 1)
    poss_ff = ffill(seg[seg.dimension == "team_in_possession"].sort_values("from_frame")[["from_frame", "to_frame", "value"]], N_FRAMES)["value"]
    period_ff = ffill(seg[seg.dimension == "period"].sort_values("from_frame")[["from_frame", "to_frame", "value"]], N_FRAMES)["value"].astype(int)
    frames, ball = build_per_frame_tables(N_FRAMES, rng, poss_ff, period_ff)
    dets = build_detections(frames, rng)
    R["simulate_s"] = round(time.perf_counter() - t0, 2)
    R["transitions"] = len(ttab)
    R["segments"] = len(seg)
    R["clock_segments"] = len(clk)
    R["segments_per_dimension"] = seg.groupby("dimension").size().sort_values(ascending=False).to_dict()
    R["transition_types"] = ttab.groupby("ttype").size().to_dict()
    R["detections"] = len(dets)

    # ---- Option B reference (numpy forward fill)
    t0 = time.perf_counter()
    B = build_state_frame_reference(seg, clk, frames, ball, N_FRAMES, "anchored", column_order)
    R["B_build_numpy_s"] = round(time.perf_counter() - t0, 2)
    R["B_columns_written"] = B.shape[1]

    # ---- storage
    sizes = {}
    sizes["B_state_frame_zstd"] = write_parquet(B, out / "B_state_frame.parquet")
    sizes["B_state_frame_snappy"] = write_parquet(B, out / "B_state_frame_snappy.parquet", "snappy")
    per_frame_cols = [c for c in frames.columns if c not in ("video_id", "frame_index", "video_ts_ms")] + \
                     [c for c in ball.columns if c not in ("video_id", "frame_index")]
    sizes["B_state_frame_without_per_frame_CV_columns_zstd"] = write_parquet(
        B.drop(columns=per_frame_cols), out / "B_state_only.parquet")
    sizes["A_state_segments"] = write_parquet(seg, out / "A_state_segments.parquet")
    sizes["A_clock_segments"] = write_parquet(clk, out / "A_clock_segments.parquet")
    sizes["A_state_transitions"] = write_parquet(ttab, out / "A_state_transitions.parquet")
    sizes["shared_frames"] = write_parquet(frames, out / "frames.parquet")
    sizes["shared_ball_states"] = write_parquet(ball, out / "ball_states.parquet")
    sizes["shared_detections"] = write_parquet(dets, out / "detections.parquet")
    R["bytes"] = sizes
    R["B_in_memory_bytes_pandas"] = int(B.memory_usage(deep=True).sum())

    con = duckdb.connect()
    con.execute(f"CREATE TABLE seg AS SELECT * FROM '{out / 'A_state_segments.parquet'}'")
    con.execute(f"CREATE TABLE clk AS SELECT * FROM '{out / 'A_clock_segments.parquet'}'")
    con.execute(f"CREATE TABLE frames AS SELECT * FROM '{out / 'frames.parquet'}'")
    con.execute(f"CREATE TABLE ball_states AS SELECT * FROM '{out / 'ball_states.parquet'}'")
    con.execute(f"CREATE TABLE det AS SELECT * FROM '{out / 'detections.parquet'}'")
    con.execute(f"CREATE TABLE B AS SELECT * FROM '{out / 'B_state_frame.parquet'}'")

    # ---- runs (wide segments) and full view materialisation
    def make_runs():
        con.execute("CREATE OR REPLACE TABLE runs AS " + sql_runs("anchored"))
        return con.execute("SELECT count(*) FROM runs").fetchone()[0]
    R["A_runs_build_s"], R["A_runs_rows"] = timeit(make_runs, args.reps)
    sizes["A_runs_materialised"] = 0
    con.execute(f"COPY runs TO '{out / 'A_runs.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    sizes["A_runs_materialised"] = os.path.getsize(out / "A_runs.parquet")

    view_sql = sql_view("runs", "anchored", column_order)

    def materialise():
        con.execute(f"COPY ({view_sql}) TO '{out / 'A_view_materialised.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    R["A_view_materialise_to_parquet_s"], _ = timeit(materialise, args.reps)
    sizes["A_view_materialised_zstd"] = os.path.getsize(out / "A_view_materialised.parquet")

    def write_B():
        con.execute(f"COPY B TO '{out / 'B_rewrite.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    R["B_full_rewrite_parquet_s"], _ = timeit(write_B, args.reps)

    # ---- correctness: view == reference on every frame and column (both directions)
    con.execute(f"CREATE OR REPLACE TABLE V AS {view_sql}")
    cols = ", ".join(f'"{c}"' for c in column_order + ["flow_state"])
    d1 = con.execute(f"SELECT count(*) FROM (SELECT {cols} FROM V EXCEPT ALL SELECT {cols} FROM B)").fetchone()[0]
    d2 = con.execute(f"SELECT count(*) FROM (SELECT {cols} FROM B EXCEPT ALL SELECT {cols} FROM V)").fetchone()[0]
    R["correctness_view_vs_B_rows_differing"] = [d1, d2]
    if d1 or d2:
        bad = []
        for c in column_order + ["flow_state"]:
            k = con.execute(f'SELECT count(*) FROM V JOIN B USING (frame_index) WHERE V."{c}" IS DISTINCT FROM B."{c}"').fetchone()[0]
            if k:
                bad.append((c, k))
        R["correctness_columns_differing"] = bad

    # ---- Q1: state at an arbitrary frame (200 random frames, one query each)
    qf = rng.integers(0, N_FRAMES, 200).tolist()

    def q1_B():
        for f in qf:
            con.execute("SELECT * FROM B WHERE frame_index = ?", [f]).fetchall()

    def q1_A_view():
        sql = sql_view("runs", "anchored", column_order, "WHERE f.frame_index = $f")
        for f in qf:
            con.execute(sql.replace("$f", str(f))).fetchall()

    def q1_A_seg():
        for f in qf:
            con.execute("SELECT dimension, value FROM seg WHERE from_frame <= ? AND ? < to_frame", [f, f]).fetchall()
            con.execute("SELECT clock, CASE WHEN running THEN greatest(0, anchor_ds - ((? - from_frame) * 10010) // 30000) ELSE anchor_ds END FROM clk WHERE from_frame <= ? AND ? < to_frame", [f, f, f]).fetchall()
    for name, fn in (("Q1_point_B_ms", q1_B), ("Q1_point_A_view_ms", q1_A_view), ("Q1_point_A_segments_ms", q1_A_seg)):
        s, _ = timeit(fn, args.reps)
        R[name] = round(s / len(qf) * 1000, 3)

    # ---- Q2: all frames where the offense is in the bonus and shot clock < 5 s
    def q2_B():
        return con.execute("SELECT count(*), min(frame_index), max(frame_index) FROM B WHERE bonus_state <> 'none' AND shot_clock_status = 'on' AND shot_clock_s < 5").fetchone()

    def q2_B_parquet():
        return con.execute(f"SELECT count(*), min(frame_index), max(frame_index) FROM '{out / 'B_state_frame.parquet'}' WHERE bonus_state <> 'none' AND shot_clock_status = 'on' AND shot_clock_s < 5").fetchone()

    def q2_A_view():
        return con.execute(f"SELECT count(*), min(frame_index), max(frame_index) FROM ({view_sql}) WHERE bonus_state <> 'none' AND shot_clock_status = 'on' AND shot_clock_s < 5").fetchone()

    def q2_A_interval():
        # interval-native: per run, the first frame with shot clock < 5.0 s is solved in closed form
        sql = f"""
        WITH r AS (
          SELECT from_frame, to_frame, shot_from, shot_anchor, shot_running,
                 CASE team_in_possession WHEN 'home' THEN team_fouls_away WHEN 'away' THEN team_fouls_home ELSE -1 END AS def_fouls
          FROM runs WHERE shot_status = 'on'),
        q AS (
          SELECT from_frame, to_frame,
                 CASE WHEN NOT shot_running THEN CASE WHEN shot_anchor < 50 THEN from_frame ELSE to_frame END
                      ELSE greatest(from_frame, shot_from + CAST(ceil(greatest(0, shot_anchor - 49) * {FPS_NUM} / {DS_PER_FRAME_NUM}.0) AS BIGINT)) END AS lo
          FROM r WHERE def_fouls >= 7)
        SELECT sum(greatest(0, to_frame - lo)), min(CASE WHEN to_frame > lo THEN lo END), max(CASE WHEN to_frame > lo THEN to_frame - 1 END) FROM q"""
        return con.execute(sql).fetchone()
    q2 = {}
    for name, fn in (("Q2_filter_B_table_ms", q2_B), ("Q2_filter_B_parquet_ms", q2_B_parquet),
                     ("Q2_filter_A_view_ms", q2_A_view), ("Q2_filter_A_interval_ms", q2_A_interval)):
        s, res = timeit(fn, args.reps)
        R[name] = round(s * 1000, 2)
        q2[name] = [int(x) if x is not None else None for x in res]
    R["Q2_results_count_min_max"] = q2

    # ---- Q3: per-frame join with detections
    def q3_B():
        return con.execute("""SELECT s.ball_control_state, count(*), round(avg(d.conf), 6) FROM det d JOIN B s USING (frame_index)
                              WHERE s.margin BETWEEN -5 AND 5 AND s.shot_clock_s < 10 GROUP BY 1 ORDER BY 1""").fetchall()

    def q3_A():
        gc_sc = f"CASE WHEN r.shot_running THEN greatest(0, r.shot_anchor - ((d.frame_index - r.shot_from) * {DS_PER_FRAME_NUM}) // {FPS_NUM}) ELSE r.shot_anchor END"
        return con.execute(f"""SELECT replace(replace(r.ball_control_state, 'home_ball', 'msu_ball'), 'away_ball', 'opponent_ball') AS bcs,
                                      count(*), round(avg(d.conf), 6)
                               FROM det d ASOF JOIN runs r ON d.frame_index >= r.from_frame
                               WHERE r.score_home - r.score_away BETWEEN -5 AND 5 AND r.shot_status = 'on' AND ({gc_sc}) < 100
                               GROUP BY 1 ORDER BY 1""").fetchall()
    s, rb = timeit(q3_B, args.reps)
    R["Q3_join_detections_B_ms"] = round(s * 1000, 2)
    s, ra = timeit(q3_A, args.reps)
    R["Q3_join_detections_A_asof_ms"] = round(s * 1000, 2)
    R["Q3_results_equal"] = rb == ra

    # ---- Q4: correction: one foul re-attributed at minute 12 of the first half (game clock <= 8:00)
    tt = ttab.copy()
    fouls = [t for t in trans if t["ttype"] == "T09_foul" and t["payload"].get("period") == 1]
    target = next(t for t in fouls if t["clocks"]["game"][0] <= 4800)
    old_team = target["payload"]["foul_by"]
    new_team = "home" if old_team == "away" else "away"
    p1_end = next(t["frame"] for t in trans if t["ttype"] == "T21_period_start")
    cf = target["frame"]
    R["Q4_correction"] = {"transition_id": target["transition_id"], "frame": cf, "game_clock_ds": target["clocks"]["game"][0],
                          "from_team": old_team, "to_team": new_team}

    def correct_A():
        # 1) append the correction and a superseding transition (append-only)
        corr = pd.DataFrame([dict(correction_id="C0001", game_id=GAME_ID, target="state_transitions",
                                  target_id=target["transition_id"], field="foul_by", raw_value=old_team,
                                  corrected_value=new_team, reason="benchmark", reviewer="bench")])
        # 2) rebuild only the team-foul segments of period 1 from the corrected foul list
        p1_fouls = []
        for t in fouls:
            team = new_team if t is target else t["payload"]["foul_by"]
            p1_fouls.append((t["frame"], team))
        rows = []
        cnt = {"home": 0, "away": 0}
        prev = seg[(seg.dimension.isin(["team_fouls_home", "team_fouls_away"])) & (seg.from_frame < p1_end)]
        keep = seg.drop(prev.index)
        open_rows = {}
        for d in ("team_fouls_home", "team_fouls_away"):
            first = prev[prev.dimension == d].sort_values("from_frame").iloc[0]
            open_rows[d] = dict(first)
            rows.append(open_rows[d])
        for f, team in p1_fouls:
            cnt[team] += 1
            d = f"team_fouls_{team}"
            open_rows[d]["to_frame"] = f
            src_row = prev[(prev.dimension == d) & (prev.from_frame <= f)].sort_values("from_frame").iloc[-1]
            new = dict(src_row)
            new.update(from_frame=f, to_frame=p1_end, value=str(cnt[team]), opened_by=target["transition_id"] if f == cf else new["opened_by"])
            if f >= cf:   # rebuilt segments carry the correction's provenance (reviewer-asserted value)
                new.update(src="manual", conf=1.0, dq="observed")
            rows.append(new)
            open_rows[d] = new
        new_p1 = pd.DataFrame(rows)
        seg2 = pd.concat([keep, new_p1], ignore_index=True).sort_values(["dimension", "from_frame"]).reset_index(drop=True)
        tt2 = pd.concat([tt, pd.DataFrame([dict(game_id=GAME_ID, transition_id=len(tt), frame_index=cf,
                                                 video_ts_ms=int(round(cf * 1000 * FPS_DEN / FPS_NUM)), ttype="T09_foul",
                                                 changes="{}", payload=json.dumps({"foul_by": new_team, "period": 1}),
                                                 supersedes_id=target["transition_id"], **{"pass": "anchored"})])], ignore_index=True)
        write_parquet(seg2, out / "A_state_segments_v2.parquet")
        write_parquet(tt2, out / "A_state_transitions_v2.parquet")
        write_parquet(corr, out / "A_state_corrections.parquet")
        return seg2, len(prev), len(new_p1)
    s, (seg2, n_old, n_new) = timeit(correct_A, args.reps)
    R["Q4_A_correction_s"] = round(s, 4)
    R["Q4_A_segment_rows_replaced"] = [int(n_old), int(n_new)]

    # A hybrid: also regenerate the materialised per-frame table after the correction
    con.execute(f"CREATE OR REPLACE TABLE seg AS SELECT * FROM '{out / 'A_state_segments_v2.parquet'}'")

    def regen():
        con.execute("CREATE OR REPLACE TABLE runs AS " + sql_runs("anchored"))
        con.execute(f"COPY ({view_sql}) TO '{out / 'A_view_materialised_v2.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    s, _ = timeit(regen, args.reps)
    R["Q4_A_hybrid_regenerate_per_frame_s"] = round(s, 3)

    # B: patch the frames in the window and rewrite the whole immutable Parquet file
    d_home = 1 if new_team == "home" else -1
    d_away = -d_home

    # B must also re-stamp provenance on exactly the frames whose fouls group the corrected segments cover:
    # from the first team_fouls_home boundary at or after the correction (fouls_* follows team_fouls_home).
    corrected_home = [t["frame"] for t in fouls if t["frame"] >= cf and (new_team if t is target else t["payload"]["foul_by"]) == "home"]
    h0 = min(corrected_home) if corrected_home else p1_end
    prov_patch = f"frame_index >= {h0} AND frame_index < {p1_end}"
    R["Q4_B_provenance_frames_restamped"] = int(p1_end - h0)
    # ... and when home LOSES the foul, frames [cf, h0) fall back to the provenance of the home segment
    # that was open before the correction (copied from frame cf - 1).
    pv = con.execute(f"SELECT fouls_src, fouls_conf, fouls_dq FROM B WHERE frame_index = {cf - 1}").fetchone()
    lose_patch = f"frame_index >= {cf} AND frame_index < {h0}" if old_team == "home" else "FALSE"
    R["Q4_B_provenance_frames_restored"] = int(h0 - cf) if old_team == "home" else 0

    def correct_B():
        con.execute(f"""COPY (
            SELECT * REPLACE (
              CASE WHEN frame_index >= {cf} AND frame_index < {p1_end} THEN team_fouls_msu + ({d_home}) ELSE team_fouls_msu END AS team_fouls_msu,
              CASE WHEN frame_index >= {cf} AND frame_index < {p1_end} THEN team_fouls_opp + ({d_away}) ELSE team_fouls_opp END AS team_fouls_opp,
              CASE WHEN frame_index >= {cf} AND frame_index < {p1_end} THEN {bonus_sql(f'team_fouls_opp + ({d_away})')} ELSE msu_bonus_state END AS msu_bonus_state,
              CASE WHEN frame_index >= {cf} AND frame_index < {p1_end} THEN {bonus_sql(f'team_fouls_msu + ({d_home})')} ELSE opp_bonus_state END AS opp_bonus_state,
              CASE WHEN frame_index >= {cf} AND frame_index < {p1_end} THEN
                   CASE team_in_possession WHEN 'msu' THEN {bonus_sql(f'team_fouls_opp + ({d_away})')}
                                           WHEN 'opponent' THEN {bonus_sql(f'team_fouls_msu + ({d_home})')} ELSE 'none' END
                   ELSE bonus_state END AS bonus_state,
              CASE WHEN {prov_patch} THEN 'manual' WHEN {lose_patch} THEN '{pv[0]}' ELSE fouls_src END AS fouls_src,
              CASE WHEN {prov_patch} THEN 1.0 WHEN {lose_patch} THEN {pv[1]} ELSE fouls_conf END AS fouls_conf,
              CASE WHEN {prov_patch} THEN 'observed' WHEN {lose_patch} THEN '{pv[2]}' ELSE fouls_dq END AS fouls_dq,
              CASE WHEN {prov_patch} THEN least(period_conf, game_clock_conf, score_conf, 1.0, timeouts_conf, possession_conf, players_conf)
                   WHEN {lose_patch} THEN least(period_conf, game_clock_conf, score_conf, {pv[1]}, timeouts_conf, possession_conf, players_conf)
                   ELSE confidence END AS confidence)
            FROM B) TO '{out / 'B_state_frame_v2.parquet'}' (FORMAT parquet, COMPRESSION zstd)""")
    s, _ = timeit(correct_B, args.reps)
    R["Q4_B_correction_rewrite_s"] = round(s, 3)
    R["Q4_B_frames_touched"] = int(p1_end - cf)
    R["Q4_B_cells_touched"] = int((p1_end - cf) * 5)

    # B in a mutable store (DuckDB table UPDATE) for comparison
    con.execute("CREATE OR REPLACE TABLE B2 AS SELECT * FROM B")

    def correct_B_update():
        con.execute(f"""UPDATE B2 SET team_fouls_msu = team_fouls_msu + ({d_home}), team_fouls_opp = team_fouls_opp + ({d_away})
                        WHERE frame_index >= {cf} AND frame_index < {p1_end}""")
        con.execute(f"""UPDATE B2 SET team_fouls_msu = team_fouls_msu - ({d_home}), team_fouls_opp = team_fouls_opp - ({d_away})
                        WHERE frame_index >= {cf} AND frame_index < {p1_end}""")
    s, _ = timeit(correct_B_update, args.reps)
    R["Q4_B_update_in_place_s_(two UPDATEs)"] = round(s, 4)

    # correctness after the correction: regenerated view == patched B
    con.execute(f"CREATE OR REPLACE TABLE V2 AS SELECT * FROM '{out / 'A_view_materialised_v2.parquet'}'")
    con.execute(f"CREATE OR REPLACE TABLE BV2 AS SELECT * FROM '{out / 'B_state_frame_v2.parquet'}'")
    e1 = con.execute(f"SELECT count(*) FROM (SELECT {cols} FROM V2 EXCEPT ALL SELECT {cols} FROM BV2)").fetchone()[0]
    e2 = con.execute(f"SELECT count(*) FROM (SELECT {cols} FROM BV2 EXCEPT ALL SELECT {cols} FROM V2)").fetchone()[0]
    changed = con.execute(f"SELECT count(*) FROM V2 JOIN V USING (frame_index) WHERE V2.team_fouls_msu IS DISTINCT FROM V.team_fouls_msu").fetchone()[0]
    R["Q4_correctness_after_rows_differing"] = [e1, e2]
    R["Q4_frames_whose_team_fouls_changed"] = changed

    # ---- Q5: blind vs anchored pass diff (ball_control_state boundaries jittered by up to +/-6 frames)
    con.execute(f"CREATE OR REPLACE TABLE seg AS SELECT * FROM '{out / 'A_state_segments.parquet'}'")
    con.execute("CREATE OR REPLACE TABLE runs AS " + sql_runs("anchored"))
    sb = seg[seg.dimension == "ball_control_state"].sort_values("from_frame").reset_index(drop=True).copy()
    jit = rng.integers(-6, 7, len(sb))
    jit[0] = 0
    nf = (sb["from_frame"].to_numpy() + jit)
    nf = np.maximum.accumulate(np.maximum(nf, 0))
    sb["from_frame"] = nf
    sb["to_frame"] = np.append(nf[1:], N_FRAMES)
    sb = sb[sb.to_frame > sb.from_frame]
    sb["pass"] = "blind"
    con.register("sb_df", sb)
    con.execute("CREATE OR REPLACE TABLE seg_blind AS SELECT * FROM sb_df")

    def diff_segments():
        return con.execute("""SELECT sum(least(a.to_frame, b.to_frame) - greatest(a.from_frame, b.from_frame))
            FROM seg a JOIN seg_blind b ON a.dimension = b.dimension AND a.from_frame < b.to_frame AND b.from_frame < a.to_frame
            WHERE a.dimension = 'ball_control_state' AND a.value IS DISTINCT FROM b.value""").fetchone()[0]

    def diff_frames():
        return con.execute("""SELECT count(*) FROM frames f
            ASOF JOIN (SELECT from_frame, value FROM seg WHERE dimension = 'ball_control_state') a ON f.frame_index >= a.from_frame
            ASOF JOIN (SELECT from_frame, value FROM seg_blind) b ON f.frame_index >= b.from_frame
            WHERE a.value IS DISTINCT FROM b.value""").fetchone()[0]
    s, r1 = timeit(diff_segments, args.reps)
    R["Q5_pass_diff_segments_ms"] = round(s * 1000, 2)
    s, r2 = timeit(diff_frames, args.reps)
    R["Q5_pass_diff_per_frame_ms"] = round(s * 1000, 2)
    R["Q5_frames_differing_segments_vs_frames"] = [int(r1), int(r2)]

    # ---- Q6: whole-pass B rebuild from transitions (what a pipeline rerun costs without segments)
    t0 = time.perf_counter()
    build_state_frame_reference(seg, clk, frames, ball, N_FRAMES, "anchored", column_order)
    R["Q6_B_rebuild_reference_numpy_s"] = round(time.perf_counter() - t0, 2)

    (out / "k09_results.json").write_text(json.dumps(R, indent=2, default=str))
    print(json.dumps(R, indent=2, default=str))


if __name__ == "__main__":
    main()
