from __future__ import annotations

from typing import Any, Mapping

from poe_affix_builder.domain.models import (
    BuildReport,
    MappingValidationReport,
    RebuildReport,
    RefreshReport,
    UnresolvedTier,
)


def build_report_from_dict(data: Mapping[str, Any]) -> BuildReport:
    unresolved = []
    for row in data.get("unresolved_tiers") or []:
        unresolved.append(
            UnresolvedTier(
                slug=str(row.get("slug") or ""),
                family_key=str(row.get("family_key") or ""),
                kind=str(row.get("kind") or ""),
                level=row.get("level") if isinstance(row.get("level"), int) else None,
                name=row.get("name") if isinstance(row.get("name"), str) else None,
                text=row.get("text") if isinstance(row.get("text"), str) else None,
            )
        )
    return BuildReport(
        items_written=int(data.get("items_written") or 0),
        affixes_written=int(data.get("affixes_written") or 0),
        tiers_written=int(data.get("tiers_written") or 0),
        unresolved_tiers=tuple(unresolved),
        mapping_warnings={str(k): list(v) for k, v in (data.get("mapping_warnings") or {}).items()},
    )


def build_report_to_dict(report: BuildReport) -> dict[str, Any]:
    return {
        "items_written": report.items_written,
        "affixes_written": report.affixes_written,
        "tiers_written": report.tiers_written,
        "unresolved_tiers": [u.__dict__ for u in report.unresolved_tiers],
        "mapping_warnings": report.mapping_warnings,
    }


def rebuild_report_from_dict(data: Mapping[str, Any]) -> RebuildReport:
    return RebuildReport(
        ok=bool(data.get("ok")),
        items=int(data.get("items") or 0),
        affixes=int(data.get("affixes") or 0),
        tiers=int(data.get("tiers") or 0),
        unresolved_mod_matches=tuple(dict(v) for v in (data.get("unresolved_mod_matches") or [])),
    )


def rebuild_report_to_dict(report: RebuildReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "items": report.items,
        "affixes": report.affixes,
        "tiers": report.tiers,
        "unresolved_mod_matches": [dict(row) for row in report.unresolved_mod_matches],
    }


def validation_report_from_dict(data: Mapping[str, Any]) -> MappingValidationReport:
    return MappingValidationReport(
        items=int(data.get("items") or 0),
        items_with_warnings=int(data.get("items_with_warnings") or 0),
        warnings={str(k): list(v) for k, v in (data.get("warnings") or {}).items()},
    )


def validation_report_to_dict(report: MappingValidationReport) -> dict[str, Any]:
    return {
        "items": report.items,
        "items_with_warnings": report.items_with_warnings,
        "warnings": report.warnings,
    }


def refresh_report_from_dict(data: Mapping[str, Any]) -> RefreshReport:
    return RefreshReport(
        ok=bool(data.get("ok")),
        source=str(data.get("source") or ""),
        started_at_utc=str(data.get("started_at_utc") or ""),
        finished_at_utc=str(data.get("finished_at_utc") or ""),
        duration_seconds=float(data.get("duration_seconds") or 0.0),
        items_fetched=int(data.get("items_fetched") or 0),
        affixes_fetched=int(data.get("affixes_fetched") or 0),
        tiers_fetched=int(data.get("tiers_fetched") or 0),
        snapshot_sha256=str(data.get("snapshot_sha256") or ""),
        snapshot_path=str(data.get("snapshot_path") or ""),
    )


def refresh_report_to_dict(report: RefreshReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "source": report.source,
        "started_at_utc": report.started_at_utc,
        "finished_at_utc": report.finished_at_utc,
        "duration_seconds": report.duration_seconds,
        "items_fetched": report.items_fetched,
        "affixes_fetched": report.affixes_fetched,
        "tiers_fetched": report.tiers_fetched,
        "snapshot_sha256": report.snapshot_sha256,
        "snapshot_path": report.snapshot_path,
    }
