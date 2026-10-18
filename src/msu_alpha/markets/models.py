"""Typed records for the market tables (design section 3.2 and the supporting tables).

One SnapshotRow = one priced outcome of one market of one book or exchange at one snapshot.
Spreads and moneylines are stored per team (ESPN team ID), never as home/away.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any

from . import SCHEMA_VERSION


class Source(str, Enum):
    CBBD = "cbbd"
    ESPN = "espn"
    SBRO = "sbro"
    ODDSAPI = "oddsapi"
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"
    POLYMARKET_US = "polymarket_us"


class Market(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    MONEYLINE_1H = "moneyline_1h"
    SPREAD_1H = "spread_1h"
    TOTAL_1H = "total_1h"
    TEAM_TOTAL = "team_total"
    PROP_POINTS = "prop_points"
    PROP_REBOUNDS = "prop_rebounds"
    PROP_ASSISTS = "prop_assists"
    PROP_THREES = "prop_threes"
    PROP_PRA = "prop_pra"

    @property
    def is_spread(self) -> bool:
        return self in (Market.SPREAD, Market.SPREAD_1H)

    @property
    def is_total(self) -> bool:
        return self in (Market.TOTAL, Market.TOTAL_1H, Market.TEAM_TOTAL)


class Side(str, Enum):
    TEAM = "team"
    OVER = "over"
    UNDER = "under"
    YES = "yes"
    NO = "no"


class Phase(str, Enum):
    PREGAME = "pregame"
    LIVE = "live"


class SnapshotLabel(str, Enum):
    OPEN = "open"
    OPEN_FIRST_SEEN = "open_first_seen"
    OPEN_REPORTED = "open_reported"
    T_24H = "t-24h"
    T_1H = "t-1h"
    CLOSE = "close"
    CLOSE_REPORTED = "close_reported"
    GAMEDAY = "gameday"
    SWEEP = "sweep"
    INPLAY_1M = "inplay_1m"
    MOVEMENT = "movement"


class ProviderType(str, Enum):
    BOOK = "book"
    CONSENSUS = "consensus"
    MODEL = "model"
    EXCHANGE = "exchange"
    LIVE = "live"


class MatchReason(str, Enum):
    TEAM_UNMAPPED = "team_unmapped"
    NO_CANDIDATE = "no_candidate"
    MULTIPLE_CANDIDATES = "multiple_candidates"
    TIME_DIFF_GT_TOLERANCE = "time_diff_gt_tolerance"
    ESPN_POSTPONED_OR_CANCELED = "espn_postponed_or_canceled"
    SOURCE_EVENT_ID_CHANGED = "source_event_id_changed"
    NULL_SOURCE_ID = "null_source_id"
    SCORE_MISMATCH = "score_mismatch"
    SETTLEMENT_MISMATCH = "settlement_mismatch"


@dataclass
class SnapshotRow:
    source: Source
    book: str
    market: Market
    side: Side
    snapshot_time_utc: datetime
    fetched_at_utc: datetime
    season: int
    source_event_id: str
    raw_ref: str
    game_id: str | None = None          # ESPN event ID; null until matched
    market_phase: Phase = Phase.PREGAME
    team_id: str | None = None          # ESPN team ID (spreads, moneylines, team totals)
    player_id: str | None = None        # ESPN athlete ID (props)
    line: float | None = None           # signed from this team's point of view (-2.5 gives 2.5)
    line_is_integer: bool = False
    price_american: int | None = None
    price_decimal: float | None = None
    price_decimal_source: float | None = None
    implied_prob: float | None = None
    booksum: float | None = None
    fair_prob_power: float | None = None
    fair_prob_shin: float | None = None
    fair_prob_mult: float | None = None
    power_k: float | None = None
    shin_z: float | None = None
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    bid_size: float | None = None
    ask_size: float | None = None
    volume: float | None = None
    open_interest: float | None = None
    source_time_utc: datetime | None = None
    snapshot_label: SnapshotLabel = SnapshotLabel.SWEEP
    observed_post_event: bool = False
    dq_flags: list[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.line is not None:
            self.line_is_integer = float(self.line).is_integer()

    def dedup_key(self) -> tuple:
        """C-14 uniqueness key (also the store's dedup key). source_event_id is included so two
        unmatched events (game_id null) with the same line never collide."""
        return (
            self.game_id, self.source_event_id, self.source.value, self.book, self.market.value, self.market_phase.value,
            self.snapshot_label.value, self.side.value, self.team_id or self.player_id,
            self.line, self.snapshot_time_utc,
        )

    def group_key(self) -> tuple:
        """Rows that form one complementary set for margin removal: (event, book, market, line, snapshot)."""
        line_key = abs(self.line) if (self.line is not None and self.market.is_spread) else self.line
        return (
            self.source_event_id, self.source.value, self.book, self.market.value, self.market_phase.value,
            self.snapshot_label.value, self.player_id, line_key, self.snapshot_time_utc,
        )

    def flag(self, rule_id: str) -> None:
        if rule_id not in self.dq_flags:
            self.dq_flags.append(rule_id)

    def to_record(self) -> dict[str, Any]:
        rec = asdict(self)
        for k, v in rec.items():
            if isinstance(v, Enum):
                rec[k] = v.value
        return rec


SNAPSHOT_COLUMNS = [f.name for f in fields(SnapshotRow)]


@dataclass
class ManifestEntry:
    fetched_at_utc: str
    source: str
    method: str
    endpoint: str
    url: str                      # credentials removed
    status: int
    headers: dict[str, str]
    sha256: str
    byte_length: int
    body_path: str
    collector_version: str
    run_id: str
    job_id: str
    request_body: str | None = None
    redacted_fields: list[str] = field(default_factory=list)
    sha256_received: str | None = None   # equals sha256 unless fields were redacted before storage


@dataclass
class Game:
    game_id: str                  # ESPN event ID
    season: int
    home_team_id: str
    away_team_id: str
    scheduled_tip_utc: datetime
    neutral_site: bool = False
    conference_game: bool = False
    status: str = "scheduled"
    actual_tip_utc: datetime | None = None
    home_score: int | None = None
    away_score: int | None = None

    @property
    def tip_utc(self) -> datetime:
        return self.actual_tip_utc or self.scheduled_tip_utc

    @property
    def team_pair(self) -> frozenset[str]:
        return frozenset((self.home_team_id, self.away_team_id))


@dataclass
class Provider:
    source: str
    provider_id: str
    name: str
    provider_type: ProviderType
    valid_from: str


@dataclass
class TeamXwalkEntry:
    espn_team_id: str
    source: str
    source_team_key: str
    source_team_name: str
    valid_from: str
    valid_to: str | None = None
    method: str = "manual"
    reviewed_by: str | None = None


@dataclass
class SourceEventMapEntry:
    source: str
    source_event_id: str
    espn_game_id: str
    method: str
    confidence: float
    valid_from: str


@dataclass
class MatchQueueItem:
    source: str
    source_event_id: str
    raw_ref: str
    team_a_raw: str
    team_b_raw: str
    start_raw: str | None
    candidates: list[str]
    reason: MatchReason
    first_seen_utc: str
    resolved_espn_game_id: str | None = None
    resolved_by: str | None = None
    resolved_utc: str | None = None


@dataclass
class QuarantineRow:
    rule_id: str
    row: dict[str, Any]
    raw_ref: str
    first_seen_utc: str
    resolved_by: str | None = None
    resolved_utc: str | None = None
    resolution: str | None = None
