from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Sequence


@dataclass(frozen=True)
class ModEntry:
    mod_key: str
    kind: str
    domain: str
    family_key: str
    required_level: int
    name: str
    text: str
    text_norm: str
    stats: list[dict[str, Any]]
    spawn_tags: set[str]


@dataclass(frozen=True)
class UnresolvedTier:
    slug: str
    family_key: str
    kind: str
    level: int | None
    name: str | None
    text: str | None


@dataclass(frozen=True)
class BuildResult:
    items_written: int
    affixes_written: int
    tiers_written: int
    unresolved_tiers: Sequence[UnresolvedTier]
    mapping_warnings: Dict[str, list[dict[str, Any]]]


@dataclass(frozen=True)
class RebuildResult:
    items: int
    affixes: int
    tiers: int
    report: Dict[str, Any]


@dataclass(frozen=True)
class MatchExplanation:
    score: int
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManifestTier:
    level: int | None
    name: str
    text: str
    stats: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManifestAffix:
    kind: str
    family_key: str
    template: str
    tiers: tuple[ManifestTier, ...]


@dataclass(frozen=True)
class ManifestItem:
    slug: str
    category: str
    label: str
    include_domains: tuple[str, ...]
    include_spawn_tags: tuple[str, ...]
    affixes: tuple[ManifestAffix, ...]


@dataclass(frozen=True)
class ManifestDocument:
    version: int
    items: tuple[ManifestItem, ...]


@dataclass(frozen=True)
class SnapshotTier:
    level: int | None
    name: str
    text: str
    drop_chance: int | None = None


@dataclass(frozen=True)
class SnapshotAffix:
    kind: str
    family_key: str
    template: str
    tiers: tuple[SnapshotTier, ...]


@dataclass(frozen=True)
class SnapshotItem:
    slug: str
    category: str
    label: str
    href: str
    affixes: tuple[SnapshotAffix, ...]


@dataclass(frozen=True)
class SnapshotDocument:
    version: int
    source: str
    fetched_at: str
    items: tuple[SnapshotItem, ...]


@dataclass(frozen=True)
class OutputTier:
    level: int | None
    name: str | None
    text: str | None
    stats: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class OutputAffix:
    family_key: str
    kind: str
    template: str
    tiers: tuple[OutputTier, ...]


@dataclass(frozen=True)
class OutputItem:
    slug: str
    category: str
    label: str
    affixes: tuple[OutputAffix, ...]


@dataclass(frozen=True)
class BuildReport:
    items_written: int
    affixes_written: int
    tiers_written: int
    unresolved_tiers: tuple[UnresolvedTier, ...]
    mapping_warnings: Dict[str, list[dict[str, Any]]]


@dataclass(frozen=True)
class RebuildReport:
    ok: bool
    items: int
    affixes: int
    tiers: int
    unresolved_mod_matches: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class MappingValidationReport:
    items: int
    items_with_warnings: int
    warnings: Dict[str, list[dict[str, Any]]]


@dataclass(frozen=True)
class RefreshReport:
    ok: bool
    source: str
    started_at_utc: str
    finished_at_utc: str
    duration_seconds: float
    items_fetched: int
    affixes_fetched: int
    tiers_fetched: int
    snapshot_sha256: str
    snapshot_path: str


@dataclass(frozen=True)
class ItemLink:
    category: str
    label: str
    href: str
    slug: str


def copy_mapping_list(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def copy_mapping_dict_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(dict(row) for row in rows)
