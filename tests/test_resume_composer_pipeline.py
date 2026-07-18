from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "qa/.venv/Scripts/python.exe"
RENDERCV = ROOT / ".venv/Scripts/rendercv.exe"
START = ROOT / "tailoring/scripts/start-session.ps1"
PREPARE = ROOT / "tailoring/scripts/start-writer.ps1"
FINALIZE = ROOT / "tailoring/scripts/finalize-writer.ps1"
INTAKE = ROOT / "qa/jobs/codeway-applied-ai-20260718-run2/job-intake.json"
BASE = ROOT / "resumes/vincenzo-rosciano-one-page.yaml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class ResumeComposerPipelineE2E(unittest.TestCase):
    def test_full_bundle_promotion(self) -> None:
        run_id = f"e2e-composer-{uuid.uuid4().hex}"
        session = ROOT / "tailoring/sessions" / run_id
        base_hash = sha256(BASE)
        with tempfile.TemporaryDirectory() as directory:
            sandbox_root = Path(directory) / "sandboxes"
            try:
                subprocess.run([
                    "powershell", "-NoProfile", "-File", START,
                    "-JobIntake", INTAKE,
                    "-SessionId", run_id,
                    "-SandboxRoot", sandbox_root,
                ], cwd=ROOT, check=True, capture_output=True, text=True)
                manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
                expected_knowledge = [
                    path
                    for folder in ("experience", "projects")
                    for path in (ROOT / "knowledge-base" / folder).glob("*.md")
                    if path.name != "README.md"
                ]
                self.assertEqual(
                    len(manifest["source"]["knowledge"]),
                    len(expected_knowledge),
                )
                for task_id, task in manifest["tasks"]["scouts"].items():
                    assignment = json.loads(Path(task["assignment"]["path"]).read_text(encoding="utf-8"))
                    write_json(Path(task["sandbox"]) / "outbox/result.json", {
                        "schema_version": 1,
                        "assignment_id": assignment["assignment_id"],
                        "domain": assignment["domain"],
                        "ranked_sources": [],
                        "gaps": [],
                        "conflicts": [],
                    })
                subprocess.run([
                    "powershell", "-NoProfile", "-File", PREPARE, "-Session", session,
                ], cwd=ROOT, check=True, capture_output=True, text=True)
                manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
                composer = manifest["tasks"]["composer"]
                sandbox = Path(composer["sandbox"])
                work = sandbox / "work"
                outbox = sandbox / "outbox"
                shutil.copy2(sandbox / "inputs/base-resume.yaml", work / "resume.yaml")
                subprocess.run([
                    RENDERCV, "render", work / "resume.yaml",
                    "--output-folder", work,
                    "--typst-path", "render-temp/resume.typ",
                    "--pdf-path", "resume.pdf",
                    "--dont-generate-markdown",
                    "--dont-generate-html",
                    "--dont-generate-png",
                    "--quiet",
                ], check=True)
                shutil.copy2(work / "resume.yaml", outbox / "resume.yaml")
                shutil.copy2(work / "resume.pdf", outbox / "resume.pdf")
                resume = yaml.safe_load((outbox / "resume.yaml").read_text(encoding="utf-8"))
                provenance = []
                for entry_index, entry in enumerate(resume["cv"]["sections"]["Experience"]):
                    for bullet_index, _ in enumerate(entry["highlights"]):
                        target = f"/cv/sections/Experience/{entry_index}/highlights/{bullet_index}"
                        provenance.append({"kind": "experience-bullet", "target": target, "sources": [{"type": "baseline", "pointer": target}]})
                for project_index, _ in enumerate(resume["cv"]["sections"]["Projects & Open Source"]):
                    target = f"/cv/sections/Projects & Open Source/{project_index}"
                    provenance.append({"kind": "project", "target": target, "sources": [{"type": "baseline", "pointer": target}]})
                for group_index, group in enumerate(resume["cv"]["sections"]["Technical Skills"]):
                    target = f"/cv/sections/Technical Skills/{group_index}/details"
                    for item in [value.strip() for value in group["details"].split(",") if value.strip()]:
                        provenance.append({"kind": "skill", "target": target, "item": item, "sources": [{"type": "baseline", "pointer": target}]})
                result = {
                    "schema_version": 1,
                    "status": "ready",
                    "inputs": {
                        "baseline_sha256": manifest["snapshots"]["base_resume"]["sha256"],
                        "job_sha256": manifest["snapshots"]["job_description"]["sha256"],
                        "knowledge_manifest_sha256": manifest["snapshots"]["knowledge_manifest"]["sha256"],
                        "scout_result_sha256": [manifest["tasks"]["scouts"][task_id]["output_sha256"] for task_id in sorted(manifest["tasks"]["scouts"])],
                    },
                    "artifacts": {
                        "resume_yaml": {"path": "resume.yaml", "sha256": sha256(outbox / "resume.yaml")},
                        "resume_pdf": {"path": "resume.pdf", "sha256": sha256(outbox / "resume.pdf")},
                    },
                    "provenance": provenance,
                    "visual_inspection": {
                        "inspected": True,
                        "pdf_sha256": sha256(outbox / "resume.pdf"),
                        "page_count": 1,
                        "pages_viewed": [1],
                        "checks": {
                            "no_clipping_or_overlap": True,
                            "legible_text": True,
                            "balanced_spacing": True,
                            "consistent_hierarchy": True,
                        },
                        "issues": [],
                    },
                    "blocking_reasons": [],
                    "questions": [],
                }
                write_json(outbox / "result.json", result)
                subprocess.run([
                    "powershell", "-NoProfile", "-File", FINALIZE, "-Session", session,
                ], cwd=ROOT, check=True, text=True)
                final_manifest = json.loads((session / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(final_manifest["status"], "completed")
                self.assertTrue((session / "composer/resume.pdf").is_file())
                self.assertTrue((session / "composer/receipt.json").is_file())
                self.assertFalse(sandbox_root.exists())
                self.assertEqual(sha256(BASE), base_hash)
            finally:
                if session.exists():
                    for path in session.rglob("*"):
                        if path.is_file():
                            path.chmod(path.stat().st_mode | 0o200)
                    shutil.rmtree(session)


if __name__ == "__main__":
    unittest.main()
