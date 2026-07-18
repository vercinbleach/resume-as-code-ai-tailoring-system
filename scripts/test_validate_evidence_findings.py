import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate_evidence_findings.py")
SPEC = importlib.util.spec_from_file_location("validate_evidence_findings", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def unit(claim_ids: list[str] | None = None, evidence_id: str = "evidence-python") -> dict:
    return {
        "evidence_id": evidence_id,
        "source_file": "knowledge-base/projects/example.md",
        "line_start": 1,
        "line_end": 1,
        "excerpt": "Supported Python delivery.",
        "claim_ids": claim_ids or [],
    }


def packet(claim_id: str | None = None, resume_safe: bool = True, *, role: str = "evidence-reviewer") -> dict:
    return {
        "schema_version": 3,
        "role": role,
        "findings": [{
            "finding_id": "finding-python",
            "criterion_id": "must-have-python",
            "status": "strong",
            "evidence_strength": "high",
            "evidence_units": [unit([claim_id] if claim_id else [])],
            "reason": "The source directly demonstrates Python delivery.",
            "caveats": [],
            "follow_up_questions": [],
            "resume_safe": resume_safe,
        }],
    }


class EvidenceFindingTests(unittest.TestCase):
    def test_safe_claim_passes(self) -> None:
        claims = {"claim-safe": {"resume_safe": True, "status": "confirmed", "source_file": "knowledge-base/projects/example.md"}}
        self.assertEqual(validator.validate_packet(packet("claim-safe"), claims), [])

    def test_unsafe_claim_cannot_be_marked_safe(self) -> None:
        claims = {"claim-unsafe": {"resume_safe": False, "status": "unverified", "source_file": "knowledge-base/projects/example.md"}}
        errors = validator.validate_packet(packet("claim-unsafe"), claims)
        self.assertTrue(any("referenced claim is unsafe" in error for error in errors))
        self.assertTrue(any("unsafe claim status" in error for error in errors))

    def test_missing_reviewer_finding_has_no_units(self) -> None:
        value = packet(resume_safe=False)
        finding = value["findings"][0]
        finding["status"] = "missing"
        finding["evidence_units"] = []
        finding["evidence_strength"] = "none"
        self.assertEqual(validator.validate_packet(value, {}), [])

    def test_critic_requires_one_evidence_unit_per_use(self) -> None:
        value = packet(role="claim-risk-critic")
        value["findings"][0]["evidence_units"] = []
        errors = validator.validate_packet(value, {})
        self.assertTrue(any("exactly one evidence unit" in error for error in errors))

    def test_duplicate_evidence_id_is_rejected(self) -> None:
        value = packet()
        duplicate = dict(value["findings"][0])
        duplicate["finding_id"] = "finding-python-duplicate"
        value["findings"].append(duplicate)
        errors = validator.validate_packet(value, {})
        self.assertTrue(any("evidence_id is duplicated" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
