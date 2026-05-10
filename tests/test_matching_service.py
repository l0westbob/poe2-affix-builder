from __future__ import annotations

import unittest

from poe_affix_builder.domain.models import ModEntry
from poe_affix_builder.services.matching_service import (
    build_indexes,
    collect_build_candidates,
    select_build_candidate,
    select_rebuild_candidate,
)


def _entry(
    *,
    mod_key: str,
    kind: str = "prefix",
    domain: str = "item",
    family_key: str = "Life",
    required_level: int = 10,
    name: str = "Healthy",
    text: str = "+10 to maximum Life",
    stats: list[dict[str, object]] | None = None,
    spawn_tags: set[str] | None = None,
) -> ModEntry:
    return ModEntry(
        mod_key=mod_key,
        kind=kind,
        domain=domain,
        family_key=family_key,
        required_level=required_level,
        name=name,
        text=text,
        text_norm=text.lower(),
        stats=stats or [{"id": "base_maximum_life", "min": 10, "max": 10}],
        spawn_tags=spawn_tags or {"amulet"},
    )


class MatchingServiceTests(unittest.TestCase):
    def test_build_candidate_falls_back_across_kind(self):
        entries = [_entry(mod_key="A", kind="unique")]
        indexes = build_indexes(entries)
        candidates = collect_build_candidates(
            indexes,
            kind="gen3",
            family_key="Life",
            level=10,
            name="Healthy",
            text_ref="+10 to maximum Life",
        )
        self.assertEqual([row.mod_key for row in candidates], ["A"])

    def test_build_candidate_prefers_exact_stat_order(self):
        candidates = [
            _entry(mod_key="A", stats=[{"id": "a"}, {"id": "b"}]),
            _entry(mod_key="B", stats=[{"id": "b"}, {"id": "a"}]),
        ]
        decision = select_build_candidate(
            candidates,
            include_domains={"item"},
            include_spawn_tags={"amulet"},
            ref_text="+10 to maximum Life",
            ref_name="Healthy",
            ref_stat_ids=["a", "b"],
        )
        self.assertIsNotNone(decision.entry)
        self.assertEqual(decision.entry.mod_key, "A")
        self.assertIn("stats-exact-order", decision.explanation.reasons)

    def test_build_candidate_prefers_domain_and_spawn_tag_alignment(self):
        candidates = [
            _entry(mod_key="A", domain="item", spawn_tags={"amulet"}),
            _entry(mod_key="B", domain="misc", spawn_tags={"ring"}),
        ]
        decision = select_build_candidate(
            candidates,
            include_domains={"item"},
            include_spawn_tags={"amulet"},
            ref_text="+10 to maximum Life",
            ref_name="Healthy",
            ref_stat_ids=["base_maximum_life"],
        )
        self.assertIsNotNone(decision.entry)
        self.assertEqual(decision.entry.mod_key, "A")

    def test_rebuild_candidate_prefers_exact_kind(self):
        candidates = [
            _entry(mod_key="A", kind="prefix"),
            _entry(mod_key="B", kind="suffix"),
        ]
        decision = select_rebuild_candidate(
            candidates,
            kind="prefix",
            text="+10 to maximum Life",
            name="Healthy",
            include_domains={"item"},
            include_spawn_tags={"amulet"},
        )
        self.assertIsNotNone(decision.entry)
        self.assertEqual(decision.entry.mod_key, "A")
        self.assertIn("kind-exact", decision.explanation.reasons)


if __name__ == "__main__":
    unittest.main()
