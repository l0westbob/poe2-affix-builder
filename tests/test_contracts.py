from __future__ import annotations

import json
import unittest
from pathlib import Path

from poe_affix_builder.contracts import (
    MANIFEST_CONTRACT_VERSION,
    OUTPUT_CONTRACT_VERSION,
    REPORT_CONTRACT_VERSION,
    SNAPSHOT_CONTRACT_VERSION,
)
from poe_affix_builder.contracts.manifest_contracts import manifest_from_dict, manifest_to_dict
from poe_affix_builder.contracts.output_contracts import output_item_from_dict, output_item_to_dict
from poe_affix_builder.contracts.report_contracts import (
    build_report_from_dict,
    build_report_to_dict,
    rebuild_report_from_dict,
    rebuild_report_to_dict,
    refresh_report_from_dict,
    refresh_report_to_dict,
    validation_report_from_dict,
    validation_report_to_dict,
)
from poe_affix_builder.contracts.snapshot_contracts import snapshot_from_dict, snapshot_to_dict


ROOT = Path(__file__).resolve().parents[1]


class ContractRoundTripTests(unittest.TestCase):
    def test_contract_versions_are_explicit(self):
        self.assertEqual(SNAPSHOT_CONTRACT_VERSION, 1)
        self.assertEqual(MANIFEST_CONTRACT_VERSION, 1)
        self.assertEqual(OUTPUT_CONTRACT_VERSION, 1)
        self.assertEqual(REPORT_CONTRACT_VERSION, 1)

    def test_manifest_round_trip_matches_semantics(self):
        raw = json.loads((ROOT / "config" / "item_mapping.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest_to_dict(manifest_from_dict(raw)), raw)

    def test_snapshot_round_trip_matches_semantics(self):
        raw = json.loads((ROOT / "config" / "poe2db_snapshot.json").read_text(encoding="utf-8"))
        normalized = snapshot_to_dict(snapshot_from_dict(raw))
        self.assertIn("modifier_sections", normalized["items"][0])
        self.assertIn("normal", normalized["items"][0]["modifier_sections"])
        self.assertNotIn("affixes", normalized["items"][0])
        if "affixes" in raw["items"][0]:
            self.assertEqual(normalized["items"][0]["modifier_sections"]["normal"], raw["items"][0]["affixes"])
        else:
            self.assertEqual(normalized, raw)

    def test_output_round_trip_matches_semantics(self):
        raw = json.loads((ROOT / "result" / "affixes" / "Amulets.json").read_text(encoding="utf-8"))
        self.assertEqual(output_item_to_dict(output_item_from_dict(raw)), raw)

    def test_manifest_round_trip_supports_bases_and_modifier_sections(self):
        raw = {
            "version": 1,
            "items": [
                {
                    "slug": "Amulets",
                    "category": "Jewellery",
                    "label": "Amulets",
                    "include_domains": ["item"],
                    "include_spawn_tags": ["amulet"],
                    "bases": [
                        {
                            "name": "Lapis Amulet",
                            "href": "/us/Lapis_Amulet",
                            "required_level": 12,
                        }
                    ],
                    "modifier_sections": {
                        "normal": [
                            {
                                "kind": "prefix",
                                "family_key": "Life",
                                "template": "+# to maximum Life",
                                "tiers": [
                                    {
                                        "level": 1,
                                        "name": "Healthy",
                                        "text": "+(1-2) to maximum Life",
                                        "stats": ["base_maximum_life"],
                                    }
                                ],
                            }
                        ]
                    },
                    "affixes": [
                        {
                            "kind": "prefix",
                            "family_key": "Life",
                            "template": "+# to maximum Life",
                            "tiers": [
                                {
                                    "level": 1,
                                    "name": "Healthy",
                                    "text": "+(1-2) to maximum Life",
                                    "stats": ["base_maximum_life"],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        self.assertEqual(manifest_to_dict(manifest_from_dict(raw)), raw)

    def test_output_round_trip_supports_bases_and_modifier_sections(self):
        raw = {
            "slug": "Amulets",
            "category": "Jewellery",
            "label": "Amulets",
            "bases": [
                {
                    "name": "Lapis Amulet",
                    "href": "/us/Lapis_Amulet",
                    "required_level": 12,
                }
            ],
            "modifier_sections": {
                "normal": [
                    {
                        "family_key": "Life",
                        "kind": "prefix",
                        "template": "+# to maximum Life",
                        "tiers": [
                            {
                                "level": 1,
                                "name": "Healthy",
                                "text": "+(1-2) to maximum Life",
                                "stats": [{"id": "base_maximum_life", "min": 1, "max": 2}],
                            }
                        ],
                    }
                ]
            },
        }
        self.assertEqual(output_item_to_dict(output_item_from_dict(raw)), raw)

    def test_output_legacy_affixes_input_normalizes_to_modifier_sections(self):
        raw = {
            "slug": "Amulets",
            "category": "Jewellery",
            "label": "Amulets",
            "affixes": [
                {
                    "family_key": "Life",
                    "kind": "prefix",
                    "template": "+# to maximum Life",
                    "tiers": [{"level": 1, "name": "Healthy", "text": "+(1-2) to maximum Life"}],
                }
            ],
        }

        normalized = output_item_to_dict(output_item_from_dict(raw))

        self.assertNotIn("affixes", normalized)
        self.assertEqual(normalized["modifier_sections"]["normal"], raw["affixes"])

    def test_snapshot_legacy_affixes_input_normalizes_to_modifier_sections(self):
        raw = {
            "version": 1,
            "source": "fixture",
            "fetched_at": "2026-05-11T00:00:00+00:00",
            "items": [
                {
                    "slug": "Amulets",
                    "category": "Jewellery",
                    "label": "Amulets",
                    "href": "https://poe2db.tw/us/Amulets",
                    "affixes": [
                        {
                            "kind": "prefix",
                            "family_key": "Life",
                            "template": "+# to maximum Life",
                            "tiers": [
                                {
                                    "level": 1,
                                    "name": "Healthy",
                                    "text": "+(1-2) to maximum Life",
                                    "drop_chance": 100,
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        normalized = snapshot_to_dict(snapshot_from_dict(raw))

        self.assertNotIn("affixes", normalized["items"][0])
        self.assertEqual(normalized["items"][0]["modifier_sections"]["normal"], raw["items"][0]["affixes"])

    def test_report_round_trip_matches_semantics(self):
        build_raw = json.loads((ROOT / "result" / "build_report.json").read_text(encoding="utf-8"))
        rebuild_raw = json.loads((ROOT / "result" / "rebuild_mapping_report.json").read_text(encoding="utf-8"))
        validate_raw = json.loads((ROOT / "result" / "mapping_validation.json").read_text(encoding="utf-8"))
        refresh_raw = json.loads((ROOT / "result" / "poe2db_refresh_report.json").read_text(encoding="utf-8"))

        self.assertEqual(build_report_to_dict(build_report_from_dict(build_raw)), build_raw)
        self.assertEqual(rebuild_report_to_dict(rebuild_report_from_dict(rebuild_raw)), rebuild_raw)
        self.assertEqual(validation_report_to_dict(validation_report_from_dict(validate_raw)), validate_raw)
        self.assertEqual(refresh_report_to_dict(refresh_report_from_dict(refresh_raw)), refresh_raw)


if __name__ == "__main__":
    unittest.main()
