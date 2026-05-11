from __future__ import annotations

from typing import Any, Iterable, Mapping

from poe_affix_builder.policies.section_rules import (
    EXPECTED_NON_NORMAL_UNRESOLVED,
    NORMAL_UNRESOLVED,
    UNKNOWN_UNRESOLVED,
    unresolved_reason_code,
)

DIAGNOSTICS_CONTRACT_VERSION = 1
UNRESOLVED_CATEGORIES = (NORMAL_UNRESOLVED, EXPECTED_NON_NORMAL_UNRESOLVED, UNKNOWN_UNRESOLVED)


def classify_unresolved_match(row: Mapping[str, Any]) -> dict[str, Any]:
    section = str(row.get("section") or "unknown")
    reason_code = unresolved_reason_code(section)
    explanation = row.get("match_explanation") or ("no-candidates",)
    return {
        "section": section,
        "slug": str(row.get("slug") or ""),
        "kind": str(row.get("kind") or ""),
        "family_key": str(row.get("family_key") or ""),
        "level": row.get("level") if isinstance(row.get("level"), int) else None,
        "reason_code": reason_code,
        "match_explanation": [str(item) for item in explanation],
    }


def unresolved_diagnostics_to_dict(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    categories: dict[str, list[dict[str, Any]]] = {key: [] for key in UNRESOLVED_CATEGORIES}
    for row in rows:
        classified = classify_unresolved_match(row)
        categories[classified["reason_code"]].append(classified)

    return {
        "version": DIAGNOSTICS_CONTRACT_VERSION,
        "summary": {key: len(value) for key, value in categories.items()},
        "unresolved_matches": categories,
    }
