from __future__ import annotations

import re
from typing import Optional

_NUMBER_RE = re.compile(r"\d{1,4}")
_RANGE_HASH_RE = re.compile(r"\(\s*#\s*[-]\s*#\s*\)")
_SINGLE_HASH_RE = re.compile(r"\(\s*#\s*\)")
_WS_RE = re.compile(r"\s+")


def normalize_dashes(text: str) -> str:
    return text.replace("—", "-").replace("–", "-").replace("−", "-")


def normalize_output_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    out = out.replace("\n", " ")
    out = normalize_dashes(out)
    out = _WS_RE.sub(" ", out).strip()
    return out


def normalize_compare_text(text: Optional[str]) -> Optional[str]:
    out = normalize_output_text(text)
    if out is None:
        return None
    return out.lower()


def text_to_template(mod_text: str) -> str:
    text = normalize_output_text(mod_text) or ""
    text = _NUMBER_RE.sub("#", text)
    text = _RANGE_HASH_RE.sub("#", text)
    text = _SINGLE_HASH_RE.sub("#", text)
    text = _WS_RE.sub(" ", text).strip()
    return text
