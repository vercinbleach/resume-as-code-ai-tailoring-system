import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("knowledge_claims.py")
SPEC = importlib.util.spec_from_file_location("knowledge_claims", MODULE_PATH)
assert SPEC and SPEC.loader
knowledge_claims = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = knowledge_claims
SPEC.loader.exec_module(knowledge_claims)


def valid_claim(claim_id: str = "claim-example-automation") -> dict:
    return {
        "id": claim_id,
        "statement": "Automated a repeatable technical workflow.",
        "dimensions": ["technical"],
        "technologies": ["Python"],
        "evidence": [
            {
                "source_type": "user-confirmed",
                "locator": "user-confirmed: 2026-07-17",
                "checked": "2026-07-17",
            }
        ],
        "confidence": "high",
        "status": "confirmed",
        "resume_safe": True,
        "sensitivity": "internal-anonymized",
        "aliases": [],
        "caveats": [],
    }


def write_document(root: Path, payload: dict) -> Path:
    path = root / "knowledge-base" / "projects" / "example.md"
    path.parent.mkdir(parents=True)
    encoded = json.dumps(payload, indent=2)
    path.write_text(
        f"---\nid: project-example\n---\n\n# Example\n\n"
        f"{knowledge_claims.START_MARKER}\n```json\n{encoded}\n```\n"
        f"{knowledge_claims.END_MARKER}\n",
        encoding="utf-8",
    )
    return path


class KnowledgeClaimsTests(unittest.TestCase):
    def test_valid_document_builds_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = {"schema_version": 1, "claims": [valid_claim()], "evidence_gaps": []}
            write_document(root, payload)
            documents, errors = knowledge_claims.discover(root)
            self.assertEqual(errors, [])
            index = knowledge_claims.render_index(root, documents)
            row = json.loads(index)
            self.assertEqual(row["id"], "claim-example-automation")
            self.assertEqual(row["project_id"], "project-example")

    def test_unsafe_status_is_rejected(self) -> None:
        claim = valid_claim()
        claim["status"] = "unverified"
        claim["caveats"] = ["Metric has not been recovered."]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_document(
                root,
                {"schema_version": 1, "claims": [claim], "evidence_gaps": []},
            )
            _, errors = knowledge_claims.discover(root)
            self.assertTrue(any("cannot be resume_safe" in error for error in errors))

    def test_gap_must_reference_existing_claim(self) -> None:
        gap = {
            "id": "gap-example-metric",
            "question": "What was the exact measured improvement?",
            "importance": "high",
            "status": "open",
            "affects_claims": ["claim-missing"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_document(
                root,
                {"schema_version": 1, "claims": [valid_claim()], "evidence_gaps": [gap]},
            )
            _, errors = knowledge_claims.discover(root)
            self.assertTrue(any("references unknown claim-missing" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
