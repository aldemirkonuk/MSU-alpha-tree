"""Team crosswalk and game matching to the ESPN event ID (design section 5; R-MK-06, R-MK-07).

Rules (design 5.2):
1. Candidate search: same unordered ESPN team pair, and |dt| within the source's window
   (or US-Eastern date +-1 day when either side has no usable time).
2. Auto-accept: exactly one candidate and |dt| <= 5,400 s, or the same Eastern date when a time is missing.
3. Everything else goes to the review queue with a reason code.
Prices are always assigned by team ID, never by home/away.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime

from .models import Game, MatchReason, TeamXwalkEntry
from .timeutil import eastern_date, seconds_between

_ALIASES = [(r"\bstate\b", "st"), (r"\bst\.?(?=\s|$)", "st"), (r"&", " and "), (r"\buniv(ersity)?\b", "")]


def normalise_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    for pattern, repl in _ALIASES:
        s = re.sub(pattern, repl, s)
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _is_state_school(norm: str) -> bool:
    """'michigan st' or 'penn st nittany lions' (a non-leading 'st' token); 'st johns' is not."""
    return "st" in norm.split()[1:]


def _ambiguous_saint(norm: str) -> bool:
    return norm.startswith(("st ", "saint ", "mount st", "mt st"))


@dataclass
class TeamLookup:
    espn_team_id: str | None
    method: str                     # exact_key | exact_name | fuzzy | unmapped | refused_guard
    score: float | None = None


@dataclass
class TeamCrosswalk:
    entries: list[TeamXwalkEntry] = field(default_factory=list)

    def add(self, entry: TeamXwalkEntry) -> None:
        self.entries.append(entry)

    def lookup(self, source: str, key: str | None = None, name: str | None = None,
               accept_score: float = 95.0, runner_up_gap: float = 5.0) -> TeamLookup:
        rows = [e for e in self.entries if e.source == source]
        if key is not None:
            for e in rows:
                if e.source_team_key == str(key):
                    return TeamLookup(e.espn_team_id, "exact_key", 100.0)
        if not name:
            return TeamLookup(None, "unmapped")
        target = normalise_name(name)
        for e in rows:
            if normalise_name(e.source_team_name) == target:
                return TeamLookup(e.espn_team_id, "exact_name", 100.0)
        # Fuzzy fallback across every known name for this source; never across the State guard.
        scored = sorted(
            ((difflib.SequenceMatcher(None, target, normalise_name(e.source_team_name)).ratio() * 100.0, e)
             for e in rows),
            key=lambda t: -t[0],
        )
        if not scored:
            return TeamLookup(None, "unmapped")
        best_score, best = scored[0]
        runner = scored[1][0] if len(scored) > 1 else 0.0
        best_norm = normalise_name(best.source_team_name)
        if _is_state_school(target) != _is_state_school(best_norm) or _ambiguous_saint(target) or _ambiguous_saint(best_norm):
            return TeamLookup(None, "refused_guard", best_score)
        if best_score >= accept_score and best_score - runner >= runner_up_gap:
            return TeamLookup(best.espn_team_id, "fuzzy", best_score)
        return TeamLookup(None, "unmapped", best_score)


@dataclass
class MatchDecision:
    game_id: str | None
    reason: MatchReason | None
    candidates: list[str]


def match_game(
    team_a: str | None,
    team_b: str | None,
    games: list[Game],
    start_utc: datetime | None = None,
    event_date_eastern: date | None = None,
    candidate_window_s: float | None = None,
    auto_accept_s: float = 5400.0,
) -> MatchDecision:
    """Match one source event (both teams already mapped to ESPN team IDs) to an ESPN game."""
    if not team_a or not team_b:
        return MatchDecision(None, MatchReason.TEAM_UNMAPPED, [])
    pair = frozenset((team_a, team_b))
    src_date = event_date_eastern or (eastern_date(start_utc) if start_utc else None)

    def is_candidate(g: Game) -> bool:
        if g.team_pair != pair:
            return False
        if start_utc is not None and candidate_window_s is not None:
            return abs(seconds_between(g.scheduled_tip_utc, start_utc)) <= candidate_window_s
        if src_date is None:
            return False
        return abs((eastern_date(g.scheduled_tip_utc) - src_date).days) <= 1

    cands = [g for g in games if is_candidate(g)]
    ids = [g.game_id for g in cands]
    if not cands:
        return MatchDecision(None, MatchReason.NO_CANDIDATE, [])
    if len(cands) > 1:
        return MatchDecision(None, MatchReason.MULTIPLE_CANDIDATES, ids)
    g = cands[0]
    if g.status in ("postponed", "canceled", "cancelled"):
        return MatchDecision(None, MatchReason.ESPN_POSTPONED_OR_CANCELED, ids)
    if start_utc is not None and candidate_window_s is not None:
        ok = abs(seconds_between(g.scheduled_tip_utc, start_utc)) <= auto_accept_s
    else:
        ok = src_date is not None and eastern_date(g.scheduled_tip_utc) == src_date
    if ok:
        return MatchDecision(g.game_id, None, ids)
    return MatchDecision(None, MatchReason.TIME_DIFF_GT_TOLERANCE, ids)
