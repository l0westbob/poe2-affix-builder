from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from poe_affix_builder.adapters.json_store import load_json
from poe_affix_builder.contracts.manifest_contracts import validate_manifest_dict
from poe_affix_builder.policies.item_rules import domain_for_category, spawn_tags_for_slug


def load_manifest(path: Path) -> Dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a JSON object")
    validate_manifest_dict(data)
    return dict(data)


__all__ = ["domain_for_category", "load_manifest", "spawn_tags_for_slug"]
