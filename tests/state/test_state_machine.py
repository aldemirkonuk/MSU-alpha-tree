"""config/state_machine.yaml, the K09 table specs and the pbp_only fold (tools/state/k09_fold.py).

No private data: the game below is synthetic and written to contain the CBBD ordering faults measured on
the two pilot games (free throws listed 2-of-2 first, substitutions before the whistle, End Game before
End Period, a team rebound without a player).
"""
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "state"))
import k09_fold as K  # noqa: E402

SM = K.load_machine()
CONST = K.load_constants()


# ---------------------------------------------------------------- config ----------------------------------

def test_every_transition_is_complete():
    dims = set(SM["dimensions"])
    for tt, spec in SM["transitions"].items():
        for k in ("name", "allowed_from", "to", "trigger", "rules", "changes", "seen_by"):
            assert k in spec, f"{tt} lacks {k}"
        if tt not in ("T25",):
            assert spec["rules"], f"{tt} has no rule reference"
        if spec["changes"] != "all":
            unknown = set(spec["changes"]) - dims
            assert not unknown, f"{tt} changes unknown dimensions {unknown}"


def test_flow_states_used_by_transitions_exist():
    states = set(SM["dimensions"]["flow_state"]["values"]) | {"final", "none", "same", "any"}
    for tt, spec in SM["transitions"].items():
        for key in ("allowed_from", "to"):
            v = spec[key]
            vals = [v] if isinstance(v, str) else v
            assert set(vals) <= states, f"{tt}.{key} uses unknown flow states {set(vals) - states}"


def test_dimensions_are_typed_and_team_neutral():
    for d, spec in SM["dimensions"].items():
        assert spec["stored"] in ("segment", "clock_map", "derived"), d
        assert not d.endswith(("_msu", "_opp")) and "msu_" not in d, f"{d} is not team-neutral (N-MD-02)"
        if spec["stored"] == "segment":
            assert spec["value_type"] in ("int", "enum", "bool", "list", "float"), d
            if spec["value_type"] == "enum":
                assert spec["values"], d


def test_pbp_mapping_targets_exist():
    types = set(SM["transitions"]) | {"annotation"}
    for pt, rule in SM["pbp_mapping"]["types"].items():
        items = rule if isinstance(rule, list) else [rule]
        for it in items:
            for key in ("ttype", "made", "missed"):
                if key in it:
                    vals = it[key] if isinstance(it[key], list) else [it[key]]
                    assert set(vals) <= types, f"{pt}: {vals}"


def test_constants_used_by_the_fold_exist():
    for k in ("bonus_team_foul", "double_bonus_team_foul", "players_per_team_on_court", "timeouts"):
        assert k in CONST
    assert {"clock_rate_tolerance", "running_min_anchor_gap_s"} <= set(SM["constants"])


@pytest.mark.parametrize("table", ["clock_map", "state_transitions", "state_segments"])
def test_table_specs(table):
    spec = yaml.safe_load((REPO / "schema" / "tables" / f"{table}.yaml").read_text())
    cols = spec["columns"]
    assert set(spec["primary_key"]) <= set(cols), f"{table}: key column missing"
    for name, c in cols.items():
        for k in ("type", "nullable", "definition", "licence", "as_of", "requirements"):
            assert k in c, f"{table}.{name} lacks {k}"
    assert "state_version" in cols and "pass" in cols


# ---------------------------------------------------------------- synthetic game ---------------------------

HOME, AWAY = "Home U", "Away St"
H = [{"id": i, "name": f"h{i}", "team": HOME} for i in range(1, 7)]
A = [{"id": i, "name": f"a{i}", "team": AWAY} for i in range(11, 17)]


def row(rid, period, sec, pt, side, text, hs, as_, scoring=False, value=0, players=(), on=None):
    on = on if on is not None else H[:5] + A[:5]
    return {"id": rid, "period": period, "secondsRemaining": sec, "clock": f"{sec // 60}:{sec % 60:02d}", "playType": pt,
            "isHomeTeam": {"home": True, "away": False}.get(side), "team": {"home": HOME, "away": AWAY}.get(side),
            "playText": text, "homeScore": hs, "awayScore": as_, "scoringPlay": scoring, "scoreValue": value,
            "participants": [{"id": p} for p in players], "onFloor": on, "wallclock": None}


def synthetic_game():
    on2 = H[1:6] + A[:5]          # h1 out, h6 in after the free throws at 1100
    r = [
        row(1, 1, 1200, "Jumpball", None, "Start game", 0, 0),
        row(2, 1, 1199, "Jumpball", "home", "Jump Ball won by Home U", 0, 0),
        row(3, 1, 1180, "JumpShot", "home", "h2 makes three", 3, 0, True, 3, [2]),
        row(4, 1, 1160, "LayUpShot", "away", "a11 misses layup", 3, 0, False, 2, [11]),
        row(5, 1, 1158, "Defensive Rebound", "home", "UConn-like team rebound", 3, 0),              # team rebound, no player
        # free throws listed 2 of 2 first, substitution and foul out of order (as measured on CBBD)
        row(6, 1, 1100, "Substitution", "home", "h6 subbing in for Home U", 3, 2, players=[6]),
        row(7, 1, 1100, "MadeFreeThrow", "away", "a12 makes free throw 2 of 2", 3, 2, True, 1, [12]),
        row(8, 1, 1100, "MadeFreeThrow", "away", "a12 makes free throw 1 of 2", 3, 1, True, 1, [12]),
        row(9, 1, 1100, "Substitution", "home", "h1 subbing out for Home U", 3, 2, players=[1]),
        row(10, 1, 1100, "PersonalFoul", "home", "Foul on h3.", 3, 0, players=[3]),
        row(11, 1, 1080, "JumpShot", "home", "h2 misses jumper", 3, 2, False, 2, [2], on=on2),
        row(12, 1, 1078, "Defensive Rebound", "away", "a13 Defensive Rebound.", 3, 2, players=[13], on=on2),
        row(13, 1, 1060, "Lost Ball Turnover", "away", "a13 bad pass turnover", 3, 2, players=[13], on=on2),
        row(14, 1, 1060, "Steal", "home", "h4 Steal.", 3, 2, players=[4], on=on2),
        row(15, 1, 1050, "ShortTimeOut", "away", "Away St Timeout", 3, 2, on=on2),
        row(16, 1, 1040, "DunkShot", "home", "h6 makes dunk", 5, 2, True, 2, [6], on=on2),
        row(17, 1, 0, "End Game", None, "End of Game", 5, 2, on=on2),       # out of order on purpose
        row(18, 1, 0, "End Period", None, "End of 1st half", 5, 2, on=on2),
    ]
    game = {"sourceId": "999", "homeTeam": HOME, "awayTeam": AWAY, "homePoints": 5, "awayPoints": 2}
    return game, r


def run_synthetic():
    game, plays = synthetic_game()
    ty = K.Typer(SM, CONST, HOME)
    T = ty.run(plays, (5, 2))
    K.finalise_ids(T, "999")
    return ty, T


def test_synthetic_game_has_no_breaks():
    ty, T = run_synthetic()
    assert dict(ty.breaks) == {}
    assert ty.state["score_home"] == 5 and ty.state["score_away"] == 2
    assert ty.flow == "final"


def test_reordering_fixes_measured_cbbd_faults():
    ty, _ = run_synthetic()
    order = [p["id"] for p in ty.plays]
    assert order.index(10) < order.index(8) < order.index(7)        # foul, then FT 1, then FT 2
    assert order.index(18) < order.index(17)                        # End Period before End Game
    assert ty.notes["ORD-03 rows moved inside an instant"] > 0


def test_lineup_from_substitution_rows():
    _, T = run_synthetic()
    subs = [t for t in T if t.ttype == "T22"]
    assert len(subs) == 1
    assert subs[0].changes["lineup_home"] == "2|3|4|5|6"


def test_team_rebound_after_a_try_is_out_of_bounds():
    _, T = run_synthetic()
    t13 = [t for t in T if t.ttype == "T13" and t.subtype == "out_of_bounds_after_try"]
    assert len(t13) == 1 and t13[0].changes["possession_team"] == "home"


def test_turnover_with_steal_is_one_live_change_of_control():
    _, T = run_synthetic()
    assert [t.ttype for t in T].count("T03") == 1


def test_timeout_resumes_with_inferred_t26():
    _, T = run_synthetic()
    seq = [t.ttype for t in T]
    i = seq.index("T16")
    assert seq[i + 1] == "T26" and T[i + 1].inferred


def test_segments_integrity_and_view_equals_reference():
    _, T = run_synthetic()
    segs = K.fold(T)
    assert dict(K.check_segments(segs, T)) == {}
    diff, cells = K.view_equals_reference(segs, T)
    assert cells > 0 and diff == 0


def test_transition_ids_are_deterministic():
    _, T1 = run_synthetic()
    _, T2 = run_synthetic()
    assert [t.transition_id for t in T1] == [t.transition_id for t in T2]
    assert len({t.transition_id for t in T1}) == len(T1)


def test_clock_map_classifies_running_stopped_and_cut():
    samples = [
        {"video_time_s": "0", "period": "1ST", "period_present": "y", "game_clock_present": "y", "game_clock": "20:00"},
        {"video_time_s": "60", "period": "1ST", "period_present": "y", "game_clock_present": "y", "game_clock": "19:00"},   # running
        {"video_time_s": "120", "period": "1ST", "period_present": "y", "game_clock_present": "y", "game_clock": "19:00"},  # stopped
        {"video_time_s": "180", "period": "1ST", "period_present": "y", "game_clock_present": "y", "game_clock": "16:00"},  # cut
    ]
    rows, stats = K.clock_map_from_ocr(samples, 0.02, 5)
    assert [r["status"] for r in rows] == ["running", "stopped", "cut"]
    assert rows[0]["from_gc_ds"] == 12000 and rows[0]["to_gc_ds"] == 11400
