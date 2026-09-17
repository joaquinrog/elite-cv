from __future__ import annotations

import re
from typing import Mapping


NONCHARACTER_RE = re.compile(r"[\ufdd0-\ufdef\ufffe\uffff]|[\U0001fffe-\U0001ffff]|[\U0003fffe-\U0003ffff]")
MIN_MEANINGFUL_CHARACTERS = 30


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def audit_pdf_text(
    text: str,
    *,
    expected_fields: Mapping[str, str],
    protected_fields: Mapping[str, str] | None = None,
) -> dict[str, object]:
    findings: list[dict[str, object]] = []

    def add(code: str) -> None:
        if not any(item["code"] == code for item in findings):
            findings.append({"code": code})

    meaningful_text = "".join(character for character in text if character.isalnum())
    if len(meaningful_text) < MIN_MEANINGFUL_CHARACTERS:
        add("text_too_short")
    if "\ufffd" in text:
        add("replacement_character")
    if NONCHARACTER_RE.search(text):
        add("noncharacter")

    normalized = _compact(text)
    for value in expected_fields.values():
        if _compact(str(value)) not in normalized:
            add("expected_text_missing")

    for value in (protected_fields or {}).values():
        compact_value = _compact(str(value))
        if compact_value in normalized:
            continue
        dehyphenated = _compact(re.sub(r"-\s*\n\s*", "", text))
        if compact_value in dehyphenated:
            add("protected_field_hyphenation")

    return {"status": "pass" if not findings else "fail", "findings": findings}
