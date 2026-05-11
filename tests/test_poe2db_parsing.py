from __future__ import annotations

import unittest

from poe_affix_builder.adapters.poe2db_modifiers import extract_modifier_sections


def _row(family_key: str, generation_type: int = 1) -> dict[str, object]:
    return {
        "ModGenerationTypeID": generation_type,
        "ModFamilyList": [family_key],
        "Name": family_key,
        "Level": 1,
        "DropChance": 100,
        "str": "<span>+(1-2) to maximum Life</span>",
    }


class Poe2DbParsingTests(unittest.TestCase):
    def test_extract_modifier_sections_keeps_all_observed_section_types(self):
        modsview = {
            "normal": [_row("Normal")],
            "corrupted": [_row("Corrupted", 2)],
            "desecrated": [_row("Desecrated")],
            "essence": [_row("Essence")],
            "perfect_essence": [_row("PerfectEssence")],
            "socketable": [_row("Socketable", 0)],
            "bonded": [_row("Bonded", 0)],
            "empty_section": [],
            "metadata": {"ignored": True},
        }

        sections = extract_modifier_sections(modsview)

        self.assertEqual(
            set(sections),
            {"normal", "corrupted", "desecrated", "essence", "perfect_essence", "socketable", "bonded"},
        )
        self.assertEqual(sections["socketable"][0]["kind"], "gen0")
        self.assertEqual(sections["corrupted"][0]["kind"], "suffix")


if __name__ == "__main__":
    unittest.main()
