from __future__ import annotations

from typing import Any, Mapping

from poe_affix_builder.domain.models import OutputAffix, OutputBase, OutputItem, OutputModifierSection, OutputTier

OUTPUT_CONTRACT_VERSION = 1


def _output_affixes_from_rows(rows: list[Any] | tuple[Any, ...]) -> tuple[OutputAffix, ...]:
    affixes = []
    for affix in rows or []:
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
    return tuple(affixes)


def output_item_from_dict(data: Mapping[str, Any]) -> OutputItem:
    bases = []
    for base in data.get("bases") or []:
        bases.append(
            OutputBase(
                name=str(base.get("name") or ""),
                href=str(base.get("href") or ""),
                required_level=base.get("required_level") if isinstance(base.get("required_level"), int) else None,
            )
        )
    modifier_sections = []
    for name, rows in (data.get("modifier_sections") or {}).items():
        modifier_sections.append(
            OutputModifierSection(
                name=str(name),
                affixes=_output_affixes_from_rows(rows if isinstance(rows, (list, tuple)) else []),
            )
        )
    affixes = _output_affixes_from_rows(data.get("affixes") or [])
    if not affixes:
        for section in modifier_sections:
            if section.name == "normal":
                affixes = section.affixes
                break
    elif not modifier_sections:
        modifier_sections.append(OutputModifierSection(name="normal", affixes=affixes))
    return OutputItem(
        slug=str(data.get("slug") or ""),
        category=str(data.get("category") or ""),
        label=str(data.get("label") or ""),
        bases=tuple(bases),
        modifier_sections=tuple(modifier_sections),
        affixes=affixes,
    )


def output_item_to_dict(item: OutputItem) -> dict[str, Any]:
    return {
        "category": item.category,
        "label": item.label,
        **(
            {
                "bases": [
                    {
                        "name": base.name,
                        "href": base.href,
                        "required_level": base.required_level,
                    }
                    for base in item.bases
                ]
            }
            if item.bases
            else {}
        ),
        **(
            {
                "modifier_sections": {
                    section.name: [
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
                        for affix in section.affixes
                    ]
                    for section in item.modifier_sections
                }
            }
            if item.modifier_sections
            else {}
        ),
        "slug": item.slug,
    }
