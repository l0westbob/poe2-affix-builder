from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from poe_affix_builder.builder import build_affixes, validate_mapping


ROOT = Path(__file__).resolve().parents[1]
MODS_PATH = ROOT / "data" / "poe2" / "data" / "mods.json"
MANIFEST_PATH = ROOT / "config" / "item_mapping.json"
RESULT_DIR = ROOT / "result" / "affixes"
HAS_REAL_DATASET = MODS_PATH.exists() and RESULT_DIR.exists()


def _iter_json_files(path: Path):
    return sorted([p for p in path.glob("*.json") if p.is_file()])


class BuilderTests(unittest.TestCase):
    @unittest.skipUnless(HAS_REAL_DATASET, "Requires local PoE2 source checkout under data/poe2")
    def test_build_schema_and_counts(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "out"
            report = Path(td) / "report.json"
            result = build_affixes(
                mods_json_path=MODS_PATH,
                manifest_path=MANIFEST_PATH,
                out_dir=out_dir,
                report_path=report,
            )

            files = _iter_json_files(out_dir)
            self.assertEqual(result.items_written, 78)
            self.assertEqual(len(files), 78)
            self.assertEqual(result.affixes_written, 7058)
            self.assertEqual(result.tiers_written, 18182)
            self.assertTrue(report.exists())

            sample = json.loads((out_dir / "Amulets.json").read_text(encoding="utf-8"))
            self.assertEqual(set(sample.keys()), {"slug", "category", "label", "bases", "modifier_sections"})
            self.assertNotIn("affixes", sample)
            affix = sample["modifier_sections"]["normal"][0]
            self.assertEqual(set(affix.keys()), {"family_key", "kind", "template", "tiers"})
            tier = affix["tiers"][0]
            self.assertIn("level", tier)
            self.assertIn("name", tier)
            self.assertIn("text", tier)
            self.assertIn("normal", sample["modifier_sections"])

    @unittest.skipUnless(HAS_REAL_DATASET, "Requires local PoE2 source checkout under data/poe2")
    def test_deterministic_output(self):
        with tempfile.TemporaryDirectory() as td:
            out_a = Path(td) / "a"
            out_b = Path(td) / "b"
            rep_a = Path(td) / "a.json"
            rep_b = Path(td) / "b.json"

            build_affixes(
                mods_json_path=MODS_PATH,
                manifest_path=MANIFEST_PATH,
                out_dir=out_a,
                report_path=rep_a,
            )
            build_affixes(
                mods_json_path=MODS_PATH,
                manifest_path=MANIFEST_PATH,
                out_dir=out_b,
                report_path=rep_b,
            )

            files_a = {p.name: p.read_bytes() for p in _iter_json_files(out_a)}
            files_b = {p.name: p.read_bytes() for p in _iter_json_files(out_b)}
            self.assertEqual(files_a.keys(), files_b.keys())
            for name in files_a:
                self.assertEqual(files_a[name], files_b[name], msg=f"Mismatch for {name}")

    @unittest.skipUnless(HAS_REAL_DATASET, "Requires local PoE2 source checkout under data/poe2")
    def test_golden_parity_exact(self):
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "out"
            report = Path(td) / "report.json"
            build_affixes(
                mods_json_path=MODS_PATH,
                manifest_path=MANIFEST_PATH,
                out_dir=out_dir,
                report_path=report,
            )

            result_files = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in _iter_json_files(RESULT_DIR)}
            built_files = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in _iter_json_files(out_dir)}

            self.assertEqual(result_files.keys(), built_files.keys())

            diffs = set()
            for name in result_files:
                if result_files[name] != built_files[name]:
                    diffs.add(name)

            self.assertEqual(diffs, set())

    @unittest.skipUnless(HAS_REAL_DATASET, "Requires local PoE2 source checkout under data/poe2")
    def test_build_report_golden_parity_exact(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "report.json"
            build_affixes(
                mods_json_path=MODS_PATH,
                manifest_path=MANIFEST_PATH,
                out_dir=Path(td) / "out",
                report_path=report,
            )

            expected = json.loads((ROOT / "result" / "build_report.json").read_text(encoding="utf-8"))
            actual = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(actual, expected)

    @unittest.skipUnless(HAS_REAL_DATASET, "Requires local PoE2 source checkout under data/poe2")
    def test_validate_mapping_golden_parity_exact(self):
        expected = json.loads((ROOT / "result" / "mapping_validation.json").read_text(encoding="utf-8"))
        actual = validate_mapping(mods_json_path=MODS_PATH, manifest_path=MANIFEST_PATH)
        self.assertEqual(actual, expected)

    def test_unmatched_tier_keeps_placeholder(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            mods = {
                "TestMod1": {
                    "generation_type": "prefix",
                    "groups": ["TestFamily"],
                    "required_level": 1,
                    "name": "Alpha",
                    "text": "+(1-3) to Life",
                    "stats": [{"id": "base_maximum_life", "min": 1, "max": 3}],
                    "domain": "item",
                    "spawn_weights": [{"tag": "amulet", "weight": 1000}],
                }
            }
            manifest = {
                "version": 1,
                "items": [
                    {
                        "slug": "TestItem",
                        "category": "Jewellery",
                        "label": "Test",
                        "include_domains": ["item"],
                        "include_spawn_tags": ["amulet"],
                        "affixes": [
                            {
                                "kind": "prefix",
                                "family_key": "TestFamily",
                                "template": "+# to Life",
                                "tiers": [
                                    {"level": 2, "name": "Missing", "text": "legacy text", "stats": []}
                                ],
                            }
                        ],
                    }
                ],
            }

            mods_path = td_path / "mods.json"
            manifest_path = td_path / "manifest.json"
            out_dir = td_path / "out"
            report = td_path / "report.json"
            mods_path.write_text(json.dumps(mods), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            build_affixes(
                mods_json_path=mods_path,
                manifest_path=manifest_path,
                out_dir=out_dir,
                report_path=report,
            )

            output = json.loads((out_dir / "TestItem.json").read_text(encoding="utf-8"))
            self.assertNotIn("affixes", output)
            tier = output["modifier_sections"]["normal"][0]["tiers"][0]
            self.assertEqual(tier["text"], "legacy text")
            self.assertNotIn("stats", tier)

    def test_build_preserves_bases_and_modifier_sections(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            mods = {
                "TestMod1": {
                    "generation_type": "prefix",
                    "groups": ["TestFamily"],
                    "required_level": 1,
                    "name": "Alpha",
                    "text": "+(1-3) to Life",
                    "stats": [{"id": "base_maximum_life", "min": 1, "max": 3}],
                    "domain": "item",
                    "spawn_weights": [{"tag": "amulet", "weight": 1000}],
                }
            }
            manifest = {
                "version": 1,
                "items": [
                    {
                        "slug": "TestItem",
                        "category": "Jewellery",
                        "label": "Test",
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
                                    "family_key": "TestFamily",
                                    "template": "+# to Life",
                                    "tiers": [
                                        {"level": 1, "name": "Alpha", "text": "+(1-3) to Life", "stats": ["base_maximum_life"]}
                                    ],
                                }
                            ],
                            "corrupted": [
                                {
                                    "kind": "suffix",
                                    "family_key": "TestFamily",
                                    "template": "+# to Life",
                                    "tiers": [
                                        {"level": 1, "name": "Alpha", "text": "+(1-3) to Life", "stats": ["base_maximum_life"]}
                                    ],
                                }
                            ],
                        },
                        "affixes": [
                            {
                                "kind": "prefix",
                                "family_key": "TestFamily",
                                "template": "+# to Life",
                                "tiers": [
                                    {"level": 1, "name": "Alpha", "text": "+(1-3) to Life", "stats": ["base_maximum_life"]}
                                ],
                            }
                        ],
                    }
                ],
            }

            mods_path = td_path / "mods.json"
            manifest_path = td_path / "manifest.json"
            out_dir = td_path / "out"
            report = td_path / "report.json"
            mods_path.write_text(json.dumps(mods), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            build_affixes(
                mods_json_path=mods_path,
                manifest_path=manifest_path,
                out_dir=out_dir,
                report_path=report,
            )

            output = json.loads((out_dir / "TestItem.json").read_text(encoding="utf-8"))
            self.assertEqual(output["bases"][0]["name"], "Lapis Amulet")
            self.assertIn("modifier_sections", output)
            self.assertIn("normal", output["modifier_sections"])
            self.assertIn("corrupted", output["modifier_sections"])
            self.assertEqual(output["modifier_sections"]["corrupted"][0]["tiers"][0]["stats"][0]["id"], "base_maximum_life")
            self.assertNotIn("affixes", output)


if __name__ == "__main__":
    unittest.main()
