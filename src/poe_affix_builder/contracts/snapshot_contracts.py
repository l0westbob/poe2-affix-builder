from __future__ import annotations

from typing import Any, Mapping

from poe_affix_builder.domain.models import (
    SnapshotAffix,
    SnapshotBase,
    SnapshotDocument,
    SnapshotItem,
    SnapshotModifierSection,
    SnapshotTier,
)


def snapshot_from_dict(data: Mapping[str, Any]) -> SnapshotDocument:
    items = []
    for item in data.get("items") or []:
        bases = None
        if "bases" in item:
            rows = []
            for base in item.get("bases") or []:
                rows.append(
                    SnapshotBase(
                        name=str(base.get("name") or ""),
                        href=str(base.get("href") or ""),
                        required_level=base.get("required_level") if isinstance(base.get("required_level"), int) else None,
                    )
                )
            bases = tuple(rows)

        modifier_sections = None
        if "modifier_sections" in item or "affixes" in item:
            sections = []
            source_sections = dict(item.get("modifier_sections") or {})
            if "normal" not in source_sections and "affixes" in item:
                source_sections["normal"] = item.get("affixes") or []
            for name, affixes_raw in source_sections.items():
                affixes = []
                for affix in affixes_raw or []:
                    tiers = []
                    for tier in affix.get("tiers") or []:
                        tiers.append(
                            SnapshotTier(
                                level=tier.get("level") if isinstance(tier.get("level"), int) else None,
                                name=str(tier.get("name") or ""),
                                text=str(tier.get("text") or ""),
                                drop_chance=tier.get("drop_chance") if isinstance(tier.get("drop_chance"), int) else None,
                            )
                        )
                    affixes.append(
                        SnapshotAffix(
                            kind=str(affix.get("kind") or ""),
                            family_key=str(affix.get("family_key") or ""),
                            template=str(affix.get("template") or ""),
                            tiers=tuple(tiers),
                        )
                    )
                sections.append(
                    SnapshotModifierSection(
                        name=str(name),
                        affixes=tuple(affixes),
                    )
                )
            modifier_sections = tuple(sections)
        items.append(
            SnapshotItem(
                slug=str(item.get("slug") or ""),
                category=str(item.get("category") or ""),
                label=str(item.get("label") or ""),
                href=str(item.get("href") or ""),
                bases=bases,
                modifier_sections=modifier_sections,
            )
        )
    return SnapshotDocument(
        version=data.get("version") if isinstance(data.get("version"), int) else 1,
        source=str(data.get("source") or ""),
        fetched_at=str(data.get("fetched_at") or ""),
        items=tuple(items),
    )


def snapshot_to_dict(document: SnapshotDocument) -> dict[str, Any]:
    return {
        "version": document.version,
        "source": document.source,
        "fetched_at": document.fetched_at,
        "items": [
            {
                **{
                    "slug": item.slug,
                    "category": item.category,
                    "label": item.label,
                    "href": item.href,
                },
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
                    if item.bases is not None
                    else {}
                ),
                **(
                    {
                        "modifier_sections": {
                            section.name: [
                                {
                                    "kind": affix.kind,
                                    "family_key": affix.family_key,
                                    "template": affix.template,
                                    "tiers": [
                                        {
                                            "level": tier.level,
                                            "name": tier.name,
                                            "text": tier.text,
                                            "drop_chance": tier.drop_chance,
                                        }
                                        for tier in affix.tiers
                                    ],
                                }
                                for affix in section.affixes
                            ]
                            for section in item.modifier_sections
                        }
                    }
                    if item.modifier_sections is not None
                    else {}
                ),
            }
            for item in document.items
        ],
    }
