from __future__ import annotations

from typing import Any, Mapping

from poe_affix_builder.domain.models import OutputAffix, OutputItem, OutputTier


def output_item_from_dict(data: Mapping[str, Any]) -> OutputItem:
    affixes = []
    for affix in data.get("affixes") or []:
        tiers = []
        for tier in affix.get("tiers") or []:
            stats = []
            for row in tier.get("stats") or []:
                if isinstance(row, Mapping):
                    stats.append(dict(row))
            tiers.append(
                OutputTier(
                    level=tier.get("level") if isinstance(tier.get("level"), int) else None,
                    name=tier.get("name") if isinstance(tier.get("name"), str) else None,
                    text=tier.get("text") if isinstance(tier.get("text"), str) else None,
                    stats=tuple(stats),
                )
            )
        affixes.append(
            OutputAffix(
                family_key=str(affix.get("family_key") or ""),
                kind=str(affix.get("kind") or ""),
                template=str(affix.get("template") or ""),
                tiers=tuple(tiers),
            )
        )
    return OutputItem(
        slug=str(data.get("slug") or ""),
        category=str(data.get("category") or ""),
        label=str(data.get("label") or ""),
        affixes=tuple(affixes),
    )


def output_item_to_dict(item: OutputItem) -> dict[str, Any]:
    return {
        "affixes": [
            {
                "family_key": affix.family_key,
                "kind": affix.kind,
                "template": affix.template,
                "tiers": [
                    {
                        "level": tier.level,
                        "name": tier.name,
                        "text": tier.text,
                        **({"stats": [dict(row) for row in tier.stats]} if tier.stats else {}),
                    }
                    for tier in affix.tiers
                ],
            }
            for affix in item.affixes
        ],
        "category": item.category,
        "label": item.label,
        "slug": item.slug,
    }
