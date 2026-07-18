import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from assemble_writer_results import assemble
from materialize_writer_result import materialize
from prepare_writer_assignments import build_assignments
from validate_writer_result import validate_result
from writer_task_common import sha256_file, write_json


def card(evidence_id: str, source_file: str, source_id: str, criterion: str) -> dict:
    return {
        "id": evidence_id,
        "criterion_id": criterion,
        "source_file": source_file,
        "line_start": 1,
        "line_end": 3,
        "excerpt": "## Evidence\n\nSupported delivery.",
        "excerpt_sha256": "unused-in-this-test",
        "claim_ids": [],
        "technologies": ["Python"],
        "source_metadata": {"id": source_id, "organization": "Example Co"},
        "reason": "Supported.",
        "caveats": [],
        "use_status": "include",
    }


class WriterFanoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = {
            "cv": {"name": "Candidate", "sections": {
                "Education": [{"name": "University"}],
                "Experience": [{"company": "Example Co", "position": "Engineer", "highlights": ["Old bullet"]}],
                "Projects & Open Source": [{"label": "Old Project", "details": "Old details"}],
                "Technical Skills": [
                    {"label": "Backend", "details": "Python"},
                    {"label": "Frontend", "details": "React"},
                    {"label": "Tools", "details": "Docker"},
                    {"label": "Languages", "details": "Spanish"},
                ],
            }},
            "design": {},
        }
        self.context = {
            "schema_version": 2,
            "job": {"company": "Target", "title": "Engineer"},
            "criteria": [{"criterion_id": "python", "text": "Python", "kind": "must-have", "decision": "include", "include_evidence_ids": ["evidence-exp", "evidence-project"], "maybe_evidence_ids": [], "reasons": [], "caveats": [], "follow_up_questions": []}],
            "evidence_cards": [
                card("evidence-exp", "knowledge-base/experience/example-co-engineer.md", "exp-example", "python"),
                card("evidence-project", "knowledge-base/projects/example.md", "project-example", "python"),
            ],
        }

    def test_assignments_are_scoped_and_assembled_deterministically(self) -> None:
        assignments = build_assignments(self.context, self.base)
        self.assertEqual([item["id"] for item in assignments["experience-0"]["evidence_cards"]], ["evidence-exp", "evidence-project"])
        self.assertEqual([item["id"] for item in assignments["projects"]["evidence_cards"]], ["evidence-project"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assignments_dir = root / "assignments"
            results_dir = root / "results"
            assignments_dir.mkdir()
            results_dir.mkdir()
            for task_id, assignment in assignments.items():
                write_json(assignments_dir / f"{task_id}.json", assignment)
            results = {
                "experience-0": {"source_index": 0, "highlights": [{"mode": "authored", "text": "Built Python systems.", "supporting_evidence_ids": ["evidence-exp"]}]},
                "projects": {"projects": [{"mode": "authored", "project_id": "project-example", "label": "Example", "details": "Built a Python project.", "supporting_evidence_ids": ["evidence-project"]}]},
                "technical-skills": {"technical_skills": [
                    {"mode": "preserve", "source_index": 3},
                    {"mode": "authored", "skill_group_id": "backend", "label": "Backend", "details": "Python", "supporting_evidence_ids": ["evidence-exp"]},
                    {"mode": "preserve", "source_index": 2},
                    {"mode": "preserve", "source_index": 1},
                ]},
            }
            for task_id, content in results.items():
                assignment_path = assignments_dir / f"{task_id}.json"
                write_json(results_dir / f"{task_id}.json", {
                    "schema_version": 1,
                    "task_id": task_id,
                    "assignment_sha256": sha256_file(assignment_path),
                    "status": "ready",
                    "content": content,
                    "blocking_reasons": [],
                    "questions": [],
                })
            context_path = root / "context.json"
            base_path = root / "base.yaml"
            write_json(context_path, self.context)
            base_path.write_text(yaml.safe_dump(self.base, sort_keys=False), encoding="utf-8")
            result = assemble(assignments_dir, results_dir, context_path, base_path)
            errors = validate_result(result, self.context, self.base, result_context_sha256=sha256_file(context_path), result_base_sha256=sha256_file(base_path))
            self.assertEqual(errors, [])
            for anchor, source_index in (("Tools", 2), ("Languages", 3)):
                missing_anchor = copy.deepcopy(result)
                missing_anchor["content"]["technical_skills"] = [
                    item for item in missing_anchor["content"]["technical_skills"]
                    if item.get("source_index") != source_index
                ]
                errors = validate_result(missing_anchor, self.context, self.base, result_context_sha256=sha256_file(context_path), result_base_sha256=sha256_file(base_path))
                self.assertIn(f"technical_skills must retain profile anchor '{anchor}'", errors)
            output = materialize(result, self.base)
            self.assertEqual(output["cv"]["sections"]["Education"], self.base["cv"]["sections"]["Education"])
            self.assertEqual(output["cv"]["sections"]["Experience"][0]["highlights"], ["Built Python systems."])

    def test_project_cannot_cite_another_project(self) -> None:
        assignments = build_assignments(self.context, self.base)
        project = assignments["projects"]
        item = {"mode": "authored", "project_id": "project-other", "label": "Other", "details": "Wrong.", "supporting_evidence_ids": ["evidence-project"]}
        from validate_writer_part import validate_part
        result = {"schema_version": 1, "task_id": "projects", "assignment_sha256": "x", "status": "ready", "content": {"projects": [item]}, "blocking_reasons": [], "questions": []}
        errors = validate_part(result, project, "x")
        self.assertTrue(any("another project" in error for error in errors))

    def test_skills_require_all_profile_anchors_but_allow_reordering(self) -> None:
        assignments = build_assignments(self.context, self.base)
        skills = assignments["technical-skills"]
        from validate_writer_part import validate_part
        self.assertEqual(
            skills["constraints"]["profile_anchor_groups"],
            ["Backend", "Frontend", "Tools", "Languages"],
        )
        reordered = {
            "schema_version": 1,
            "task_id": "technical-skills",
            "assignment_sha256": "x",
            "status": "ready",
            "content": {"technical_skills": [
                {"mode": "preserve", "source_index": 3},
                {"mode": "preserve", "source_index": 1},
                {"mode": "preserve", "source_index": 0},
                {"mode": "preserve", "source_index": 2},
            ]},
            "blocking_reasons": [],
            "questions": [],
        }
        self.assertEqual(validate_part(reordered, skills, "x"), [])
        for anchor, source_index in (("Tools", 2), ("Languages", 3)):
            missing_anchor = copy.deepcopy(reordered)
            missing_anchor["content"]["technical_skills"] = [
                item for item in missing_anchor["content"]["technical_skills"]
                if item["source_index"] != source_index
            ]
            errors = validate_part(missing_anchor, skills, "x")
            self.assertIn(f"technical_skills must retain profile anchor '{anchor}'", errors)

    def test_organization_only_evidence_does_not_cross_roles_at_same_company(self) -> None:
        second = {"company": "Example Co", "position": "Lead Engineer", "highlights": ["Old lead bullet"]}
        self.base["cv"]["sections"]["Experience"].append(second)
        assignments = build_assignments(self.context, self.base)
        self.assertEqual([item["id"] for item in assignments["experience-0"]["evidence_cards"]], ["evidence-exp"])
        self.assertEqual(assignments["experience-1"]["evidence_cards"], [])


if __name__ == "__main__":
    unittest.main()
