from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from poe_affix_builder.source import load_mod_entries


class SourceTests(unittest.TestCase):
    def test_load_mod_entries_keeps_composite_family_keys(self):
        with tempfile.TemporaryDirectory() as td:
            mods_path = Path(td) / "mods.json"
            mods_path.write_text(
                json.dumps(
                    {
                        "CompositeStat": {
                            "generation_type": "suffix",
                            "groups": ["Strength", "Intelligence"],
                            "required_level": 65,
                            "name": "of Amanamu",
                            "text": "+(9-15) to [Strength|Strength] and [Intelligence|Intelligence]",
                            "stats": [
                                {"id": "base_strength", "min": 9, "max": 15},
                                {"id": "base_intelligence", "min": 9, "max": 15},
                            ],
                            "domain": "item",
                            "spawn_weights": [{"tag": "amulet", "weight": 1000}],
                        }
                    }
                ),
                encoding="utf-8",
            )

            entries = load_mod_entries(mods_path)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].family_key, "Strength|Intelligence")


if __name__ == "__main__":
    unittest.main()
