"""Reference fuser of the live-state pack (baseline 4). A harness that proves the spec, not production code.

It is causal: it sees a time-ordered stream of sensor messages and keeps, for every field it handles, the live
value, its grade, its age and the time it became known. Every limit comes from config/live_state/*.yaml through
lslib (P["name"]); the two period lengths come from config/invariants.yaml.

Three parts:
  Spec        the pack as the code reads it (params, resolved records, dropout rules, max-dwell bounds).
  GradeTrack  one value under one dropout rule of any field: the grade it holds at every age, its max dwell and
  HeldValue   what happens when the sensor returns. With derive() this covers the status, roster, observation,
              derived and meta profiles (core.yaml conventions.grade_path_timing).
  Fuser       the clock and counter profiles in full: period, game clock, running flag, shot clock, score, team
              fouls, timeouts. Dead-reckoning, cues, carry, max dwell, freeze on replay and break, re-acquire,
              snap-and-log, confirm windows, authority, late corrections with versions.

Messages (dicts, `t` = video seconds, never decreasing):
  {"t", "kind": "bug", "period", "clock_s", "shot_s", <counter name>: value, ...}   any part may be missing
  {"t", "kind": "cue", "what": "stop" | "start" | "shot_reset", "value"}             audio or CV
  {"t", "kind": "cv_make", "field": "score_home", "points": 2}                       a made basket seen by CV
  {"t", "kind": "pbp", "field", "value", "period", "clock_s", "final": False}        a play-by-play row AS IT ARRIVES
  {"t", "kind": "meta", "what": "replay" | "break" | "main_camera" | "feed" | "audio", "on": bool}
  {"t", "kind": "human", "field", "value"}                                           a review answer
advance(t) moves time on with no message (frame=False tells it no frame arrived: the stream heartbeat).
"""
from __future__ import annotations

import bisect
from collections import deque

import lslib

UNKNOWN = "unknown"
SCORE_STEPS = (1, 2, 3)   # Rule 5-1: a goal counts 1, 2 or 3 points (R-IV-04)
STEPS = {"score": SCORE_STEPS, "team_fouls": (1,), "timeouts_left": (-1,), "period": (1,)}
DEFAULT_COUNTERS = ("score_home", "score_away", "team_fouls_home", "team_fouls_away",
                    "timeouts_left_home", "timeouts_left_away")


def kind_of(name):
    return next((k for k in STEPS if name.startswith(k)), "score")


class Spec:
    """The pack as the reference code reads it."""

    def __init__(self, core=None, fields=None):
        self.core = core or lslib.load_core()
        self.fields = lslib.load_fields() if fields is None else fields
        self.full = lslib.resolve(self.core, self.fields)
        self.params = lslib.params(self.core, self.fields)
        self.P = {k: v["value"] for k, v in self.params.items()}
        ladder = list(self.core["grades"]["ladder"])
        self.rank = {g: i for i, g in enumerate(ladder)}
        self.rank["quarantined"] = len(ladder)   # aside: no consumer reads it
        const = lslib._yaml(lslib.INVARIANTS)["constants"]
        self.half_s, self.extra_s = float(const["half_length_s"]), float(const["extra_period_length_s"])

    def worst(self, *grades):
        return max((g for g in grades if g), key=self.rank.__getitem__)

    def rule(self, field, when):
        """The dropout rule of a field whose `when` text equals (or starts with) the given text."""
        rules = self.full[field]["dropout"]
        hit = [d for d in rules if d["when"] == when] or [d for d in rules if d["when"].startswith(when)]
        if len(hit) != 1:
            raise KeyError(f"{field}: {len(hit)} dropout rules match {when!r}")
        return hit[0]

    def dwell(self, field, value=None):
        """Longest time (s) the rules allow this value of the field to last; None when no bound applies."""
        rec = self.full[field]
        by_value = rec.get("max_dwell_by_value") or {}
        entry = by_value.get(value) if value in by_value else (rec.get("max_dwell") if not by_value or value is None else None)
        if entry is None:
            return None
        return float(entry["value"] if isinstance(entry, dict) else self.core["max_dwell"][entry]["value"])

    def dwell_counts_in(self, field, value=None):
        """real or game_clock: the time the max-dwell bound of this value runs in (None when there is no bound)."""
        rec = self.full[field]
        by_value = rec.get("max_dwell_by_value") or {}
        entry = by_value.get(value) if value in by_value else (rec.get("max_dwell") if not by_value or value is None else None)
        if entry is None:
            return None
        return (entry if isinstance(entry, dict) else self.core["max_dwell"][entry]).get("counts_in", "real")

    def period_len(self, period):
        return self.half_s if period <= 2 else self.extra_s

    def game_time(self, period, clock_s):
        """Seconds of game time played when the clock of `period` shows clock_s."""
        base = (period - 1) * self.half_s if period <= 2 else 2 * self.half_s + (period - 3) * self.extra_s
        return base + self.period_len(period) - clock_s


# ------------------------------------------------------------------------------------------------ generic machine
class GradeTrack:
    """One held value under one dropout rule (core.yaml conventions.grade_path_timing).

    start_grade  the grade the value had when the condition began; the track never returns a better one.
    value_age_s  how long the value had already lasted when the condition began (for the max dwell).
    """

    def __init__(self, spec, field, when, value=None, start_grade="observed", value_age_s=0.0):
        self.spec, self.field, self.value = spec, field, value
        self.rule = spec.rule(field, when)
        self.starts, self.later = lslib.path_steps(self.rule["grade_path"])
        self.ages = lslib.step_ages(self.rule, spec.params)
        self.start_grade = spec.worst(start_grade, self.starts[0])
        self.value_age_s = value_age_s
        self.dwell_s = spec.dwell(field, value)
        if spec.dwell_counts_in(field, value) == "game_clock" and self.rule["rule"] == "FREEZE_ON_BREAK":
            self.dwell_s = None                                 # the clocks are stopped in a break: the bound does not elapse

    def at(self, age_s, returned=False):
        """-> {"value", "grade", "age_s", "ended"} at `age_s` seconds into the condition."""
        spec, grade = self.spec, self.start_grade
        for g, a in zip(self.later, self.ages):
            if (a == lslib.ON_RETURN and returned) or (a != lslib.ON_RETURN and (age_s > a or (a == 0 and age_s >= 0))):
                grade = spec.worst(grade, g)
        value, ended = self.value, False
        held = spec.rank[grade] >= spec.rank["carried"]            # MAX_DWELL binds values that are no longer seen
        if self.dwell_s is not None and held and self.value_age_s + age_s > self.dwell_s:
            ended = True
            nxt = self.rule.get("next_value")
            if nxt:                                                 # the rules say what follows: it is inferred
                value, grade = str(nxt).split(" (")[0].strip(), "inferred"
            else:
                value, grade = UNKNOWN, UNKNOWN
        if grade == UNKNOWN:
            value = UNKNOWN
        return {"value": value, "grade": grade, "age_s": age_s, "ended": ended}


class HeldValue:
    """A status, roster or observation value: observed, then dropped under a named rule, then seen again."""

    def __init__(self, spec, field):
        self.spec, self.field = spec, field
        self.value, self.grade, self.since, self.track, self.t_drop = UNKNOWN, UNKNOWN, None, None, None
        self.unverified = False
        self.log = []

    def observe(self, t, value, grade="observed"):
        """A sensor shows the value. After a drop this is the return: SNAP_AND_LOG or REACQUIRE of the rule."""
        if self.track is not None:
            held = self.at(t)
            if held["grade"] != UNKNOWN and held["value"] != value:
                self.log.append({"known_at": t, "log": "latency_report", "field": self.field, "kind": "snap_miss",
                                 "held": held["value"], "seen": value, "age_s": held["age_s"], "rule": self.track.rule["on_return"]})
        if value != self.value or self.since is None:
            self.since = t
        self.value, self.grade, self.track, self.t_drop, self.unverified = value, grade, None, None, False

    def drop(self, t, when):
        """The condition `when` of one of the field's dropout rules starts at t."""
        now = self.at(t)
        self.track = GradeTrack(self.spec, self.field, when, value=now["value"], start_grade=now["grade"],
                                value_age_s=t - (self.since if self.since is not None else t))
        self.t_drop, self.ended_t = t, None
        self.unverified = self.track.rule["on_return"] == "REACQUIRE"

    def back(self, t):
        """The condition ends without an observation yet (the broadcast returns from a break)."""
        self.ended_t = t

    def at(self, t):
        if self.track is None:
            return {"value": self.value, "grade": self.grade, "age_s": 0.0, "ended": False, "unverified": False}
        out = self.track.at(t - self.t_drop, returned=getattr(self, "ended_t", None) is not None)
        out["unverified"] = self.unverified
        return out


def derive(spec, inputs, valid=True):
    """Rules WORST_INPUT and VALID_IF: grade = worst input grade, age = oldest input age; withheld when not valid.
    inputs = {field: {"grade", "age_s"}}."""
    grade = spec.worst(*[s["grade"] for s in inputs.values()])
    age = max(float(s.get("age_s") or 0.0) for s in inputs.values())
    if not valid or grade in (UNKNOWN, "quarantined"):
        return {"value": UNKNOWN, "grade": UNKNOWN, "age_s": age, "published": False}
    return {"value": "computed", "grade": grade, "age_s": age, "published": True}


def win_probability_valid(spec, s):
    """valid_if of win_probability (fields_meta.yaml), on the snapshot `s` of a Fuser."""
    P, rank = spec.P, spec.rank
    for k in [n for n in s if n.startswith("score") or n == "period"]:
        g = s[k]["grade"]
        if rank[g] > rank["carried"] or (g == "carried" and s[k]["age_s"] > P["counter_stale_after_s"]):
            return False
    c = s["game_clock_s"]
    if rank[c["grade"]] <= rank["inferred"]:
        return True
    return c["hi"] is not None and c["hi"] - c["lo"] <= P["wp_clock_interval_max_s"]


# ------------------------------------------------------------------------------- derived rules that need no pixels
def bonus_state(spec, opponent_fouls, grade="observed"):
    """bonus_home / bonus_away from the opponent's team fouls of the half. A count that is carried (or worse) is a
    lower bound: one below a threshold it cannot rule out the foul that brings the bonus -> unknown."""
    P = spec.P
    if not isinstance(opponent_fouls, int):
        return UNKNOWN
    one, double = P["bonus_from_team_foul"], P["double_bonus_from_team_foul"]
    if opponent_fouls >= double:
        return "double_bonus"
    if spec.rank[grade] >= spec.rank["carried"] and opponent_fouls in (one - 1, double - 1):
        return UNKNOWN
    return "one_and_one" if opponent_fouls >= one else "none"


def foul_trouble(spec, fouls, period, clock_s):
    """K10: is a player with `fouls` personal fouls in foul trouble at this period and game clock?"""
    P = spec.P
    if period == 1:
        return fouls >= P["foul_trouble_h1_fouls"] and spec.half_s - clock_s <= P["foul_trouble_h1_elapsed_max_s"]
    if period == 2 and clock_s > P["foul_trouble_h2_split_s"]:
        return fouls >= P["foul_trouble_h2_early_fouls"]
    return fouls >= P["foul_trouble_late_fouls"]              # the last part of the second half and every extra period


def clutch_flags(spec, period, clock_lo, clock_hi, margin):
    """clutch and late_240, each yes / no / unknown, decided on the guaranteed clock interval [lo, hi] (K06).
    Never "no" when unsure: a flag is unknown unless every clock value still possible gives the same answer."""
    P = spec.P

    def flag(limit, margin_ok):
        if period in (None, UNKNOWN) or clock_lo is None or margin_ok is None:
            return UNKNOWN
        if period < 2 or clock_lo > limit or margin_ok is False:
            return "no"
        return "yes" if clock_hi <= limit else UNKNOWN
    inside = None if not isinstance(margin, int) else abs(margin) <= P["clutch_margin_max_pts"]
    return {"clutch": flag(P["clutch_clock_max_s"], inside), "late_240": flag(P["late_window_s"], True)}


def reset_make_window(spec, lag_p99_s):
    """K02 and R-SB-03: after a game the make window is the measured p99 of its lag plus the margin, kept in bounds."""
    P = spec.P
    return min(max(lag_p99_s + P["window_margin_s"], P["make_window_min_s"]), P["make_window_max_s"])


# ---------------------------------------------------------------------------------------------------------- fuser
class _Clock:
    def __init__(self):
        self.read = self.read_t = None          # last accepted reading and its time
        self.anchor = self.anchor_t = None      # where the reckoning starts (a reading, a cue, a freeze)
        self.seen_t = None                      # last reading, cue or return from a freeze: the carried limit counts from here
        self.base_t = None                      # last reading or reset cue, never moved by a freeze: the max dwell counts from here
        self.running, self.run_seen_t, self.run_grade = None, None, UNKNOWN
        self.reads = 0            # accepted readings in a row since the last gap
        self.floor = UNKNOWN      # worst grade since the last observation (a grade never moves up without one)
        self.pending = None       # an upward or too-fast step waiting for its confirming reading
        self.frozen_at = None
        self.watch_cue = False    # a reset cue re-anchored the shot clock since its last reading


class _Counter:
    def __init__(self, name):
        self.name, self.kind = name, kind_of(name)
        self.value, self.grade, self.src = None, UNKNOWN, None
        self.obs_t = self.known_at = self.bug_t = self.change_t = None
        self.agree = set()
        self.cand, self.cand_n, self.cand_t, self.cand_gap = None, 0, None, False
        self.bug_raw = None       # the last raw bug reading (never overwritten by a higher authority)
        self.windows = []         # open confirm windows: {"value", "t", "deadline", "by", "before"}
        self.recent = deque(maxlen=12)
        self.floor = UNKNOWN
        self.book_hold = None     # a scorebook value the bug contradicts: the bug may not pull the value back
        self.whistle = False      # a whistle of unknown cause since the last observation (team fouls)
        self.frozen = False       # frozen by a replay or a break and not read again yet
        self.brk_seen = False     # a break lay between the last observation and now
        self.hold_flagged = False
        self.book_G = None        # game time of the scorebook row that last set the value


class Fuser:
    def __init__(self, spec=None, counters=DEFAULT_COUNTERS, alias=None, main_camera=False, feed=False, audio=False,
                 rim_watch=None, feed_fields=None):
        """alias = {counter name: field of the pack whose rules it uses} for counters the pack does not name
        (the replay harness holds the score total, because the private reads keep the total only).
        main_camera: CV sees the play. It sets rim_watch (CV would see a made basket: the change detector of the
        score); the harness sets rim_watch apart because it has no CV."""
        self.spec = spec or Spec()
        self.t = None
        self.c, self.sc = _Clock(), _Clock()
        self.sc_ref = None                    # game-clock estimate at the shot-clock anchor
        self.period = _Counter("period")
        self.k = {n: _Counter(n) for n in counters}
        for n, f in (alias or {}).items():
            self.k[n].kind = kind_of(f)
        self.replay = self.brk = False
        self.main_camera, self.feed, self.audio = main_camera, feed, audio
        self.rim_watch = main_camera if rim_watch is None else rim_watch
        self.feed_fields = set(counters) | {"period"} if feed_fields is None else set(feed_fields)   # what the feed carries
        self.last_feed_t = self.last_frame_t = None
        self.pending_makes = []
        self.hist_G, self.hist_t = [], []     # accepted clock readings: game time -> video time
        self.version = 1
        self.log, self.transitions, self.history = [], [], {}
        self.raw_ignored = 0
        self.counts = {"returns": 0, "return_misses": 0, "rejected_reads": 0}

    # ---------------------------------------------------------------------------------------------- bookkeeping
    def _log(self, log, field, kind, **kw):
        self.log.append({"known_at": self.t, "log": log, "field": field, "kind": kind, "version": self.version, **kw})

    def _write(self, field, value, grade, event_t=None, supersedes=None, src=None):
        """A transition: the value of a field changed. as_of_known never changes for instants already past."""
        row = {"id": len(self.transitions), "field": field, "value": value, "grade": grade, "event_t": event_t,
               "known_at": self.t, "version": self.version, "supersedes": supersedes, "src": src}
        self.transitions.append(row)
        self.history.setdefault(field, []).append(row)
        return row["id"]

    def as_of_known(self, field, t):
        """What the fused state held for `field` at time t (live view; immutable)."""
        rows = [r for r in self.history.get(field, []) if r["known_at"] <= t]
        return rows[-1] if rows else None

    def as_of_event(self, field, event_t, version=None):
        """What was true at event_t as version `version` (default: the latest) tells it."""
        version = self.version if version is None else version
        rows = [r for r in self.history.get(field, []) if r["version"] <= version]
        dead = {r["supersedes"] for r in rows if r["supersedes"] is not None}
        rows = [r for r in rows if r["id"] not in dead and r["event_t"] is not None and r["event_t"] <= event_t]
        return max(rows, key=lambda r: (r["event_t"], r["id"])) if rows else None

    def _frozen(self):
        return self.replay or self.brk

    def _bug_away(self, last_t):
        """Health signal of the scorebug: away once a full scorebug_down_after_s has passed with no accepted reading."""
        return last_t is None or self.t - last_t >= self.spec.P["scorebug_down_after_s"]

    def _gap(self, last_t):
        """Seen from a new reading: was the bug away before it (more than scorebug_down_after_s since the last one)?"""
        return last_t is None or self.t - last_t > self.spec.P["scorebug_down_after_s"]

    def feed_healthy(self):
        return self.feed and self.last_feed_t is not None and self.t - self.last_feed_t <= self.spec.P["feed_stale_after_s"]

    def stream_lost(self):
        return self.last_frame_t is not None and self.t - self.last_frame_t > self.spec.P["stream_lost_after_s"]

    def level(self):
        """degradation_level: first match wins (fields_meta.yaml); a worse level applies at once."""
        if self.stream_lost():
            return "D5_no_video"
        if self.brk:
            return "D4_break"
        if self.replay:
            return "D3_replay"
        if not self.main_camera:
            return "D2_off_main"
        return "D1_bug_away" if self._bug_away(self.c.read_t) else "D0_full"

    # ----------------------------------------------------------------------------------------------- game clock
    def clock_est(self, c=None):
        """Dead-reckoned estimate (rule DEAD_RECKON): runs with the running flag, floored at 0; frozen in a freeze."""
        c = c or self.c
        if c.anchor is None:
            return None
        if c is self.sc:                                   # the shot clock runs and stops with the game clock
            now, ref = self.clock_est(self.c), self.sc_ref
            return c.anchor if now is None or ref is None else max(0.0, c.anchor - max(0.0, ref - now))
        if c.frozen_at is not None or c.running is not True:
            return c.anchor
        return max(0.0, c.anchor - (self.t - c.anchor_t))

    def _clock_grade(self):
        P, c, t, rank = self.spec.P, self.c, self.t, self.spec.rank
        if c.read is None:
            return UNKNOWN
        if not self._bug_away(c.read_t) and not self._frozen():
            g = "observed" if c.reads >= P["scorebug_up_after_reads"] else "inferred"   # SNAP_AND_LOG: one reading
        elif self._frozen():
            g = "carried"                                        # FREEZE_ON_REPLAY / FREEZE_ON_BREAK
        else:
            flag_seen = c.run_seen_t is not None and c.run_seen_t >= c.read_t - P["scorebug_down_after_s"]
            if c.running is not None and flag_seen and t - c.read_t <= P["clock_inferred_max_s"]:
                g = "inferred"                                   # DEAD_RECKON: a claim only this long after a READING
            else:                                                # the carried limit counts from the last reading or cue
                g = "carried" if t - c.seen_t <= P["clock_carried_max_s"] else UNKNOWN
            if c.running and self.clock_est() <= 0.0:
                g = UNKNOWN                                      # period end reached while hidden (MAX_DWELL)
        if rank[g] > rank[c.floor]:
            c.floor = g                                          # a grade never moves up without an observation
        return self.spec.worst(g, c.floor)

    def _clock_read(self, period, rem):
        P, c, t = self.spec.P, self.c, self.t
        tol = P["clock_tolerance_s"]
        if c.read is not None and self.period.value is not None:
            if period < self.period.value:
                self.counts["rejected_reads"] += 1
                return
            dt = t - c.read_t
            up = period == self.period.value and rem > c.read + tol
            fast = period == self.period.value and rem < c.read - dt - tol
            new_period = period > self.period.value
            if up or fast or new_period:
                kind = "period" if new_period else "up" if up else "fast"
                need = P["scorebug_up_after_reads"] if kind != "up" else P["clock_upward_confirm_reads"]
                p = c.pending
                ok = p is not None and p["kind"] == kind and p["period"] == period \
                    and p["rem"] - (t - p["t"]) - tol <= rem <= p["rem"] + tol
                n = p["n"] + 1 if ok else 1
                c.pending = {"kind": kind, "period": period, "rem": rem, "t": t, "n": n, "t0": p["t0"] if ok else t}
                if n < need:
                    self.counts["rejected_reads"] += 1        # one odd read is a misread until it persists
                    return
                if kind == "up":                              # R-IV-05: an official correction, logged, not an error
                    self._log("state_corrections", "game_clock_s", "official_clock_correction", old=self.clock_est(), new=rem)
                    self._write("game_clock_s", rem, "observed", event_t=c.pending["t0"], src="scorebug_ocr")
                elif kind == "fast":
                    self._log("latency_report", "game_clock_s", "clock_fell_faster_than_time", old=self.clock_est(), new=rem)
                else:
                    self._period_step(period, c.pending["t0"])
                    c.read = None
        c.pending = None
        away = c.read is None or self._gap(c.read_t) or c.reads == 0   # reads is 0 after a replay or a break
        if away and c.read is not None:
            est, grade = self.clock_est(), self.spec.worst(self._clock_grade(), c.floor)
            self.counts["returns"] += 1
            if abs(rem - est) > P["snap_log_tolerance_s"]:        # logged whatever the grade was
                self.counts["return_misses"] += 1
                self._log("latency_report", "game_clock_s", "snap_miss", held=round(est, 1), seen=rem,
                          miss_s=round(rem - est, 1), age_s=t - c.read_t, grade=grade)
        prev, prev_t = c.read, c.read_t
        consecutive = prev is not None and not away and t - prev_t <= P["scorebug_down_after_s"]
        c.reads = c.reads + 1 if consecutive else 1
        pair = prev is not None and t - prev_t <= P["scorebug_up_after_reads"] * P["scorebug_down_after_s"]
        if pair and c.pending is None and c.frozen_at is None and c.reads > 0:
            # the flag is read from two readings at most one missed second apart (as in measure_real.status_before)
            step = 1.0 if rem >= P["clock_tenths_below_s"] else 0.1    # one display step
            fell = prev - rem
            ran = min(t - prev_t, 1.0) / 2                             # half the time between the readings, at most 0.5 s
            running = True if fell >= max(ran, step / 2) else False if t - prev_t >= step else c.running
            if running != c.running:
                self._write("game_clock_running", "running" if running else "stopped", "observed", event_t=t, src="scorebug_ocr")
            c.running, c.run_seen_t, c.run_grade = running, t, "observed"
        elif prev is not None:
            c.running, c.run_grade = None, UNKNOWN               # after a longer gap the flag is unknown until re-read
        c.read, c.read_t, c.anchor, c.anchor_t, c.seen_t, c.base_t, c.frozen_at = rem, t, rem, t, t, t, None
        c.floor = "inferred" if c.reads < P["scorebug_up_after_reads"] else "observed"
        self.hist_G.append(self.spec.game_time(period, rem))
        self.hist_t.append(t)

    def _period_step(self, period, t0):
        k = self.period
        k.value, k.grade, k.obs_t, k.known_at, k.src, k.floor = period, "observed", self.t, self.t, "scorebug_ocr", "observed"
        self.c.running, self.c.run_grade = None, UNKNOWN         # a new period starts with the flag unread
        self._write("period", period, "observed", event_t=t0, src="scorebug_ocr")
        if period == 2:                                        # team fouls return to 0 for the second half (R-IV-09)
            for c in self.k.values():
                if c.kind == "team_fouls" and c.value is not None:
                    c.value, c.grade, c.floor, c.src, c.agree, c.cand = 0, "inferred", "inferred", "rule", set(), None
                    self._write(c.name, 0, "inferred", event_t=t0, src="rule")

    def _cue(self, what, value=None):
        """Rule CUE_RECKON. A cue observes the flag (or the reset), not the clock value: the reckoning is
        re-anchored at the cue and the carried limit counts from it. The inferred limit of the value still counts
        from the last READING (the replay harness does not support restarting it at a cue)."""
        c, sc = self.c, self.sc
        if what == "shot_reset":
            if sc.read is not None:
                sc.anchor, sc.anchor_t, sc.seen_t, sc.base_t, sc.watch_cue = float(value), self.t, self.t, self.t, True
                self.sc_ref = self.clock_est(c)
            return
        if c.read is None:
            return
        est, running = self.clock_est(), what == "start"
        for k in self.k.values():
            k.whistle = k.whistle or what == "stop"
        if running != c.running:
            self._write("game_clock_running", "running" if running else "stopped", "inferred", event_t=self.t, src="cue")
        c.anchor, c.anchor_t, c.seen_t, c.running, c.run_seen_t = est, self.t, self.t, running, self.t
        c.run_grade = "inferred"                                 # provisional by the cue; the digits confirm it

    def _running_state(self):
        P, c = self.spec.P, self.c
        if c.running is None:
            return UNKNOWN, UNKNOWN
        value = "running" if c.running else "stopped"
        if not self._bug_away(c.read_t) and not self._frozen():
            return value, c.run_grade if c.run_seen_t is not None and c.run_seen_t >= c.read_t else "carried"
        if self._frozen():
            return value, "carried"
        age = self.t - max(c.seen_t, c.run_seen_t or c.seen_t)
        if c.running and max(0.0, c.read - (self.t - c.read_t)) <= 0.0:
            return UNKNOWN, UNKNOWN                              # the clock cannot run past 0 (Rule 5-7.3)
        if age <= P["clock_inferred_max_s"]:
            return value, "inferred"
        return (value, "carried") if age <= P["clock_carried_max_s"] else (UNKNOWN, UNKNOWN)

    # ----------------------------------------------------------------------------------------------- shot clock
    def _shot_read(self, value):
        sc = self.sc
        sc.reads = 1 if sc.read is None or self._gap(sc.read_t) else sc.reads + 1
        sc.read, sc.read_t, sc.anchor, sc.anchor_t, sc.seen_t, sc.base_t = float(value), self.t, float(value), self.t, self.t, self.t
        sc.floor, sc.watch_cue, sc.frozen_at = "observed", False, None
        self.sc_ref = self.clock_est(self.c)

    def _shot_state(self):
        P, sc, t, rank = self.spec.P, self.sc, self.t, self.spec.rank
        if sc.read is None:
            return UNKNOWN, UNKNOWN
        if not self._bug_away(sc.read_t) and not self._frozen():
            return sc.read, "observed"
        age, est = t - sc.seen_t, self.clock_est(sc)
        carried = "carried" if age <= P["shot_clock_carried_max_s"] else UNKNOWN
        if t - sc.base_t > P["max_dwell.shot_clock_period"] and not self.brk:
            g = UNKNOWN                                          # MAX_DWELL: no control outlasts the shot clock (it is stopped in a break)
        elif self._frozen():
            g = "carried"
        else:   # slot unreadable while the game clock is read: FOLLOW_FIELD; whole bug away: DEAD_RECKON. One horizon,
            g = "inferred" if t - sc.read_t <= P["shot_clock_inferred_max_s"] else carried   # counted from the last READING
        if rank[g] > rank[sc.floor]:
            sc.floor = g
        g = self.spec.worst(g, sc.floor)
        return (UNKNOWN if g == UNKNOWN else est), g

    # ------------------------------------------------------------------------------------------------- counters
    def _video_time_of(self, period, clock_s):
        """Video time at which the bug clock showed this game-clock second; None if it was not read then."""
        if period is None or clock_s is None or not self.hist_G:
            return None
        G = self.spec.game_time(period, clock_s)
        i = bisect.bisect_left(self.hist_G, G - 1e-6)
        if i >= len(self.hist_G) or abs(self.hist_G[i] - G) > 2 * self.spec.P["clock_tolerance_s"]:
            return None
        return self.hist_t[i]

    def _set(self, k, value, grade, src, event_t=None, supersedes=None):
        k.recent.append((k.value, k.known_at))
        k.value, k.grade, k.floor, k.src, k.known_at = value, grade, grade, src, self.t
        k.change_t = event_t if event_t is not None else self.t
        return self._write(k.name, value, grade, event_t=event_t, supersedes=supersedes, src=src)

    def _last_id(self, k):
        rows = self.history.get(k.name) or []
        return rows[-1]["id"] if rows else None

    def _counter_read(self, k, v):
        P, t = self.spec.P, self.t
        gap = self._gap(k.bug_t) or k.frozen
        k.bug_t, k.bug_raw = t, v
        if k.kind == "team_fouls" and k.value is not None and k.value >= P["team_foul_bug_cap"] and v >= P["team_foul_bug_cap"]:
            v = k.value                                          # the bug stops counting at its cap; it cannot contradict
        open_w = [w for w in k.windows if t <= w["deadline"]]
        if v == k.value:
            k.cand, k.cand_n, k.obs_t, k.whistle, k.frozen = None, 0, t, False, False
            for w in [w for w in k.windows if w["value"] == v]:
                self._log("latency_report", k.name, "confirmed_by_bug", lag_s=t - w["t"], by=w["by"])
                k.windows.remove(w)
                k.agree.add({"cv_events": "cv", "pbp_feed": "pbp"}[w["by"]])
            sign = STEPS[k.kind][0]
            k.windows = [w for w in k.windows if (w["value"] - v) * sign > 0]   # the bug reached or passed them
            if k.book_hold is not None and (v - k.book_hold) * sign >= 0:
                k.book_hold, k.hold_flagged = None, False
            k.agree.add("bug")
            k.grade = k.floor = "confirmed" if len(k.agree) >= 2 else "observed"
            return
        if open_w and any(v == w["before"] for w in open_w):
            return                                               # the bug has not caught up yet: expected inside the window
        if k.book_hold is not None and (v - k.book_hold) * (STEPS[k.kind][0]) < 0:
            if not k.hold_flagged:                               # AUTHORITY: scorebook > bug; the raw reading stays
                self._log("scoreboard_flags", k.name, "bug_differs_from_scorebook", bug=v, scorebook=k.book_hold)
                k.hold_flagged = True
            return
        if k.cand == v:
            k.cand_n += 1
        else:
            k.cand, k.cand_n, k.cand_t, k.cand_gap = v, 1, t, gap or k.value is None
        if k.cand_n < P["scorebug_up_after_reads"]:
            return                                               # one read of a new value: animation or misread
        old, first = k.value, k.value is None
        step = None if first else v - old
        event_t = k.cand_t - (P["make_to_bug_p50_s"] if k.kind == "score" else 0.0)
        cv_open = [w for w in k.windows if w["by"] == "cv_events"]
        if cv_open:                                              # CV and the board disagree: the board wins the value live
            self._log("scoreboard_flags", k.name, "cv_make_differs_from_board", cv=old, board=v)
            self._log("cv_events_unmatched", k.name, "make_not_on_board", cv=old, board=v)
            k.windows = [w for w in k.windows if w["by"] != "cv_events"]
        elif not first and k.cand_gap:
            if k.grade != UNKNOWN:
                self._log("latency_report", k.name, "changed_while_hidden", held=old, seen=v, age_s=t - (k.obs_t or t))
            if step * STEPS[k.kind][0] < 0 or k.brk_seen:        # a fall, or any change over a break: a correction
                self._log("state_corrections", k.name, "correction_seen_on_return", old=old, new=v)
        elif not first and step not in STEPS[k.kind]:            # R-IV-04: held out for one read, then a candidate
            self._log("scoreboard_flags", k.name, "implausible_step", old=old, new=v)
            if step * STEPS[k.kind][0] < 0:
                self._log("state_corrections", k.name, "correction_candidate", old=old, new=v)
        k.agree, k.obs_t, k.cand, k.cand_n, k.whistle, k.frozen, k.brk_seen = {"bug"}, t, None, 0, False, False, False
        self._set(k, v, "observed", "scorebug_ocr", event_t=event_t)

    def _counter_state(self, k):
        """Value and grade now. Grades fall by the dropout rules of the field; they rise only in _counter_read / _pbp."""
        P, t, rank = self.spec.P, self.t, self.spec.rank
        if k.value is None:
            return UNKNOWN, UNKNOWN, None
        g, away = k.grade, self._bug_away(k.bug_t)
        if k.frozen or self._frozen():
            g = self.spec.worst(g, "carried")                    # FREEZE_ON_REPLAY / FREEZE_ON_BREAK, until re-read
        elif away and k is self.period:
            lo = None if self.c.read is None else self.c.read - (t - self.c.read_t)
            g = self.spec.worst(g, "inferred" if lo is not None and lo > 0 else "carried")   # the period cannot have ended
        elif away and k.kind == "score":
            if not self.rim_watch:                               # nothing watching the rim: carried at once
                g = self.spec.worst(g, "carried")
        elif away:                                               # team fouls, timeouts: the feed is the change detector
            if self.feed_healthy() and k.name in self.feed_fields:
                pass                                             # HOLD_UNTIL_EVENT: the feed would show a change
            elif self.audio and not k.whistle:
                g = self.spec.worst(g, "inferred")               # no whistle heard: no foul, no timeout
            else:
                g = self.spec.worst(g, "carried")
        if rank[g] > rank[k.floor]:
            k.floor = g
        g = self.spec.worst(g, k.floor)
        age = 0.0 if k.obs_t is None else t - k.obs_t
        return k.value, g, age

    def stale(self, name):
        """A carried counter older than counter_stale_after_s is marked stale (it stays carried)."""
        k = self.period if name == "period" else self.k[name]
        v, g, age = self._counter_state(k)
        return g == "carried" and age is not None and age > self.spec.P["counter_stale_after_s"]

    def _cv_make(self, m):
        k = self.k[m["field"]]
        if k.value is None:
            return
        before = k.value
        k.agree = {"cv"}
        self._set(k, before + m["points"], "inferred", "cv_events", event_t=m["t"] - self.spec.P["cv_make_confirm_s"])
        k.windows.append({"value": k.value, "t": m["t"], "deadline": m["t"] + self.spec.P["make_confirm_window_s"],
                          "by": "cv_events", "before": before})

    def _pbp(self, m):
        P, t = self.spec.P, self.t
        self.last_feed_t = t
        k = self.period if m["field"] == "period" else self.k.get(m["field"])
        if k is None:
            return
        X, src = m["value"], "pbp_final" if m.get("final") else "pbp_feed"
        event_t = self._video_time_of(m.get("period"), m.get("clock_s"))
        sign = STEPS[k.kind][0]
        G = None if m.get("period") is None or m.get("clock_s") is None else self.spec.game_time(m["period"], m["clock_s"])
        later_row = G is not None and (k.book_G is None or G > k.book_G)
        window = P["foul_to_bug_window_s"] if k.kind == "team_fouls" else P["pbp_to_bug_window_s"]
        if k.value is None:
            k.agree, k.book_G = {"pbp"}, G
            self._set(k, X, "observed", src, event_t=event_t)
        elif X == k.value:
            k.agree.add("pbp")
            k.book_G = G if later_row else k.book_G
            fresh_bug = "bug" in k.agree and not self._bug_away(k.bug_t)
            if fresh_bug or "cv" in k.agree:
                k.grade = k.floor = "confirmed"
            elif self.spec.rank[k.grade] > self.spec.rank["observed"] and not self._frozen():
                k.grade = k.floor = "observed"                   # observed from the feed alone
                k.obs_t = t
            k.windows = [w for w in k.windows if w["by"] != "cv_events"]
            self._log("latency_report", k.name, "confirmed_by_feed", lag_s=None if event_t is None else t - event_t)
        elif any(v == X for v, _ in k.recent):
            pass                                                 # an older row: the state already passed this value
        elif (X - k.value) * sign > 0:                           # news: the scorebook is ahead of the fused value
            bug_shows_other = not self._bug_away(k.bug_t) and k.bug_raw is not None and k.bug_raw != X and not self._frozen()
            closed = event_t is None or t >= event_t + window
            before = k.value
            k.book_G = G if later_row else k.book_G
            if bug_shows_other and closed:                       # AUTHORITY: scorebook > bug; a new version, a flag
                self.version += 1
                self._log("scoreboard_flags", k.name, "bug_differs_from_scorebook", bug=k.bug_raw, scorebook=X)
                k.agree, k.book_hold, k.hold_flagged = {"pbp"}, X, True
                self._set(k, X, "observed", src, event_t=event_t, supersedes=self._last_id(k))
            else:
                k.agree = {"pbp"}
                self._set(k, X, "observed", src, event_t=event_t)
                k.windows.append({"value": X, "t": t, "deadline": max(t, (event_t if event_t is not None else t) + window),
                                  "by": "pbp_feed", "before": before})
            k.obs_t = t
        elif k.src == "cv_events" and (event_t is None or event_t >= k.change_t - P["clock_tolerance_s"]):
            self.version += 1                                    # LATE_CORRECTION: the scorebook overrules a CV value
            self._log("cv_events_unmatched", k.name, "cv_value_overruled_by_scorebook", cv=k.value, scorebook=X)
            k.agree, k.windows, k.obs_t, k.book_G = {"pbp"}, [], t, G
            self._set(k, X, "observed", src, event_t=k.change_t, supersedes=self._last_id(k))   # CV keeps the instant
        elif k.src in ("pbp_feed", "pbp_final") and later_row and k.book_G is not None:
            self.version += 1                                    # LATE_CORRECTION: the scorebook corrected itself
            self._log("state_corrections", k.name, "scorebook_row_corrected", old=k.value, new=X)
            k.agree, k.windows, k.obs_t, k.book_G, k.book_hold, k.hold_flagged = {"pbp"}, [], t, G, None, False
            self._set(k, X, "observed", src, event_t=event_t, supersedes=self._last_id(k))

    # ------------------------------------------------------------------------------------------------ main loop
    def advance(self, t, frame=True):
        """Move time on to t; apply what only time does (guards, windows, heartbeats)."""
        if self.t is not None and t < self.t:
            raise ValueError("messages must be fed in time order")
        self.t = t
        if frame:
            self.last_frame_t = t
        P = self.spec.P
        for m in sorted([m for m in self.pending_makes if t >= m["t"] + P["replay_guard_s"]], key=lambda m: m["t"]):
            self.pending_makes.remove(m)
            self.t = m["t"] + P["replay_guard_s"]                # known when the guard has passed, not when we look
            self._cv_make(m)
        self.t = t
        for k in list(self.k.values()) + [self.period]:
            for w in [w for w in k.windows if t > w["deadline"]]:   # CONFIRM_WINDOW closed without its confirmation
                visible = not self._bug_away(k.bug_t) and not self._frozen()
                if w["by"] == "cv_events":                       # flag once; the value stays provisional (inferred)
                    self._log("scoreboard_flags", k.name, "make_not_confirmed_in_window", value=w["value"], bug_visible=visible)
                    w["deadline"], w["before"] = float("inf"), None   # from now a bug reading can overrule it
                elif w["value"] != k.value:
                    k.windows.remove(w)                          # the state has moved on from this value
                else:                                            # a scorebook value the bug never showed
                    if visible and k.bug_raw != w["value"] and not k.hold_flagged:
                        self._log("scoreboard_flags", k.name, "bug_differs_from_scorebook", bug=k.bug_raw, scorebook=w["value"])
                        k.hold_flagged = True
                    k.book_hold = w["value"]                     # AUTHORITY: the bug may not pull the value back
                    k.windows.remove(w)

    def feed_msg(self, m):
        """One sensor message. (Named feed_msg because `feed` is the play-by-play feed flag.)"""
        self.advance(m["t"])
        kind = m["kind"]
        if kind == "meta":
            self._meta(m)
        elif kind == "human":
            self._human(m)
        elif kind == "pbp":
            self._pbp(m)
        elif self._frozen() and kind in ("bug", "cv_make", "cue"):
            self.raw_ignored += 1                                # FREEZE_ON_REPLAY: stored raw, never used
            self._log("latency_report", m.get("field", kind), "ignored_in_freeze", what=kind, level=self.level())
        elif kind == "bug":
            if m.get("period") is not None and m.get("clock_s") is not None:
                if self.period.value is None:
                    self._period_step(m["period"], self.t)
                self._clock_read(m["period"], float(m["clock_s"]))
                if self.period.value == m["period"]:
                    self.period.obs_t, self.period.bug_t, self.period.frozen = self.t, self.t, False
                    self.period.grade = self.period.floor = "observed"
            if m.get("shot_s") is not None:
                self._shot_read(m["shot_s"])
            for name, k in self.k.items():
                if m.get(name) is not None:
                    self._counter_read(k, m[name])
        elif kind == "cue":
            self._cue(m["what"], m.get("value"))
        elif kind == "cv_make":
            self.pending_makes.append(m)                         # held back for replay_guard_s

    def _meta(self, m):
        what, on = m["what"], bool(m["on"])
        if what in ("replay", "break"):
            was = self._frozen()
            if on and not was:                                   # freeze: every game-state field holds its value
                for c in (self.c, self.sc):
                    if c.anchor is not None:
                        c.anchor, c.anchor_t, c.frozen_at = self.clock_est(c), self.t, self.t
                if self.sc.anchor is not None:
                    self.sc_ref = self.clock_est(self.c)
                dropped = [p for p in self.pending_makes if p["t"] >= self.t - self.spec.P["replay_guard_s"]]
                for p in dropped:                                # the replay detector objected inside the guard
                    self.pending_makes.remove(p)
                    self.raw_ignored += 1
                    self._log("latency_report", p["field"], "ignored_in_freeze", what="cv_make", level="D3_replay")
            setattr(self, "replay" if what == "replay" else "brk", on)
            if on:
                for k in list(self.k.values()) + [self.period]:
                    k.frozen, k.cand, k.cand_n = True, None, 0
                    k.brk_seen = k.brk_seen or what == "break"
            if was and not self._frozen():                       # back: nothing is trusted until it is read again
                for c in (self.c, self.sc):
                    if c.anchor is not None:
                        c.anchor_t, c.frozen_at, c.reads, c.floor = self.t, None, 0, self.spec.worst(c.floor, "carried")
                        c.seen_t = self.t                        # the carried limit counts from the return
                if self.sc.anchor is not None:
                    self.sc_ref = self.clock_est(self.c)
                self._log("latency_report", "degradation_level", "reacquire" if what == "break" else "replay_end")
        elif what == "main_camera":
            self.main_camera = self.rim_watch = on
        elif what == "feed":
            self.feed = on
        elif what == "audio":
            self.audio = on

    def _human(self, m):
        """A review answer wins every value (conflict rule of the field); the raw reading stays."""
        f, v = m["field"], m["value"]
        self.version += 1
        if f == "game_clock_s":
            self._log("state_corrections", f, "review_answer", old=self.clock_est(), new=v)
            c = self.c
            c.read, c.read_t, c.anchor, c.anchor_t, c.seen_t, c.base_t, c.floor, c.reads = float(v), self.t, float(v), self.t, self.t, self.t, "observed", 9
            self._write(f, v, "observed", event_t=self.t, src="human")
            return
        k = self.period if f == "period" else self.k[f]
        self._log("state_corrections", f, "review_answer", old=k.value, new=v)
        k.agree, k.obs_t, k.book_hold = {"human"}, self.t, v
        self._set(k, v, "observed", "human", event_t=m.get("event_t", self.t), supersedes=self._last_id(k))

    def snapshot(self):
        """{field: {"value", "grade", "age_s", "known_at"}}; the clocks also carry the guaranteed interval lo, hi.
        No value is ever None: what cannot be known is the string "unknown"."""
        c, t, out = self.c, self.t, {}
        g = self._clock_grade()
        if c.read is None:
            out["game_clock_s"] = {"value": UNKNOWN, "grade": UNKNOWN, "age_s": 0.0, "known_at": t, "lo": None, "hi": None}
        else:
            seen = not self._bug_away(c.read_t) and not self._frozen()
            lo = c.read if seen else max(0.0, c.read - (t - c.read_t))
            est = min(max(self.clock_est(), lo), c.read)
            out["game_clock_s"] = {"value": UNKNOWN if g == UNKNOWN else est, "grade": g, "age_s": t - c.read_t,
                                   "known_at": c.read_t, "lo": lo, "hi": c.read}
        rv, rg = self._running_state()
        out["game_clock_running"] = {"value": rv, "grade": rg, "age_s": 0.0 if c.run_seen_t is None else t - c.run_seen_t,
                                     "known_at": c.run_seen_t if c.run_seen_t is not None else t}
        sv, sg = self._shot_state()
        out["shot_clock_s"] = {"value": sv, "grade": sg, "age_s": 0.0 if self.sc.read_t is None else t - self.sc.read_t,
                               "known_at": self.sc.read_t if self.sc.read_t is not None else t}
        for name, k in [("period", self.period)] + list(self.k.items()):
            v, kg, age = self._counter_state(k)
            out[name] = {"value": v, "grade": kg, "age_s": age or 0.0, "known_at": k.known_at if k.known_at is not None else t}
        return out
