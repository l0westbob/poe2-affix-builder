from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArtifactSummaryTests(unittest.TestCase):
    def test_committed_artifact_headline_counts(self):
        result_dir = ROOT / "result" / "affixes"
        build_report = json.loads((ROOT / "result" / "build_report.json").read_text(encoding="utf-8"))
        rebuild_report = json.loads((ROOT / "result" / "rebuild_mapping_report.json").read_text(encoding="utf-8"))
        validation_report = json.loads((ROOT / "result" / "mapping_validation.json").read_text(encoding="utf-8"))

        self.assertEqual(len(list(result_dir.glob("*.json"))), 78)
        self.assertEqual(build_report["items_written"], 78)
        self.assertEqual(build_report["affixes_written"], 7058)
        self.assertEqual(build_report["tiers_written"], 18182)
        self.assertEqual(len(build_report["unresolved_tiers"]), 5457)
        self.assertEqual(len(build_report["mapping_warnings"]), 62)

        self.assertEqual(rebuild_report["items"], 78)
        self.assertEqual(rebuild_report["affixes"], 7058)
        self.assertEqual(rebuild_report["tiers"], 18182)
        self.assertEqual(len(rebuild_report["unresolved_mod_matches"]), 5457)

        self.assertEqual(validation_report["items"], 78)
        self.assertEqual(validation_report["items_with_warnings"], 62)


if __name__ == "__main__":
    unittest.main()
