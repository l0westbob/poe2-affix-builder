from __future__ import annotations

import unittest

from poe_affix_builder.policies import EXPECTED_NON_NORMAL_UNRESOLVED, NORMAL_UNRESOLVED, UNKNOWN_UNRESOLVED
from poe_affix_builder.services.diagnostics_service import unresolved_diagnostics_to_dict


class DiagnosticsTests(unittest.TestCase):
    def test_unresolved_diagnostics_are_section_categorized(self):
        diagnostics = unresolved_diagnostics_to_dict(
            [
                {"section": "normal", "slug": "Amulets", "kind": "suffix", "family_key": "Life", "level": 1},
                {"section": "socketable", "slug": "Claws", "kind": "gen0", "family_key": "AdeptRune", "level": 1},
                {"section": "mystery", "slug": "Claws", "kind": "gen9", "family_key": "Unknown", "level": 1},
            ]
        )

        self.assertEqual(diagnostics["summary"][NORMAL_UNRESOLVED], 1)
        self.assertEqual(diagnostics["summary"][EXPECTED_NON_NORMAL_UNRESOLVED], 1)
        self.assertEqual(diagnostics["summary"][UNKNOWN_UNRESOLVED], 1)
        self.assertEqual(diagnostics["unresolved_matches"][EXPECTED_NON_NORMAL_UNRESOLVED][0]["section"], "socketable")


if __name__ == "__main__":
    unittest.main()
