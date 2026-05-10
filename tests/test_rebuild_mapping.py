from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from poe_affix_builder.poe2db_snapshot import refresh_snapshot
from poe_affix_builder.rebuild_mapping import rebuild_mapping

ROOT = Path(__file__).resolve().parents[1]
MODS_PATH = ROOT / "data" / "poe2" / "data" / "mods.json"
SNAPSHOT_PATH = ROOT / "config" / "poe2db_snapshot.json"
HAS_REAL_DATASET = MODS_PATH.exists() and SNAPSHOT_PATH.exists()


class RebuildMappingTests(unittest.TestCase):
    def test_refresh_snapshot_atomic_failure_keeps_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshot_path = root / "snapshot.json"
            report_path = root / "report.json"
            snapshot_path.write_text(json.dumps({"old": True}), encoding="utf-8")

            index_html = """
            <div class=\"card\">
              <h5 class=\"card-header\">Modifiers</h5>
              <div class=\"card-body\">
                <div class=\"itemList\"><a href=\"/us/Modifiers\">Ignore</a></div>
                <div class=\"itemList\">
                  <span class=\"disabled\">Weapons</span>
                  <a href=\"/us/Bows\">Bows</a>
                  <a href=\"/us/Wands\">Wands</a>
                </div>
              </div>
            </div>
            """
            bows_html = """
            <html><body>
            <script>
            new ModsView({
              normal: [
                {
                  ModGenerationTypeID: 1,
                  ModFamilyList: ["BowDamage"],
                  Name: "Sharp",
                  Level: 1,
                  DropChance: 100,
                  str: "<span>+(1-2) to Physical Damage</span>"
                }
              ]
            });
            </script>
            </body></html>
            """

            def fetcher(url: str) -> str:
                if url.endswith("/Modifiers"):
                    return index_html
                if url.endswith("/Bows"):
                    return bows_html
                if url.endswith("/Wands"):
                    raise RuntimeError("simulated fetch failure")
                raise RuntimeError(f"unexpected url: {url}")

            with self.assertRaises(RuntimeError):
                refresh_snapshot(
                    snapshot_path=snapshot_path,
                    report_path=report_path,
                    index_url="https://poe2db.tw/us/Modifiers",
                    fetcher=fetcher,
                )

            after = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(after, {"old": True})
            self.assertFalse(report_path.exists())

    def test_rebuild_mapping_from_snapshot_and_mods(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mods_path = root / "mods.json"
            snapshot_path = root / "snapshot.json"
            out_path = root / "mapping.json"
            report_path = root / "report.json"

            mods = {
                "LifePrefix1": {
                    "generation_type": "prefix",
                    "groups": ["Life"],
                    "required_level": 1,
                    "name": "Healthy",
                    "text": "+(1-2) to maximum Life",
                    "stats": [{"id": "base_maximum_life", "min": 1, "max": 2}],
                    "domain": "item",
                    "spawn_weights": [{"tag": "amulet", "weight": 1000}],
                }
            }
            snapshot = {
                "version": 1,
                "items": [
                    {
                        "slug": "Amulets",
                        "category": "Jewellery",
                        "label": "Amulets",
                        "affixes": [
                            {
                                "kind": "prefix",
                                "family_key": "Life",
                                "template": "+# to maximum Life",
                                "tiers": [{"level": 1, "name": "Healthy", "text": "+(1-2) to maximum Life"}],
                            }
                        ],
                    }
                ],
            }

            mods_path.write_text(json.dumps(mods), encoding="utf-8")
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

            rebuild_mapping(
                mods_json_path=mods_path,
                snapshot_path=snapshot_path,
                out_path=out_path,
                report_path=report_path,
            )

            mapping = json.loads(out_path.read_text(encoding="utf-8"))
            item = mapping["items"][0]
            tier = item["affixes"][0]["tiers"][0]

            self.assertEqual(item["slug"], "Amulets")
            self.assertEqual(item["include_domains"], ["item"])
            self.assertEqual(item["include_spawn_tags"], ["amulet"])
            self.assertEqual(tier["stats"], ["base_maximum_life"])

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["ok"])
            self.assertEqual(report["unresolved_mod_matches"], [])

    def test_rebuild_mapping_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mods_path = root / "mods.json"
            snapshot_path = root / "snapshot.json"
            out_path = root / "mapping.json"
            report_path = root / "report.json"

            mods = {
                "LifePrefix1": {
                    "generation_type": "prefix",
                    "groups": ["Life"],
                    "required_level": 1,
                    "name": "Healthy",
                    "text": "+(1-2) to maximum Life",
                    "stats": [{"id": "base_maximum_life", "min": 1, "max": 2}],
                    "domain": "item",
                    "spawn_weights": [{"tag": "amulet", "weight": 1000}],
                }
            }
            snapshot = {
                "version": 1,
                "items": [
                    {
                        "slug": "Amulets",
                        "category": "Jewellery",
                        "label": "Amulets",
                        "affixes": [
                            {
                                "kind": "prefix",
                                "family_key": "Life",
                                "template": "+# to maximum Life",
                                "tiers": [{"level": 1, "name": "Healthy", "text": "+(1-2) to maximum Life"}],
                            }
                        ],
                    }
                ],
            }

            mods_path.write_text(json.dumps(mods), encoding="utf-8")
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

            rebuild_mapping(
                mods_json_path=mods_path,
                snapshot_path=snapshot_path,
                out_path=out_path,
                report_path=report_path,
            )
            first = out_path.read_bytes()

            rebuild_mapping(
                mods_json_path=mods_path,
                snapshot_path=snapshot_path,
                out_path=out_path,
                report_path=report_path,
            )
            second = out_path.read_bytes()

            self.assertEqual(first, second)

    @unittest.skipUnless(HAS_REAL_DATASET, "Requires local PoE2 source checkout under data/poe2")
    def test_rebuild_mapping_golden_parity_exact(self):
        with tempfile.TemporaryDirectory() as td:
            out_path = Path(td) / "mapping.json"
            report_path = Path(td) / "report.json"

            rebuild_mapping(
                mods_json_path=MODS_PATH,
                snapshot_path=SNAPSHOT_PATH,
                out_path=out_path,
                report_path=report_path,
            )

            expected_mapping = json.loads((ROOT / "config" / "item_mapping.json").read_text(encoding="utf-8"))
            actual_mapping = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(actual_mapping, expected_mapping)

            expected_report = json.loads((ROOT / "result" / "rebuild_mapping_report.json").read_text(encoding="utf-8"))
            actual_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(actual_report, expected_report)


if __name__ == "__main__":
    unittest.main()
