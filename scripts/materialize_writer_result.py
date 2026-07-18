#!/usr/bin/env python3
"""Materialize a validated Writer result into a job-specific RenderCV YAML."""

from __future__ import annotations

import argparse
import copy
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from validate_writer_result import validate_files


def materialize(result: dict[str, Any], base_resume: dict[str, Any]) -> dict[str, Any]:
    if result["status"] != "ready":
        raise ValueError("needs-evidence results cannot be materialized")
    output = copy.deepcopy(base_resume)
    base_sections = base_resume["cv"]["sections"]
    output_sections = output["cv"]["sections"]
    content = result["content"]

    experience: list[dict[str, Any]] = []
    for decision in content["experience"]:
        entry = copy.deepcopy(base_sections["Experience"][decision["source_index"]])
        entry["highlights"] = [
            entry["highlights"][field["baseline_index"]]
            if field["mode"] == "preserve"
            else field["text"]
            for field in decision["highlights"]
        ]
        experience.append(entry)
    output_sections["Experience"] = experience

    projects: list[dict[str, Any]] = []
    for decision in content["projects"]:
        if decision["mode"] == "preserve":
            entry = copy.deepcopy(base_sections["Projects & Open Source"][decision["source_index"]])
        else:
            entry = {"label": decision["label"], "details": decision["details"]}
        projects.append(entry)
    output_sections["Projects & Open Source"] = projects

    technical_skills: list[dict[str, Any]] = []
    for decision in content["technical_skills"]:
        if decision["mode"] == "preserve":
            entry = copy.deepcopy(base_sections["Technical Skills"][decision["source_index"]])
        else:
            entry = {"label": decision["label"], "details": decision["details"]}
        technical_skills.append(entry)
    output_sections["Technical Skills"] = technical_skills
    return output


def write_yaml_atomic(document: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(
        document,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    )
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
        text=True,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
        os.replace(temporary_name, output_path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--context-pack", required=True, type=Path)
    parser.add_argument("--base-resume", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result_path = args.result.resolve()
    context_path = args.context_pack.resolve()
    base_path = args.base_resume.resolve()
    output_path = args.output.resolve()
    if output_path in {result_path, context_path, base_path}:
        print("ERROR: output cannot overwrite a Writer input", file=sys.stderr)
        return 1
    try:
        result, _, base_resume, errors = validate_files(result_path, context_path, base_path)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        materialized = materialize(result, base_resume)
        write_yaml_atomic(materialized, output_path)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
