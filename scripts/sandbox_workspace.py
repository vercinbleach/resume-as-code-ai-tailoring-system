#!/usr/bin/env python3
"""Create, verify, and promote lightweight task sandbox workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SCHEMA_VERSION = 1
TOP_LEVEL_ENTRIES = {"inputs", "manifest.json", "outbox", "skill", "work"}
WINDOWS_DEVICE_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class SandboxError(ValueError):
    """Raised when a sandbox violates its declared contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(value: str) -> PurePosixPath:
    normalized = value.replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SandboxError(f"Unsafe relative path: {value}")
    if any(":" in part for part in path.parts):
        raise SandboxError(f"Unsafe relative path: {value}")
    if any(part.split(".", 1)[0].upper() in WINDOWS_DEVICE_NAMES for part in path.parts):
        raise SandboxError(f"Windows device names are not allowed: {value}")
    return path


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _copy_file(source: Path, destination: Path) -> None:
    if _is_reparse_point(source) or not source.is_file():
        raise SandboxError(f"Input must be a regular file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _set_read_only(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _assert_read_only(path: Path) -> None:
    if path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        raise SandboxError(f"Protected sandbox file is writable: {path}")


def remove_tree_force(path: Path) -> None:
    """Remove a sandbox tree even when snapshot files are read-only on Windows."""

    def handle_error(function: Any, value: str, _: Any) -> None:
        target = Path(value)
        try:
            target.chmod(target.stat().st_mode | stat.S_IWUSR)
            function(value)
        except OSError:
            raise

    if path.exists():
        shutil.rmtree(path, onerror=handle_error)


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.is_dir():
        return files
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if _is_reparse_point(path):
            raise SandboxError(f"Symlinks are not allowed in a sandbox: {path}")
        if path.is_file():
            files.append(path)
    return files


def tree_inventory(root: Path) -> list[dict[str, str]]:
    inventory: list[dict[str, str]] = []
    if not root.is_dir():
        return inventory
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if _is_reparse_point(path):
            raise SandboxError(f"Symlinks are not allowed in a sandbox: {path}")
        row = {
            "path": path.relative_to(root).as_posix(),
            "type": "directory" if path.is_dir() else "file",
        }
        if path.is_file():
            row["sha256"] = sha256_file(path)
        inventory.append(row)
    return inventory


def tree_sha256(root: Path) -> str:
    payload = json.dumps(tree_inventory(root), ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _parse_input_specs(values: Iterable[str]) -> list[tuple[Path, PurePosixPath]]:
    parsed: list[tuple[Path, PurePosixPath]] = []
    destinations: set[str] = set()
    for value in values:
        if "::" not in value:
            raise SandboxError("Each --input must use SOURCE::SANDBOX_RELATIVE_PATH")
        source_value, relative_value = value.split("::", 1)
        source = Path(source_value).expanduser().resolve()
        relative = _relative_path(relative_value)
        key = relative.as_posix().lower()
        if key in destinations:
            raise SandboxError(f"Duplicate sandbox input path: {relative}")
        destinations.add(key)
        parsed.append((source, relative))
    return parsed


def create_workspace(
    sandbox: Path,
    *,
    pipeline: str,
    session_id: str,
    task_id: str,
    skill_source: Path,
    inputs: list[tuple[Path, PurePosixPath]],
    promote_to: Path,
    output_name: str = "result.json",
    output_names: list[str] | None = None,
    network: str = "deny",
) -> dict[str, str]:
    sandbox = sandbox.resolve()
    skill_source = skill_source.resolve()
    declared_names = output_names if output_names is not None else [output_name]
    if not declared_names:
        raise SandboxError("At least one output must be declared")
    output_relatives = [_relative_path(value) for value in declared_names]
    if any(len(value.parts) != 1 for value in output_relatives):
        raise SandboxError("Every output must be one file directly inside outbox")
    if len({value.as_posix().lower() for value in output_relatives}) != len(output_relatives):
        raise SandboxError("Duplicate output names are not allowed")
    output_relative = output_relatives[0]
    if network not in {"deny", "allow"}:
        raise SandboxError("network must be deny or allow")
    if sandbox.exists():
        raise SandboxError(f"Sandbox already exists: {sandbox}")
    if not (skill_source / "SKILL.md").is_file():
        raise SandboxError(f"Skill folder has no SKILL.md: {skill_source}")
    for source, _ in inputs:
        if not source.is_file() or _is_reparse_point(source):
            raise SandboxError(f"Input must be a regular file: {source}")

    try:
        (sandbox / "inputs").mkdir(parents=True)
        (sandbox / "work").mkdir()
        (sandbox / "outbox").mkdir()
        shutil.copytree(skill_source, sandbox / "skill")

        input_rows: list[dict[str, str]] = []
        for source, relative in inputs:
            destination = sandbox / "inputs" / Path(*relative.parts)
            _copy_file(source, destination)
            digest = sha256_file(destination)
            input_rows.append(
                {
                    "path": f"inputs/{relative.as_posix()}",
                    "source": str(source),
                    "sha256": digest,
                }
            )

        for protected_root in (sandbox / "inputs", sandbox / "skill"):
            for file_path in _walk_files(protected_root):
                _set_read_only(file_path)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "sandbox_id": f"{pipeline}:{session_id}:{task_id}",
            "pipeline": pipeline,
            "session_id": session_id,
            "task_id": task_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lifecycle": "ephemeral",
            "contract": {
                "enforcement": "cooperative-same-user-with-hash-verification",
                "read_only": ["skill/**", "inputs/**", "manifest.json"],
                "writable": ["work/**", *[f"outbox/{value.as_posix()}" for value in output_relatives]],
                "network": "deny-by-instruction" if network == "deny" else "allow",
                "canonical_repository_write": "deny-by-instruction",
                "other_sandboxes_read": "deny-by-instruction",
                "parent_conversation": "deny-by-instruction",
            },
            "skill": {
                "path": "skill/SKILL.md",
                "source": str(skill_source),
                "tree_sha256": tree_sha256(sandbox / "skill"),
            },
            "inputs": sorted(input_rows, key=lambda row: row["path"].lower()),
            "output": {
                "path": f"outbox/{output_relative.as_posix()}",
                "promote_to": str(promote_to.resolve()),
            },
            "outputs": [f"outbox/{value.as_posix()}" for value in output_relatives],
        }
        manifest_path = sandbox / "manifest.json"
        _write_json(manifest_path, manifest)
        manifest_hash = sha256_file(manifest_path)
        _set_read_only(manifest_path)
        return {
            "sandbox": str(sandbox),
            "manifest": str(manifest_path),
            "manifest_sha256": manifest_hash,
        }
    except Exception:
        if sandbox.exists():
            remove_tree_force(sandbox)
        raise


def _load_manifest(sandbox: Path, expected_manifest_sha256: str | None) -> dict[str, Any]:
    manifest_path = sandbox / "manifest.json"
    if not manifest_path.is_file() or _is_reparse_point(manifest_path):
        raise SandboxError(f"Missing regular manifest.json: {manifest_path}")
    actual_hash = sha256_file(manifest_path)
    if expected_manifest_sha256 and actual_hash.lower() != expected_manifest_sha256.lower():
        raise SandboxError("Sandbox manifest hash changed")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SandboxError(f"Invalid sandbox manifest: {exc}") from exc
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise SandboxError(f"Unsupported sandbox schema: {manifest.get('schema_version')}")
    return manifest


def verify_workspace(
    sandbox: Path,
    *,
    expected_manifest_sha256: str | None = None,
    require_output: bool = False,
) -> dict[str, Any]:
    sandbox = sandbox.resolve()
    if not sandbox.is_dir() or _is_reparse_point(sandbox):
        raise SandboxError(f"Sandbox directory does not exist: {sandbox}")
    manifest = _load_manifest(sandbox, expected_manifest_sha256)

    actual_top_level = {path.name for path in sandbox.iterdir()}
    if actual_top_level != TOP_LEVEL_ENTRIES:
        extra = sorted(actual_top_level - TOP_LEVEL_ENTRIES)
        missing = sorted(TOP_LEVEL_ENTRIES - actual_top_level)
        raise SandboxError(f"Sandbox top-level mismatch, extra={extra}, missing={missing}")

    for path in sandbox.rglob("*"):
        if _is_reparse_point(path):
            raise SandboxError(f"Symlinks are not allowed in a sandbox: {path}")

    _assert_read_only(sandbox / "manifest.json")
    for protected_root in (sandbox / "inputs", sandbox / "skill"):
        for protected_file in _walk_files(protected_root):
            _assert_read_only(protected_file)

    skill_root = sandbox / "skill"
    if tree_sha256(skill_root) != manifest.get("skill", {}).get("tree_sha256"):
        raise SandboxError("Sandbox skill snapshot changed")

    declared_inputs = {row["path"]: row for row in manifest.get("inputs", [])}
    actual_inputs = {
        f"inputs/{path.relative_to(sandbox / 'inputs').as_posix()}": path
        for path in _walk_files(sandbox / "inputs")
    }
    if set(actual_inputs) != set(declared_inputs):
        extra = sorted(set(actual_inputs) - set(declared_inputs))
        missing = sorted(set(declared_inputs) - set(actual_inputs))
        raise SandboxError(f"Sandbox input inventory changed, extra={extra}, missing={missing}")
    for relative, row in declared_inputs.items():
        copy_path = actual_inputs[relative]
        if sha256_file(copy_path) != row["sha256"]:
            raise SandboxError(f"Sandbox input changed: {relative}")
        source = Path(row["source"])
        if not source.is_file() or _is_reparse_point(source):
            raise SandboxError(f"Input source disappeared: {source}")
        if sha256_file(source) != row["sha256"]:
            raise SandboxError(f"Input source changed after sandbox creation: {source}")

    expected_input_directories = {"inputs"}
    for relative in declared_inputs:
        parent = PurePosixPath(relative).parent
        while parent.as_posix() not in {".", "inputs"}:
            expected_input_directories.add(parent.as_posix())
            parent = parent.parent
    actual_input_directories = {
        path.relative_to(sandbox).as_posix()
        for path in (sandbox / "inputs").rglob("*")
        if path.is_dir()
    } | {"inputs"}
    if actual_input_directories != expected_input_directories:
        raise SandboxError("Sandbox input directory structure changed")

    output_relative = manifest.get("output", {}).get("path")
    output_relatives = manifest.get("outputs", [output_relative])
    if (
        not isinstance(output_relative, str)
        or not output_relative.startswith("outbox/")
        or not isinstance(output_relatives, list)
        or not output_relatives
        or any(not isinstance(value, str) or not value.startswith("outbox/") for value in output_relatives)
    ):
        raise SandboxError("Sandbox output contract is invalid")
    output_paths = [sandbox / Path(*PurePosixPath(value).parts) for value in output_relatives]
    allowed_outputs = {path.resolve() for path in output_paths}
    outbox_entries = list((sandbox / "outbox").rglob("*"))
    unexpected = [path for path in outbox_entries if path.resolve() not in allowed_outputs]
    if unexpected:
        raise SandboxError(f"Unexpected outbox files: {[str(path) for path in unexpected]}")
    if require_output:
        missing_outputs = [path for path in output_paths if not path.is_file()]
        if missing_outputs:
            if len(output_paths) == 1:
                raise SandboxError(f"Expected sandbox output is missing: {missing_outputs[0]}")
            raise SandboxError(f"Expected sandbox outputs are missing: {[str(path) for path in missing_outputs]}")

    output_path = output_paths[0]

    return {
        "manifest": manifest,
        "manifest_sha256": sha256_file(sandbox / "manifest.json"),
        "output": str(output_path),
        "output_sha256": sha256_file(output_path) if output_path.is_file() else None,
        "outputs": {
            path.name: {
                "path": str(path),
                "sha256": sha256_file(path) if path.is_file() else None,
            }
            for path in output_paths
        },
    }


def promote_workspace(
    sandbox: Path,
    *,
    expected_manifest_sha256: str,
) -> dict[str, str]:
    if not expected_manifest_sha256:
        raise SandboxError("Promotion requires the coordinator-owned manifest hash")
    verified = verify_workspace(
        sandbox,
        expected_manifest_sha256=expected_manifest_sha256,
        require_output=True,
    )
    manifest = verified["manifest"]
    source = Path(verified["output"])
    destination = Path(manifest["output"]["promote_to"]).resolve()
    if destination.exists():
        raise SandboxError(f"Promotion destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(source, temporary)
        if sha256_file(temporary) != verified["output_sha256"]:
            raise SandboxError("Promoted output hash mismatch")
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "destination": str(destination),
        "sha256": str(verified["output_sha256"]),
    }


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--sandbox", required=True, type=Path)
    create.add_argument("--pipeline", required=True)
    create.add_argument("--session-id", required=True)
    create.add_argument("--task-id", required=True)
    create.add_argument("--skill", required=True, type=Path)
    create.add_argument("--input", action="append", default=[])
    create.add_argument("--output-name", action="append", default=[])
    create.add_argument("--promote-to", required=True, type=Path)
    create.add_argument("--network", choices=("deny", "allow"), default="deny")

    for name in ("verify", "promote"):
        command = subparsers.add_parser(name)
        command.add_argument("--sandbox", required=True, type=Path)
        command.add_argument("--expected-manifest-sha256")
        if name == "verify":
            command.add_argument("--require-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "create":
            result = create_workspace(
                args.sandbox,
                pipeline=args.pipeline,
                session_id=args.session_id,
                task_id=args.task_id,
                skill_source=args.skill,
                inputs=_parse_input_specs(args.input),
                output_names=args.output_name or ["result.json"],
                promote_to=args.promote_to,
                network=args.network,
            )
        elif args.command == "verify":
            result = verify_workspace(
                args.sandbox,
                expected_manifest_sha256=args.expected_manifest_sha256,
                require_output=args.require_output,
            )
        else:
            if not args.expected_manifest_sha256:
                raise SandboxError("promote requires --expected-manifest-sha256")
            result = promote_workspace(
                args.sandbox,
                expected_manifest_sha256=args.expected_manifest_sha256,
            )
    except (OSError, SandboxError) as exc:
        print(f"ERROR: {exc}")
        return 1
    _print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
