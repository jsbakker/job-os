"""Shared fixtures for the scripts/ pytest suite.

Testing strategy: entirely subprocess-based. Every script under scripts/ is
invoked exactly as the .claude/skills/*/SKILL.md files invoke it -- as a real
`python3 scripts/X.py ...` subprocess -- rather than imported and called
in-process. This is the most faithful-to-real-usage approach and requires
zero changes to the scripts themselves.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _run_python(script_path, *args, cwd=None, input=None, env=None):
    return subprocess.run(
        [sys.executable, str(script_path), *args],
        capture_output=True,
        text=True,
        input=input,
        cwd=cwd,
        env=env,
    )


@pytest.fixture
def scripts_dir():
    return SCRIPTS_DIR


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def run_script():
    """run_script(script_name, *args, cwd=None, input=None) -> CompletedProcess

    Invokes the real scripts/<script_name> as a subprocess, mirroring exactly
    how the .claude/skills/*/SKILL.md files invoke it.
    """
    def _run(script_name, *args, cwd=None, input=None):
        return _run_python(SCRIPTS_DIR / script_name, *args, cwd=cwd, input=input)
    return _run


@pytest.fixture
def run_json(run_script):
    """run_json(script_name, *args, expect_fail=False, **kw) -> (CompletedProcess, dict|None)

    run_script + json.loads(stdout). Asserts returncode == 0 unless
    expect_fail=True, in which case it asserts returncode != 0 and returns
    (result, None) without attempting to parse stdout as JSON.
    """
    def _run(script_name, *args, expect_fail=False, **kw):
        result = run_script(script_name, *args, **kw)
        if expect_fail:
            assert result.returncode != 0, f"expected failure but got exit 0: {result.stdout!r}"
            return result, None
        assert result.returncode == 0, f"exit {result.returncode}\nstderr: {result.stderr}\nstdout: {result.stdout}"
        return result, json.loads(result.stdout)
    return _run


@pytest.fixture
def fake_repo(tmp_path):
    """fake_repo(**overrides) -> Path

    Builds a synthetic repo tree under tmp_path containing everything
    manifest_check.py's fixed input-file list looks for, plus a copy of the
    real manifest_check.py under <root>/scripts/. manifest_check.py computes
    REPO_ROOT = Path(__file__).resolve().parent.parent -- i.e. from the
    script file's own location on disk, not from cwd -- so invoking the
    *copy* at <root>/scripts/manifest_check.py fully decouples it from the
    real checkout (and the real personal data that may be sitting in it)
    with zero changes to the script itself.

    Keyword overrides:
        include_salary_expectations: bool, default True
        experience_files: dict[filename, content], default one entry
        career_goals_files: dict[filename, content], default one entry
        job_description: filename under variable-input/job-descriptions/
        job_description_content: str
    """
    def _make(
        *,
        include_salary_expectations=True,
        experience_files=None,
        career_goals_files=None,
        job_description="test-job.md",
        job_description_content="Test JD content\n",
    ):
        root = tmp_path / "fake_repo"
        (root / "scripts").mkdir(parents=True)
        shutil.copy(SCRIPTS_DIR / "manifest_check.py", root / "scripts" / "manifest_check.py")

        (root / "blueprint.md").write_text("blueprint content\n")
        (root / "formatting.md").write_text("formatting content\n")

        template = root / "template"
        template.mkdir()
        (template / "contact-info.txt").write_text("name: Test Person\n")
        (template / "all-skills.md").write_text("# Skills\nPython\n")
        (template / "certifications.md").write_text("# Certs\n")
        (template / "education.md").write_text("# Education\n")
        (template / "publications.md").write_text("# Publications\n")

        exp_dir = template / "experience"
        exp_dir.mkdir()
        for fname, content in (experience_files or {"2020-01_2022-01.md": "role content\n"}).items():
            (exp_dir / fname).write_text(content)

        vi = root / "variable-input"
        cg_dir = vi / "career-goals"
        cg_dir.mkdir(parents=True)
        for fname, content in (career_goals_files or {"goal.md": "goal content\n"}).items():
            (cg_dir / fname).write_text(content)

        jd_dir = vi / "job-descriptions"
        jd_dir.mkdir(parents=True)
        (jd_dir / job_description).write_text(job_description_content)

        if include_salary_expectations:
            (vi / "salary-expectations.md").write_text("Target: 100000\n")

        return root

    return _make


@pytest.fixture
def run_fake_script():
    """run_fake_script(fake_root, script_name, *args, input=None) -> CompletedProcess

    Invokes <fake_root>/scripts/<script_name> (a copy placed there by
    fake_repo) rather than the real scripts/ copy.
    """
    def _run(fake_root, script_name, *args, input=None):
        return _run_python(fake_root / "scripts" / script_name, *args, input=input)
    return _run


@pytest.fixture
def fake_mdls_tools(tmp_path, monkeypatch):
    """fake_mdls_tools(mdls_responses, mdimport_ok=True, pdfinfo_output=None, pdfinfo_exit=0) -> Path

    Writes tiny Python-shebang fake executables for mdimport/mdls(/pdfinfo)
    into a tmp bin dir and PREPENDS it to PATH, so pdf_page_count.py's own
    subprocess.run(["mdls", ...]) calls resolve to these fakes instead of
    the real macOS tools. Uses an absolute interpreter path in the shebang
    (not `#!/usr/bin/env python3`) since PATH has been rewritten.

    mdls_responses is a list of raw `mdls -name kMDItemNumberOfPages` output
    strings (e.g. "kMDItemNumberOfPages = 3" or "kMDItemNumberOfPages = (null)"),
    consumed one per invocation via a state-counter file; the last response
    repeats if the script calls mdls more times than there are responses.
    """
    def _make(mdls_responses, mdimport_ok=True, pdfinfo_output=None, pdfinfo_exit=0):
        bin_dir = tmp_path / "fakebin"
        bin_dir.mkdir(exist_ok=True)
        py = sys.executable

        mdimport_path = bin_dir / "mdimport"
        mdimport_path.write_text(f"#!{py}\nimport sys\nsys.exit({0 if mdimport_ok else 1})\n")
        mdimport_path.chmod(0o755)

        responses_file = tmp_path / "mdls_responses.json"
        responses_file.write_text(json.dumps(mdls_responses))
        state_file = tmp_path / "mdls_state.txt"
        state_file.write_text("0")

        mdls_script = (
            f"#!{py}\n"
            "import json\n"
            "from pathlib import Path\n"
            f"responses = json.loads(Path({str(responses_file)!r}).read_text())\n"
            f"state_path = Path({str(state_file)!r})\n"
            "idx = int(state_path.read_text().strip())\n"
            "response = responses[min(idx, len(responses) - 1)]\n"
            "state_path.write_text(str(idx + 1))\n"
            "print(response)\n"
        )
        mdls_path = bin_dir / "mdls"
        mdls_path.write_text(mdls_script)
        mdls_path.chmod(0o755)

        if pdfinfo_output is not None:
            pdfinfo_script = (
                f"#!{py}\n"
                "import sys\n"
                f"print({pdfinfo_output!r})\n"
                f"sys.exit({pdfinfo_exit})\n"
            )
            pdfinfo_path = bin_dir / "pdfinfo"
            pdfinfo_path.write_text(pdfinfo_script)
            pdfinfo_path.chmod(0o755)

        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        return bin_dir

    return _make


@pytest.fixture
def roles_json_file(tmp_path):
    """roles_json_file(roles) -> Path -- writes {"roles": roles} to a tmp file."""
    def _make(roles, filename="roles.json"):
        path = tmp_path / filename
        path.write_text(json.dumps({"roles": roles}))
        return path
    return _make


@pytest.fixture
def ndjson_file(tmp_path):
    """ndjson_file(rows) -> Path -- writes one JSON object per line."""
    def _make(rows, filename="applications.ndjson"):
        path = tmp_path / filename
        lines = [json.dumps(row) for row in rows]
        path.write_text("\n".join(lines) + ("\n" if lines else ""))
        return path
    return _make


@pytest.fixture
def manifest_file(tmp_path):
    """manifest_file(job_match=None, inputs=None) -> Path -- minimal .manifest JSON."""
    def _make(job_match=None, inputs=None, filename="test.manifest"):
        path = tmp_path / filename
        data = {}
        if job_match is not None:
            data["job_match"] = job_match
        if inputs is not None:
            data["inputs"] = inputs
        path.write_text(json.dumps(data))
        return path
    return _make
