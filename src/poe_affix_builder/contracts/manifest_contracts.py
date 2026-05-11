from __future__ import annotations

from typing import Any, Mapping

from poe_affix_builder.domain.models import (
    ManifestAffix,
    ManifestBase,
    ManifestDocument,
    ManifestItem,
    ManifestModifierSection,
    ManifestTier,
)

MANIFEST_CONTRACT_VERSION = 1


def validate_manifest_dict(data: Mapping[str, Any]) -> None:
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("Manifest must contain an 'items' array")

    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError("Each manifest item must be an object")
        for key in ("slug", "category", "label", "affixes"):
            if key not in item:
                raise ValueError(f"Manifest item missing required key: {key}")


def _manifest_affixes_from_rows(rows: list[Any] | tuple[Any, ...]) -> tuple[ManifestAffix, ...]:
    affixes = []
    for affix in rows or []:
        tiers = []
        for tier in affix.get("tiers") or []:
            stats = []
            for stat in tier.get("stats") or []:
                if isinstance(stat, str) and stat:
                    stats.append(stat)
                elif isinstance(stat, Mapping) and isinstance(stat.get("id"), str) and stat["id"]:
                    stats.append(stat["id"])
            tiers.append(
                ManifestTier(
                    level=tier.get("level") if isinstance(tier.get("level"), int) else None,
                    name=str(tier.get("name") or ""),
                    text=str(tier.get("text") or ""),
                    stats=tuple(stats),
                )
            )
        affixes.append(
            ManifestAffix(
                kind=str(affix.get("kind") or ""),
                family_key=str(affix.get("family_key") or ""),
                template=str(affix.get("template") or ""),
                tiers=tuple(tiers),
            )
        )
    return tuple(affixes)


def manifest_from_dict(data: Mapping[str, Any]) -> ManifestDocument:
    validate_manifest_dict(data)
    items = []
    for item in data.get("items") or []:
        affixes = _manifest_affixes_from_rows(item.get("affixes") or [])
        bases = []
        for base in item.get("bases") or []:
            bases.append(
                ManifestBase(
                    name=str(base.get("name") or ""),
                    href=str(base.get("href") or ""),
                    required_level=base.get("required_level") if isinstance(base.get("required_level"), int) else None,
                )
            )
        modifier_sections = []
        for name, rows in (item.get("modifier_sections") or {}).items():
            modifier_sections.append(
                ManifestModifierSection(
                    name=str(name),
                    affixes=_manifest_affixes_from_rows(rows if isinstance(rows, (list, tuple)) else []),
                )
            )
        items.append(
            ManifestItem(
                slug=str(item.get("slug") or ""),
                category=str(item.get("category") or ""),
                label=str(item.get("label") or ""),
                include_domains=tuple(str(v) for v in (item.get("include_domains") or [])),
                include_spawn_tags=tuple(str(v) for v in (item.get("include_spawn_tags") or [])),
                bases=tuple(bases),
                modifier_sections=tuple(modifier_sections),
                affixes=affixes,
            )
        )
    version = data.get("version")
    return ManifestDocument(version=version if isinstance(version, int) else 1, items=tuple(items))


def manifest_to_dict(document: ManifestDocument) -> dict[str, Any]:
    return {
        "version": document.version,
        "items": [
            {
                "slug": item.slug,
                "category": item.category,
                "label": item.label,
                "include_domains": list(item.include_domains),
                "include_spawn_tags": list(item.include_spawn_tags),
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
                                    "kind": affix.kind,
                                    "family_key": affix.family_key,
                                    "template": affix.template,
                                    "tiers": [
                                        {
                                            "level": tier.level,
                                            "name": tier.name,
                                            "text": tier.text,
                                            "stats": list(tier.stats),
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
                                "stats": list(tier.stats),
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
