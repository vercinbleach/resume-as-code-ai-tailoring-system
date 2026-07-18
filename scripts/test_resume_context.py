import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


retrieve_claims = load_module("retrieve_claims")
assemble_context_pack = load_module("assemble_context_pack")
validate_context_artifact = load_module("validate_context_artifact")


SOURCE = "knowledge-base/projects/test.md"


def claim(claim_id: str, statement: str, technology: str, *, safe: bool = True) -> dict:
    return {
        "id": claim_id,
        "statement": statement,
        "dimensions": ["technical"],
        "technologies": [technology] if technology else [],
        "evidence": [{"source_type": "user-confirmed", "locator": "user-confirmed: test", "checked": "2026-07-18"}],
        "confidence": "high" if safe else "low",
        "status": "confirmed" if safe else "unverified",
        "resume_safe": safe,
        "sensitivity": "internal-anonymized",
        "aliases": [],
        "caveats": [] if safe else ["Not verified."],
        "project_id": "project-test",
        "source_file": SOURCE,
    }


def intake(criteria: list[tuple[str, str]]) -> dict:
    return {
        "schema_version": "1.1",
        "capture": {"canonical_url": "https://example.com/job"},
        "job": {
            "company": "Example", "title": "Engineer", "job_id": "1",
            "criteria": [{
                "id": criterion_id, "text": text, "kind": "must-have", "search_terms": [text],
                "source": {"url": "https://example.com/job", "location": "requirements"},
            } for criterion_id, text in criteria],
        },
    }


def evidence_unit(evidence_id: str, claim_id: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "source_file": SOURCE,
        "line_start": 4,
        "line_end": 6,
        "excerpt": "## Evidence\n\nBuilt supported systems.",
        "claim_ids": [claim_id],
    }


def finding(finding_id: str, criterion_id: str, units: list[dict], *, status: str = "strong", safe: bool = True) -> dict:
    return {
        "finding_id": finding_id,
        "criterion_id": criterion_id,
        "status": status,
        "evidence_strength": "high" if units else "none",
        "evidence_units": units,
        "reason": "Direct supported match." if units else "No supported match.",
        "caveats": [],
        "follow_up_questions": [],
        "resume_safe": safe,
    }


class ResumeContextTests(unittest.TestCase):
    def test_exact_technology_ranks_first(self) -> None:
        claims = {
            "claim-python": claim("claim-python", "Built backend workflows.", "Python"),
            "claim-java": claim("claim-java", "Built backend workflows.", "Java"),
        }
        fields = {claim_id: retrieve_claims.claim_fields(value) for claim_id, value in claims.items()}
        idf = retrieve_claims.inverse_document_frequency(fields)
        criterion = {"text": "Strong Python skills", "search_terms": ["Python"]}
        python_score, _ = retrieve_claims.score_claim(criterion, claims["claim-python"], fields["claim-python"], idf)
        java_score, _ = retrieve_claims.score_claim(criterion, claims["claim-java"], fields["claim-java"], idf)
        self.assertGreater(python_score, java_score)

    def test_fallback_criteria_are_atomic_and_stable(self) -> None:
        legacy = {"job": {"requirements": {"must_have": [{"text": "Python", "source": None}], "preferred": [], "unclear": []}, "responsibilities": [{"text": "Build tools", "source": None}]}}
        criteria = retrieve_claims.extract_criteria(legacy)
        self.assertEqual([item["id"] for item in criteria], ["must-have-001", "responsibility-001"])

    def _fixture(self, root: Path, criteria: list[tuple[str, str]], values: list[dict]) -> dict[str, Path]:
        paths = {name: root / name for name in ("job-intake.json", "claims.jsonl", "candidate-pool.json", "evidence.json", "risk.json")}
        source = root / SOURCE
        source.parent.mkdir(parents=True)
        source.write_text("---\nid: project-test\n---\n## Evidence\n\nBuilt supported systems.\n", encoding="utf-8")
        paths["job-intake.json"].write_text(json.dumps(intake(criteria)), encoding="utf-8")
        paths["claims.jsonl"].write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")
        paths["candidate-pool.json"].write_text(json.dumps({
            "inputs": {
                "job_intake_sha256": assemble_context_pack.sha256_file(paths["job-intake.json"]),
                "claim_index_sha256": assemble_context_pack.sha256_file(paths["claims.jsonl"]),
            },
            "criteria": [{"id": item[0], "narrative_candidates": []} for item in criteria],
        }), encoding="utf-8")
        return paths

    def test_assembler_requires_risk_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = [claim("claim-python", "Built Python workflows.", "Python"), claim("claim-java", "Built Java services.", "Java")]
            paths = self._fixture(root, [("python", "Python"), ("java", "Java")], values)
            python_unit = evidence_unit("evidence-python", "claim-python")
            java_unit = evidence_unit("evidence-java", "claim-java")
            paths["evidence.json"].write_text(json.dumps({"schema_version": 3, "role": "evidence-reviewer", "findings": [finding("finding-python", "python", [python_unit]), finding("finding-java", "java", [java_unit])]}), encoding="utf-8")
            paths["risk.json"].write_text(json.dumps({"schema_version": 3, "role": "claim-risk-critic", "findings": [finding("finding-risk-python", "python", [python_unit]), finding("finding-risk-java", "java", [java_unit], status="conflict", safe=False)]}), encoding="utf-8")
            result = assemble_context_pack.assemble(paths["job-intake.json"], paths["claims.jsonl"], paths["candidate-pool.json"], paths["evidence.json"], paths["risk.json"], root, 3, 20)
            self.assertEqual([item["id"] for item in result["evidence_cards"]], ["evidence-python"])
            self.assertEqual([item["id"] for item in result["claims"]], ["claim-python"])
            indexed = {value["id"]: value for value in values}
            self.assertEqual(validate_context_artifact.validate_context_pack(result, indexed, root), [])

    def test_narrative_excerpt_without_claim_can_be_approved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = self._fixture(root, [("delivery", "Delivery")], [claim("claim-unused", "Unused claim statement.", "")])
            unit = evidence_unit("evidence-delivery", "claim-unused")
            unit["claim_ids"] = []
            paths["evidence.json"].write_text(json.dumps({"schema_version": 3, "role": "evidence-reviewer", "findings": [finding("finding-delivery", "delivery", [unit])]}), encoding="utf-8")
            paths["risk.json"].write_text(json.dumps({"schema_version": 3, "role": "claim-risk-critic", "findings": [finding("finding-risk-delivery", "delivery", [unit])]}), encoding="utf-8")
            result = assemble_context_pack.assemble(paths["job-intake.json"], paths["claims.jsonl"], paths["candidate-pool.json"], paths["evidence.json"], paths["risk.json"], root, 3, 20)
            self.assertEqual(result["evidence_cards"][0]["excerpt"], unit["excerpt"])
            self.assertEqual(result["claims"], [])

    def test_critic_must_cover_every_proposed_use_exactly(self) -> None:
        unit = evidence_unit("evidence-python", "claim-python")
        reviewer = {"schema_version": 3, "role": "evidence-reviewer", "findings": [finding("finding-python", "python", [unit])]}
        critic = {"schema_version": 3, "role": "claim-risk-critic", "findings": []}
        with self.assertRaisesRegex(ValueError, "critic omitted proposed evidence uses"):
            assemble_context_pack.validate_critic_coverage(reviewer, critic)


if __name__ == "__main__":
    unittest.main()
