"""R-MK-06, R-MK-07: ESPN-ID matching rules and the team-name guards."""
from datetime import date

from msu_alpha.markets.matching import TeamCrosswalk, match_game, normalise_name
from msu_alpha.markets.models import Game, MatchReason, TeamXwalkEntry
from msu_alpha.markets.timeutil import parse_utc

MSU, UK, UCONN, MICH = "127", "96", "41", "130"


def _g(gid, home, away, tip, status="scheduled"):
    return Game(gid, 2026, home, away, parse_utc(tip), status=status)


GAMES = [
    _g("401825481", UK, MSU, "2025-11-19T02:00:00Z"),               # neutral site, ESPN lists UK home
    _g("401860001", UCONN, MSU, "2026-03-28T01:55:00Z"),
    _g("401850010", MICH, MSU, "2026-03-13T23:00:00Z"),             # conference tournament ...
    _g("401850011", MSU, MICH, "2026-03-15T21:00:00Z"),             # ... rematch two days later
]


def test_neutral_site_home_flip_still_matches():
    # Polymarket lists MSU as home for this game; matching uses the unordered pair
    d = match_game(MSU, UK, GAMES, start_utc=parse_utc("2025-11-19T02:00:00Z"), candidate_window_s=10800)
    assert d.game_id == "401825481" and d.reason is None


def test_eastern_date_vs_utc():
    # Kalshi gives only the Eastern date 26MAR27; ESPN tip is 2026-03-28T01:55Z
    d = match_game(MSU, UCONN, GAMES, event_date_eastern=date(2026, 3, 27))
    assert d.game_id == "401860001"


def test_candidate_but_not_auto_accepted_beyond_5400s():
    d = match_game(MSU, UCONN, GAMES, start_utc=parse_utc("2026-03-28T03:55:00Z"), candidate_window_s=10800)
    assert d.game_id is None and d.reason == MatchReason.TIME_DIFF_GT_TOLERANCE and d.candidates == ["401860001"]


def test_conference_tournament_rematch_resolved_by_time():
    d = match_game(MSU, MICH, GAMES, start_utc=parse_utc("2026-03-15T21:05:00Z"), candidate_window_s=10800)
    assert d.game_id == "401850011"


def test_wide_window_with_two_candidates_goes_to_queue():
    d = match_game(MSU, MICH, GAMES, start_utc=parse_utc("2026-03-14T22:00:00Z"), candidate_window_s=129600)
    assert d.game_id is None and d.reason == MatchReason.MULTIPLE_CANDIDATES


def test_no_candidate_and_unmapped_and_postponed():
    assert match_game(MSU, "999", GAMES, start_utc=parse_utc("2026-03-15T21:00:00Z"),
                      candidate_window_s=10800).reason == MatchReason.NO_CANDIDATE
    assert match_game(None, MSU, GAMES).reason == MatchReason.TEAM_UNMAPPED
    pp = [_g("1", MSU, UK, "2026-01-01T00:00:00Z", status="postponed")]
    assert match_game(MSU, UK, pp, start_utc=parse_utc("2026-01-01T00:00:00Z"),
                      candidate_window_s=10800).reason == MatchReason.ESPN_POSTPONED_OR_CANCELED


def test_normalisation():
    assert normalise_name("Michigan State") == normalise_name("Michigan St.") == "michigan st"
    assert normalise_name("Texas A&M") == "texas a and m"


def _xwalk():
    x = TeamCrosswalk()
    for espn, name in [(MSU, "Michigan State"), (MICH, "Michigan"), ("2599", "St. John's"),
                       ("2603", "Saint Joseph's"), ("41", "UConn")]:
        x.add(TeamXwalkEntry(espn, "polymarket", name.lower(), name, "2025-07-01"))
    return x


def test_state_guard_never_fuzzy_matches_michigan_to_michigan_state():
    x = _xwalk()
    assert x.lookup("polymarket", name="Michigan St").espn_team_id == MSU          # exact after normalising
    r = x.lookup("polymarket", name="Michigan Wolverine")
    assert r.espn_team_id in (None, MICH)
    assert x.lookup("polymarket", name="Michigan Stat").espn_team_id != MICH


def test_saint_names_never_auto_accepted_by_fuzzy():
    x = _xwalk()
    assert x.lookup("polymarket", name="St Johns Red Storm").espn_team_id is None
    assert x.lookup("polymarket", name="St. John's").espn_team_id == "2599"           # exact still works


def test_exact_key_wins():
    x = _xwalk()
    assert x.lookup("polymarket", key="uconn").espn_team_id == "41"
