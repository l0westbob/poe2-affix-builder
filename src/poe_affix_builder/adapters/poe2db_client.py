from __future__ import annotations

from poe_affix_builder.adapters.poe2db_html import (
    BASE,
    extract_item_bases_from_page,
    extract_item_links_from_modifiers_index,
    extract_modsview,
    slug_from_url,
    strip_html,
    to_abs_no_fragment,
)
from poe_affix_builder.adapters.poe2db_http import DEFAULT_HEADERS, DEFAULT_INDEX_URL, fetch_html, fetch_html_with_client, is_retryable_status
from poe_affix_builder.adapters.poe2db_modifiers import (
    extract_modifier_sections,
    family_key,
    group_affixes,
    kind_from_generation_type,
    normalize_template_from_str,
)

__all__ = [
    "BASE",
    "DEFAULT_HEADERS",
    "DEFAULT_INDEX_URL",
    "extract_item_bases_from_page",
    "extract_item_links_from_modifiers_index",
    "extract_modifier_sections",
    "extract_modsview",
    "family_key",
    "fetch_html",
    "fetch_html_with_client",
    "group_affixes",
    "is_retryable_status",
    "kind_from_generation_type",
    "normalize_template_from_str",
    "slug_from_url",
    "strip_html",
    "to_abs_no_fragment",
]
