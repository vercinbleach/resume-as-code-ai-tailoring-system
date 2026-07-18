from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sandbox_workspace import (  # noqa: E402
    SandboxError,
    _relative_path,
    create_workspace,
    promote_workspace,
    remove_tree_force,
    verify_workspace,
)


class SandboxWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.skill = self.root / "source-skill"
        (self.skill / "references").mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("---\nname: test\ndescription: test\n---\n", encoding="utf-8")
        (self.skill / "references" / "rubric.md").write_text("rubric\n", encoding="utf-8")
        self.source = self.root / "resume.pdf"
        self.source.write_bytes(b"resume bytes")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create(self, name: str = "technical") -> tuple[Path, Path, dict[str, str]]:
        sandbox = self.root / "sandboxes" / name
        destination = self.root / "session" / "evaluators" / f"{name}.json"
        created = create_workspace(
            sandbox,
            pipeline="qa",
            session_id="test-session",
            task_id=name,
            skill_source=self.skill,
            inputs=[(self.source, PurePosixPath("resume.pdf"))],
            output_name="result.json",
            promote_to=destination,
        )
        return sandbox, destination, created

    def make_writable(self, path: Path) -> None:
        path.chmod(path.stat().st_mode | stat.S_IWUSR)

    def test_happy_path_creates_promotes_without_overwrite_and_cleans_up(self) -> None:
        sandbox, destination, created = self.create()
        manifest = json.loads((sandbox / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["contract"]["network"], "deny-by-instruction")
        self.assertEqual(
            manifest["contract"]["enforcement"],
            "cooperative-same-user-with-hash-verification",
        )
        self.assertFalse((sandbox / "inputs" / "resume.pdf").stat().st_mode & stat.S_IWUSR)
        output = sandbox / "outbox" / "result.json"
        output.write_text('{"score": 50}\n', encoding="utf-8")
        verify_workspace(
            sandbox,
            expected_manifest_sha256=created["manifest_sha256"],
            require_output=True,
        )
        promote_workspace(sandbox, expected_manifest_sha256=created["manifest_sha256"])
        self.assertEqual(destination.read_bytes(), output.read_bytes())
        with self.assertRaisesRegex(SandboxError, "already exists"):
            promote_workspace(sandbox, expected_manifest_sha256=created["manifest_sha256"])
        remove_tree_force(sandbox)
        self.assertFalse(sandbox.exists())

    def test_snapshot_or_manifest_tampering_blocks_verification(self) -> None:
        sandbox, _, created = self.create("input-tamper")
        copied = sandbox / "inputs" / "resume.pdf"
        self.make_writable(copied)
        copied.write_bytes(b"changed")
        copied.chmod(copied.stat().st_mode & ~stat.S_IWUSR)
        with self.assertRaisesRegex(SandboxError, "Sandbox input changed"):
            verify_workspace(sandbox, expected_manifest_sha256=created["manifest_sha256"])

        skill_sandbox, _, skill_created = self.create("skill-tamper")
        copied_skill = skill_sandbox / "skill" / "SKILL.md"
        self.make_writable(copied_skill)
        copied_skill.write_text("changed\n", encoding="utf-8")
        copied_skill.chmod(copied_skill.stat().st_mode & ~stat.S_IWUSR)
        with self.assertRaisesRegex(SandboxError, "skill snapshot changed"):
            verify_workspace(
                skill_sandbox,
                expected_manifest_sha256=skill_created["manifest_sha256"],
            )

        other, _, other_created = self.create("manifest-tamper")
        manifest = other / "manifest.json"
        self.make_writable(manifest)
        manifest.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(SandboxError, "manifest hash changed"):
            verify_workspace(other, expected_manifest_sha256=other_created["manifest_sha256"])

    def test_missing_or_additional_outbox_content_blocks_promotion(self) -> None:
        sandbox, _, created = self.create()
        with self.assertRaisesRegex(SandboxError, "output is missing"):
            verify_workspace(
                sandbox,
                expected_manifest_sha256=created["manifest_sha256"],
                require_output=True,
            )
        (sandbox / "outbox" / "result.json").write_text("{}\n", encoding="utf-8")
        (sandbox / "outbox" / "unexpected").mkdir()
        with self.assertRaisesRegex(SandboxError, "Unexpected outbox files"):
            verify_workspace(
                sandbox,
                expected_manifest_sha256=created["manifest_sha256"],
                require_output=True,
            )

    def test_unsafe_relative_paths_are_rejected(self) -> None:
        for value in ("/outside/file", "../file", "dir/file.json:stream", "CON", "folder/LPT9.txt"):
            with self.subTest(value=value), self.assertRaises(SandboxError):
                _relative_path(value)

    def test_composer_workspace_requires_every_declared_output(self) -> None:
        sandbox = self.root / "sandboxes" / "composer"
        created = create_workspace(
            sandbox,
            pipeline="resume-composer",
            session_id="test-session",
            task_id="resume-composer",
            skill_source=self.skill,
            inputs=[(self.source, PurePosixPath("resume.pdf"))],
            output_names=["result.json", "resume.yaml", "resume.pdf"],
            promote_to=self.root / "session" / "composer" / "result.json",
        )
        for name in ("result.json", "resume.yaml"):
            (sandbox / "outbox" / name).write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(SandboxError, "outputs are missing"):
            verify_workspace(sandbox, expected_manifest_sha256=created["manifest_sha256"], require_output=True)
        (sandbox / "outbox" / "resume.pdf").write_bytes(b"pdf")
        verified = verify_workspace(sandbox, expected_manifest_sha256=created["manifest_sha256"], require_output=True)
        self.assertEqual(set(verified["outputs"]), {"result.json", "resume.yaml", "resume.pdf"})


if __name__ == "__main__":
    unittest.main()
