from __future__ import annotations

from typing import Any, Mapping

from poe_affix_builder.domain.models import SnapshotAffix, SnapshotDocument, SnapshotItem, SnapshotTier


def snapshot_from_dict(data: Mapping[str, Any]) -> SnapshotDocument:
    items = []
    for item in data.get("items") or []:
        affixes = []
        for affix in item.get("affixes") or []:
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
        items.append(
            SnapshotItem(
                slug=str(item.get("slug") or ""),
                category=str(item.get("category") or ""),
                label=str(item.get("label") or ""),
                href=str(item.get("href") or ""),
                affixes=tuple(affixes),
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
                "slug": item.slug,
                "category": item.category,
                "label": item.label,
                "href": item.href,
                "affixes": [
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
                    for affix in item.affixes
                ],
            }
            for item in document.items
        ],
    }
