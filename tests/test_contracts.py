from __future__ import annotations

import json
import unittest
from pathlib import Path

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
    def test_manifest_round_trip_matches_semantics(self):
        raw = json.loads((ROOT / "config" / "item_mapping.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest_to_dict(manifest_from_dict(raw)), raw)

    def test_snapshot_round_trip_matches_semantics(self):
        raw = json.loads((ROOT / "config" / "poe2db_snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot_to_dict(snapshot_from_dict(raw)), raw)

    def test_output_round_trip_matches_semantics(self):
        raw = json.loads((ROOT / "result" / "affixes" / "Amulets.json").read_text(encoding="utf-8"))
        self.assertEqual(output_item_to_dict(output_item_from_dict(raw)), raw)

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
