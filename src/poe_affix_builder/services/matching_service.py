from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Sequence

from poe_affix_builder.domain.models import MatchExplanation, ModEntry
from poe_affix_builder.normalize import normalize_compare_text


@dataclass(frozen=True)
class BuildIndexes:
    by_name: Dict[tuple[str, str, int, str], list[ModEntry]]
    by_text: Dict[tuple[str, str, int, str], list[ModEntry]]
    by_level: Dict[tuple[str, str, int], list[ModEntry]]
    by_name_any_kind: Dict[tuple[str, int, str], list[ModEntry]]
    by_text_any_kind: Dict[tuple[str, int, str], list[ModEntry]]
    by_level_any_kind: Dict[tuple[str, int], list[ModEntry]]


@dataclass(frozen=True)
class MatchDecision:
    entry: ModEntry | None
    explanation: MatchExplanation


def build_indexes(entries: Iterable[ModEntry]) -> BuildIndexes:
    by_name: Dict[tuple[str, str, int, str], list[ModEntry]] = defaultdict(list)
    by_text: Dict[tuple[str, str, int, str], list[ModEntry]] = defaultdict(list)
    by_level: Dict[tuple[str, str, int], list[ModEntry]] = defaultdict(list)
    by_name_any_kind: Dict[tuple[str, int, str], list[ModEntry]] = defaultdict(list)
    by_text_any_kind: Dict[tuple[str, int, str], list[ModEntry]] = defaultdict(list)
    by_level_any_kind: Dict[tuple[str, int], list[ModEntry]] = defaultdict(list)

    for entry in entries:
        by_name[(entry.kind, entry.family_key, entry.required_level, entry.name)].append(entry)
        by_text[(entry.kind, entry.family_key, entry.required_level, entry.text_norm)].append(entry)
        by_level[(entry.kind, entry.family_key, entry.required_level)].append(entry)
        by_name_any_kind[(entry.family_key, entry.required_level, entry.name)].append(entry)
        by_text_any_kind[(entry.family_key, entry.required_level, entry.text_norm)].append(entry)
        by_level_any_kind[(entry.family_key, entry.required_level)].append(entry)

    return BuildIndexes(
        by_name=by_name,
        by_text=by_text,
        by_level=by_level,
        by_name_any_kind=by_name_any_kind,
        by_text_any_kind=by_text_any_kind,
        by_level_any_kind=by_level_any_kind,
    )


def build_family_index(entries: Iterable[ModEntry]) -> Dict[tuple[str, str], list[ModEntry]]:
    out: Dict[tuple[str, str], list[ModEntry]] = defaultdict(list)
    for entry in entries:
        out[(entry.kind, entry.family_key)].append(entry)
    return out


def candidate_families_for_item(entries: Iterable[ModEntry], include_domains: set[str], include_spawn_tags: set[str]) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for entry in entries:
        if include_domains and entry.domain not in include_domains:
            continue
        if include_spawn_tags and not (entry.spawn_tags & include_spawn_tags):
            continue
        out.add((entry.kind, entry.family_key))
    return out


def family_warning_detail(
    *,
    key: tuple[str, str],
    include_domains: set[str],
    include_spawn_tags: set[str],
    family_index: Dict[tuple[str, str], list[ModEntry]],
) -> Dict[str, Any]:
    kind, family_key = key
    all_entries = family_index.get(key, [])
    matching_entries = []
    for entry in all_entries:
        if include_domains and entry.domain not in include_domains:
            continue
        if include_spawn_tags and not (entry.spawn_tags & include_spawn_tags):
            continue
        matching_entries.append(entry)

    global_domains = sorted({entry.domain for entry in all_entries if entry.domain})
    matching_domains = sorted({entry.domain for entry in matching_entries if entry.domain})
    sample_spawn_tags = sorted({tag for entry in matching_entries for tag in entry.spawn_tags})[:15]
    sample_mod_keys = sorted({entry.mod_key for entry in matching_entries})[:8]
    sample_texts = sorted({entry.text for entry in matching_entries if entry.text})[:4]
    sample_stat_ids = sorted(
        {
            row.get("id")
            for entry in matching_entries
            for row in entry.stats
            if isinstance(row.get("id"), str) and row["id"]
        }
    )[:12]
    return {
        "kind": kind,
        "family_key": family_key,
        "matching_entry_count": len(matching_entries),
        "global_entry_count": len(all_entries),
        "matching_domains": matching_domains,
        "global_domains": global_domains,
        "sample_spawn_tags": sample_spawn_tags,
        "sample_mod_keys": sample_mod_keys,
        "sample_texts": sample_texts,
        "sample_stat_ids": sample_stat_ids,
    }


def extract_ref_stat_ids(tier: Dict[str, Any]) -> list[str]:
    out: list[str] = []
    for row in tier.get("stats") or []:
        if isinstance(row, str) and row:
            out.append(row)
        elif isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"]:
            out.append(row["id"])
    return out


def copy_stats(stats: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in stats:
        stat_id = row.get("id")
        if not isinstance(stat_id, str):
            continue
        item: dict[str, Any] = {"id": stat_id}
        if "max" in row:
            item["max"] = row.get("max")
        if "min" in row:
            item["min"] = row.get("min")
        out.append(item)
    return out


def collect_build_candidates(
    indexes: BuildIndexes,
    *,
    kind: str,
    family_key: str,
    level: int | None,
    name: str,
    text_ref: str | None,
) -> list[ModEntry]:
    if level is None:
        return []

    candidates: list[ModEntry] = []
    candidates.extend(indexes.by_name.get((kind, family_key, level, name), []))
    text_norm = normalize_compare_text(text_ref)
    if text_norm is not None:
        candidates.extend(indexes.by_text.get((kind, family_key, level, text_norm), []))
    candidates.extend(indexes.by_level.get((kind, family_key, level), []))

    if not candidates:
        candidates.extend(indexes.by_name_any_kind.get((family_key, level, name), []))
        if text_norm is not None:
            candidates.extend(indexes.by_text_any_kind.get((family_key, level, text_norm), []))
        candidates.extend(indexes.by_level_any_kind.get((family_key, level), []))

    deduped: list[ModEntry] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.mod_key not in seen:
            seen.add(candidate.mod_key)
            deduped.append(candidate)
    return deduped


def _score_build_candidate(
    entry: ModEntry,
    include_domains: set[str],
    include_spawn_tags: set[str],
    ref_text_norm: str | None,
    ref_name: str | None,
    ref_stat_ids: Sequence[str],
) -> MatchExplanation:
    score = 0
    reasons: list[str] = []
    if include_domains:
        if entry.domain in include_domains:
            score += 100
            reasons.append(f"domain:{entry.domain}")
        else:
            score -= 30
            reasons.append("domain-mismatch")
    if include_spawn_tags:
        overlap = len(entry.spawn_tags & include_spawn_tags)
        score += overlap * 10
        if overlap:
            reasons.append(f"spawn-tags:{overlap}")
    if ref_text_norm is not None and entry.text_norm == ref_text_norm:
        score += 30
        reasons.append("text-exact")
    if ref_name is not None and entry.name == ref_name:
        score += 10
        reasons.append("name-exact")
    if ref_stat_ids:
        entry_ids = tuple(row.get("id") for row in entry.stats if isinstance(row.get("id"), str))
        if tuple(ref_stat_ids) == entry_ids:
            score += 80
            reasons.append("stats-exact-order")
        elif set(ref_stat_ids) == set(entry_ids):
            score += 40
            reasons.append("stats-exact-set")
        else:
            score -= 10
            reasons.append("stats-mismatch")
    if entry.stats:
        score += 1
        reasons.append("has-stats")
    return MatchExplanation(score=score, reasons=tuple(reasons))


def select_build_candidate(
    candidates: Sequence[ModEntry],
    *,
    include_domains: set[str],
    include_spawn_tags: set[str],
    ref_text: str | None,
    ref_name: str | None,
    ref_stat_ids: Sequence[str],
) -> MatchDecision:
    if not candidates:
        return MatchDecision(entry=None, explanation=MatchExplanation(score=0, reasons=("no-candidates",)))
    ref_text_norm = normalize_compare_text(ref_text)
    scored = [
        (_score_build_candidate(candidate, include_domains, include_spawn_tags, ref_text_norm, ref_name, ref_stat_ids), candidate.mod_key, candidate)
        for candidate in candidates
    ]
    scored.sort(key=lambda row: (row[0].score, row[1]), reverse=True)
    explanation, _, entry = scored[0]
    return MatchDecision(entry=entry, explanation=explanation)


def index_entries_by_family_level(entries: Iterable[ModEntry]) -> Dict[tuple[str, int], list[ModEntry]]:
    indexed: Dict[tuple[str, int], list[ModEntry]] = {}
    for entry in entries:
        key = (entry.family_key, entry.required_level)
        indexed.setdefault(key, []).append(entry)
    for key, rows in indexed.items():
        indexed[key] = sorted(rows, key=lambda item: item.mod_key)
    return indexed


def _score_rebuild_candidate(
    entry: ModEntry,
    *,
    kind: str,
    text: str | None,
    name: str | None,
    include_domains: set[str],
    include_spawn_tags: set[str],
) -> MatchExplanation:
    score = 0
    reasons: list[str] = []
    if entry.kind == kind:
        score += 80
        reasons.append("kind-exact")
    if include_domains:
        if entry.domain in include_domains:
            score += 40
            reasons.append(f"domain:{entry.domain}")
        else:
            score -= 20
            reasons.append("domain-mismatch")
    if include_spawn_tags:
        overlap = len(entry.spawn_tags & include_spawn_tags)
        score += overlap * 8
        if overlap:
            reasons.append(f"spawn-tags:{overlap}")
    text_norm = normalize_compare_text(text)
    if text_norm is not None and entry.text_norm == text_norm:
        score += 40
        reasons.append("text-exact")
    if name and entry.name == name:
        score += 20
        reasons.append("name-exact")
    return MatchExplanation(score=score, reasons=tuple(reasons))


def select_rebuild_candidate(
    candidates: Sequence[ModEntry],
    *,
    kind: str,
    text: str | None,
    name: str | None,
    include_domains: set[str],
    include_spawn_tags: set[str],
) -> MatchDecision:
    if not candidates:
        return MatchDecision(entry=None, explanation=MatchExplanation(score=0, reasons=("no-candidates",)))
    scored = [
        (_score_rebuild_candidate(candidate, kind=kind, text=text, name=name, include_domains=include_domains, include_spawn_tags=include_spawn_tags), candidate.mod_key, candidate)
        for candidate in candidates
    ]
    scored.sort(key=lambda row: (row[0].score, row[1]), reverse=True)
    explanation, _, entry = scored[0]
    return MatchDecision(entry=entry, explanation=explanation)
