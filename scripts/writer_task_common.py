"""Shared deterministic helpers for isolated resume Writer tasks."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


PROFILE_ANCHOR_SKILL_GROUPS = ("Backend", "Frontend", "Tools", "Languages")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.casefold()).strip("-")


def profile_anchor_skill_groups(baseline: list[dict[str, Any]]) -> list[str]:
    """Return configured profile anchors that exist in the canonical baseline."""
    baseline_labels = {
        normalize(item.get("label", ""))
        for item in baseline
        if isinstance(item, dict) and isinstance(item.get("label"), str)
    }
    return [anchor for anchor in PROFILE_ANCHOR_SKILL_GROUPS if normalize(anchor) in baseline_labels]


def experience_source_file(entry: dict[str, Any]) -> str:
    company = re.sub(r"\s*\([^)]*\)", "", entry["company"]).strip()
    return f"knowledge-base/experience/{normalize(company + ' ' + entry['position'])}.md"


def card_matches_experience(
    card: dict[str, Any],
    entry: dict[str, Any],
    *,
    allow_organization: bool = True,
) -> bool:
    expected = experience_source_file(entry)
    if card.get("source_file") == expected:
        return True
    metadata = card.get("source_metadata") or {}
    company = re.sub(r"\s*\([^)]*\)", "", entry["company"]).strip()
    organization = metadata.get("organization")
    if allow_organization and isinstance(organization, str) and normalize(organization) == normalize(company):
        return True
    related = metadata.get("related_experience", [])
    if isinstance(related, str):
        related = [related]
    expected_name = Path(expected).name.casefold()
    return any(Path(str(value)).name.casefold() == expected_name for value in related)


def authored_field(text: str, evidence_ids: list[str]) -> dict[str, Any]:
    return {"mode": "authored", "text": text, "supporting_evidence_ids": evidence_ids}
