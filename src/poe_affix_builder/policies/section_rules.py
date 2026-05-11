from __future__ import annotations

REGULAR_MODIFIER_SECTIONS = ("normal",)
EXPECTED_NON_NORMAL_MODIFIER_SECTIONS = (
    "bonded",
    "corrupted",
    "desecrated",
    "essence",
    "perfect_essence",
    "socketable",
)

NORMAL_UNRESOLVED = "normal_unresolved"
EXPECTED_NON_NORMAL_UNRESOLVED = "expected_non_normal_unresolved"
UNKNOWN_UNRESOLVED = "unknown_unresolved"


def is_regular_modifier_section(section_name: str) -> bool:
    return section_name in REGULAR_MODIFIER_SECTIONS


def is_expected_non_normal_modifier_section(section_name: str) -> bool:
    return section_name in EXPECTED_NON_NORMAL_MODIFIER_SECTIONS


def unresolved_reason_code(section_name: str) -> str:
    if is_regular_modifier_section(section_name):
        return NORMAL_UNRESOLVED
    if is_expected_non_normal_modifier_section(section_name):
        return EXPECTED_NON_NORMAL_UNRESOLVED
    return UNKNOWN_UNRESOLVED
