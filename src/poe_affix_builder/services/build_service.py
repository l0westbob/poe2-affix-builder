from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from poe_affix_builder.adapters.json_store import write_json_atomic
from poe_affix_builder.contracts.manifest_contracts import manifest_from_dict
from poe_affix_builder.contracts.output_contracts import output_item_to_dict
from poe_affix_builder.contracts.report_contracts import build_report_to_dict, validation_report_to_dict
from poe_affix_builder.domain.models import (
    BuildReport,
    BuildResult,
    MappingValidationReport,
    OutputAffix,
    OutputBase,
    OutputItem,
    OutputModifierSection,
    OutputTier,
    UnresolvedTier,
)
from poe_affix_builder.manifest import load_manifest
from poe_affix_builder.normalize import normalize_output_text, text_to_template
from poe_affix_builder.services.matching_service import (
    build_family_index,
    build_indexes,
    candidate_families_for_item,
    collect_build_candidates,
    copy_stats,
    extract_ref_stat_ids,
    family_warning_detail,
    select_build_candidate,
)
from poe_affix_builder.source import load_mod_entries


def _build_output_affixes(
    *,
    item,
    affixes,
    include_domains: set[str],
    include_spawn_tags: set[str],
    indexes,
    unresolved: list[UnresolvedTier],
) -> tuple[OutputAffix, ...]:
    out_affixes: list[OutputAffix] = []
    for affix in affixes:
        out_tiers: list[OutputTier] = []
        first_matched_text: str | None = None

        for tier in affix.tiers:
            candidates_here = collect_build_candidates(
                indexes,
                kind=affix.kind,
                family_key=affix.family_key,
                level=tier.level,
                name=tier.name,
                text_ref=tier.text,
            )
            decision = select_build_candidate(
                candidates_here,
                include_domains=include_domains,
                include_spawn_tags=include_spawn_tags,
                ref_text=tier.text,
                ref_name=tier.name or None,
                ref_stat_ids=extract_ref_stat_ids(
                    {
                        "stats": list(tier.stats),
                    }
                ),
            )
            text_out = normalize_output_text(tier.text) if isinstance(tier.text, str) else tier.text
            stats = ()
            if decision.entry is not None:
                text_out = decision.entry.text
                copied = copy_stats(decision.entry.stats)
                stats = tuple(copied)
                if first_matched_text is None:
                    first_matched_text = decision.entry.text
            else:
                unresolved.append(
                    UnresolvedTier(
                        slug=item.slug,
                        family_key=affix.family_key,
                        kind=affix.kind,
                        level=tier.level,
                        name=tier.name or None,
                        text=tier.text or None,
                    )
                )
            out_tiers.append(OutputTier(level=tier.level, name=tier.name, text=text_out, stats=stats))

        out_affixes.append(
            OutputAffix(
                family_key=affix.family_key,
                kind=affix.kind,
                template=text_to_template(first_matched_text) if first_matched_text else affix.template,
                tiers=tuple(out_tiers),
            )
        )
    return tuple(out_affixes)


def build_affixes(
    *,
    mods_json_path: Path,
    manifest_path: Path,
    out_dir: Path,
    report_path: Path,
) -> BuildResult:
    manifest = manifest_from_dict(load_manifest(manifest_path))
    entries = load_mod_entries(mods_json_path)
    indexes = build_indexes(entries)
    family_index = build_family_index(entries)

    out_dir.mkdir(parents=True, exist_ok=True)
    unresolved: list[UnresolvedTier] = []
    mapping_warnings: Dict[str, list[dict[str, Any]]] = {}
    items_written = 0
    affixes_written = 0
    tiers_written = 0

    for item in manifest.items:
        include_domains = set(item.include_domains)
        include_spawn_tags = set(item.include_spawn_tags)
        known_families = {(affix.kind, affix.family_key) for affix in item.affixes}
        candidates = candidate_families_for_item(entries, include_domains, include_spawn_tags)
        unknown = sorted(candidates - known_families)
        if unknown:
            mapping_warnings[item.slug] = [
                family_warning_detail(
                    key=(kind, family_key),
                    include_domains=include_domains,
                    include_spawn_tags=include_spawn_tags,
                    family_index=family_index,
                )
                for kind, family_key in unknown[:50]
            ]

        out_modifier_sections: list[OutputModifierSection] = []
        for section in item.modifier_sections:
            built_affixes = _build_output_affixes(
                item=item,
                affixes=section.affixes,
                include_domains=include_domains,
                include_spawn_tags=include_spawn_tags,
                indexes=indexes,
                unresolved=unresolved,
            )
            out_modifier_sections.append(OutputModifierSection(name=section.name, affixes=built_affixes))
            affixes_written += len(built_affixes)
            tiers_written += sum(len(affix.tiers) for affix in built_affixes)

        out_affixes = next((section.affixes for section in out_modifier_sections if section.name == "normal"), tuple())
        if not out_modifier_sections and item.affixes:
            out_affixes = _build_output_affixes(
                item=item,
                affixes=item.affixes,
                include_domains=include_domains,
                include_spawn_tags=include_spawn_tags,
                indexes=indexes,
                unresolved=unresolved,
            )
            out_modifier_sections = [OutputModifierSection(name="normal", affixes=out_affixes)]
            affixes_written += len(out_affixes)
            tiers_written += sum(len(affix.tiers) for affix in out_affixes)

        out_item = OutputItem(
            slug=item.slug,
            category=item.category,
            label=item.label,
            bases=tuple(
                OutputBase(
                    name=base.name,
                    href=base.href,
                    required_level=base.required_level,
                )
                for base in item.bases
            ),
            modifier_sections=tuple(out_modifier_sections),
            affixes=tuple(out_affixes),
        )
        write_json_atomic(out_dir / f"{item.slug}.json", output_item_to_dict(out_item))
        items_written += 1

    report = BuildReport(
        items_written=items_written,
        affixes_written=affixes_written,
        tiers_written=tiers_written,
        unresolved_tiers=tuple(unresolved),
        mapping_warnings=mapping_warnings,
    )
    write_json_atomic(report_path, build_report_to_dict(report))
    return BuildResult(
        items_written=report.items_written,
        affixes_written=report.affixes_written,
        tiers_written=report.tiers_written,
        unresolved_tiers=report.unresolved_tiers,
        mapping_warnings=report.mapping_warnings,
    )


def validate_mapping(*, mods_json_path: Path, manifest_path: Path) -> Dict[str, Any]:
    manifest = manifest_from_dict(load_manifest(manifest_path))
    entries = load_mod_entries(mods_json_path)
    family_index = build_family_index(entries)

    warnings: Dict[str, list[dict[str, Any]]] = {}
    for item in manifest.items:
        include_domains = set(item.include_domains)
        include_spawn_tags = set(item.include_spawn_tags)
        known_families = {(affix.kind, affix.family_key) for affix in item.affixes}
        candidates = candidate_families_for_item(entries, include_domains, include_spawn_tags)
        unknown = sorted(candidates - known_families)
        if unknown:
            warnings[item.slug] = [
                family_warning_detail(
                    key=(kind, family_key),
                    include_domains=include_domains,
                    include_spawn_tags=include_spawn_tags,
                    family_index=family_index,
                )
                for kind, family_key in unknown
            ]

    return validation_report_to_dict(
        MappingValidationReport(
            items=len(manifest.items),
            items_with_warnings=len(warnings),
            warnings=warnings,
        )
    )
