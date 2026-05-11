from __future__ import annotations

import unittest

from poe_affix_builder.policies import (
    EXPECTED_NON_NORMAL_UNRESOLVED,
    NORMAL_UNRESOLVED,
    UNKNOWN_UNRESOLVED,
    domain_for_category,
    spawn_tags_for_slug,
    unresolved_reason_code,
)


class PolicyTests(unittest.TestCase):
    def test_domain_policy_matches_expected_categories(self):
        self.assertEqual(domain_for_category("Tablet"), "tablet")
        self.assertEqual(domain_for_category("Relics"), "sanctum_relic")
        self.assertEqual(domain_for_category("Waystones"), "area")
        self.assertEqual(domain_for_category("Weapons"), "item")

    def test_spawn_tags_policy_matches_direct_and_derived_rules(self):
        self.assertEqual(spawn_tags_for_slug("Amulets"), ["amulet"])
        self.assertEqual(spawn_tags_for_slug("Body_Armours_str_dex"), ["body_armour", "str_dex_armour"])
        self.assertEqual(spawn_tags_for_slug("Helmets_int"), ["helmet", "int_armour"])

    def test_section_policy_classifies_unresolved_groups(self):
        self.assertEqual(unresolved_reason_code("normal"), NORMAL_UNRESOLVED)
        self.assertEqual(unresolved_reason_code("socketable"), EXPECTED_NON_NORMAL_UNRESOLVED)
        self.assertEqual(unresolved_reason_code("unexpected_section"), UNKNOWN_UNRESOLVED)


if __name__ == "__main__":
    unittest.main()
