"""Tests for scripts/manifest_check.py.

manifest_check.py computes REPO_ROOT = Path(__file__).resolve().parent.parent
-- from the script file's own location on disk, not from cwd or any flag --
so these tests run against a *copy* of the script placed in a synthetic tree
built by the fake_repo fixture (see conftest.py). This fully decouples the
tests from the real checkout (which may have real personal data sitting in
variable-input/ or output/) with zero changes to the script itself.

One smoke test runs against the real repo tree, but only asserts on the
always-committed static template/ files -- variable-input/job-descriptions/
is gitignored and this checkout may have ad hoc leftover files in it, so the
smoke test deliberately does not depend on any specific job-description
filename existing.
"""
import json


def test_hash_includes_expected_file_set(fake_repo, run_fake_script):
    root = fake_repo(job_description="test-job.md")
    result = run_fake_script(root, "manifest_check.py", "hash", "--job-description", "test-job.md")
    assert result.returncode == 0
    data = json.loads(result.stdout)

    assert "blueprint.md" in data
    assert "formatting.md" in data
    assert "template/contact-info.txt" in data
    assert "template/all-skills.md" in data
    assert "template/certifications.md" in data
    assert "template/education.md" in data
    assert "template/publications.md" in data
    assert "template/experience/2020-01_2022-01.md" in data
    assert "variable-input/career-goals/goal.md" in data
    assert "variable-input/job-descriptions/test-job.md" in data
    assert "variable-input/salary-expectations.md" in data


def test_hash_excludes_salary_expectations_when_absent(fake_repo, run_fake_script):
    root = fake_repo(include_salary_expectations=False)
    result = run_fake_script(root, "manifest_check.py", "hash", "--job-description", "test-job.md")
    data = json.loads(result.stdout)
    assert "variable-input/salary-expectations.md" not in data


def test_hash_includes_multiple_experience_and_career_goals_files(fake_repo, run_fake_script):
    root = fake_repo(
        experience_files={
            "2020-01_2022-01.md": "role one\n",
            "2022-01_Ongoing.md": "role two\n",
        },
        career_goals_files={
            "goal-a.md": "goal a\n",
            "goal-b.md": "goal b\n",
        },
    )
    result = run_fake_script(root, "manifest_check.py", "hash", "--job-description", "test-job.md")
    data = json.loads(result.stdout)
    assert "template/experience/2020-01_2022-01.md" in data
    assert "template/experience/2022-01_Ongoing.md" in data
    assert "variable-input/career-goals/goal-a.md" in data
    assert "variable-input/career-goals/goal-b.md" in data


def test_hash_omits_missing_job_description_silently(fake_repo, run_fake_script):
    # compute_hashes/_hash_file skip missing files entirely rather than
    # erroring -- confirm that applies even to the job-description arg.
    root = fake_repo(job_description="test-job.md")
    result = run_fake_script(root, "manifest_check.py", "hash", "--job-description", "does-not-exist.md")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "variable-input/job-descriptions/does-not-exist.md" not in data
    assert "blueprint.md" in data  # everything else still present


def _hash(root, run_fake_script, job_description="test-job.md"):
    result = run_fake_script(root, "manifest_check.py", "hash", "--job-description", job_description)
    return json.loads(result.stdout)


def test_compare_all_match_true_when_nothing_changed(fake_repo, run_fake_script, manifest_file):
    root = fake_repo()
    current = _hash(root, run_fake_script)
    prior_manifest = manifest_file(inputs=current)

    result = run_fake_script(
        root, "manifest_check.py", "compare",
        "--job-description", "test-job.md", "--manifest", str(prior_manifest),
    )
    data = json.loads(result.stdout)
    assert data == {"all_match": True, "changed_files": [], "new_files": [], "removed_files": []}


def test_compare_detects_changed_file(fake_repo, run_fake_script, manifest_file):
    root = fake_repo()
    current = _hash(root, run_fake_script)
    prior = dict(current)
    a_key = next(iter(prior))
    prior[a_key] = "deliberately-different-hash"
    prior_manifest = manifest_file(inputs=prior)

    result = run_fake_script(
        root, "manifest_check.py", "compare",
        "--job-description", "test-job.md", "--manifest", str(prior_manifest),
    )
    data = json.loads(result.stdout)
    assert data["all_match"] is False
    assert data["changed_files"] == [a_key]
    assert data["new_files"] == []
    assert data["removed_files"] == []


def test_compare_detects_new_file(fake_repo, run_fake_script, manifest_file):
    root = fake_repo()
    current = _hash(root, run_fake_script)
    prior = dict(current)
    removed_key = next(iter(prior))
    del prior[removed_key]  # a file present now that wasn't in the prior manifest
    prior_manifest = manifest_file(inputs=prior)

    result = run_fake_script(
        root, "manifest_check.py", "compare",
        "--job-description", "test-job.md", "--manifest", str(prior_manifest),
    )
    data = json.loads(result.stdout)
    assert data["all_match"] is False
    assert data["new_files"] == [removed_key]
    assert data["changed_files"] == []
    assert data["removed_files"] == []


def test_compare_detects_removed_file(fake_repo, run_fake_script, manifest_file):
    root = fake_repo()
    current = _hash(root, run_fake_script)
    prior = dict(current)
    prior["a-file-that-no-longer-exists.md"] = "some-hash"
    prior_manifest = manifest_file(inputs=prior)

    result = run_fake_script(
        root, "manifest_check.py", "compare",
        "--job-description", "test-job.md", "--manifest", str(prior_manifest),
    )
    data = json.loads(result.stdout)
    assert data["all_match"] is False
    assert data["removed_files"] == ["a-file-that-no-longer-exists.md"]
    assert data["changed_files"] == []
    assert data["new_files"] == []


def test_compare_missing_inputs_key_treated_as_empty_prior(fake_repo, run_fake_script, manifest_file):
    root = fake_repo()
    prior_manifest = manifest_file()  # no "inputs" key at all

    result = run_fake_script(
        root, "manifest_check.py", "compare",
        "--job-description", "test-job.md", "--manifest", str(prior_manifest),
    )
    data = json.loads(result.stdout)
    # Every currently-hashed file looks "new" against an empty prior.
    assert data["all_match"] is False
    assert len(data["new_files"]) > 0
    assert data["changed_files"] == []
    assert data["removed_files"] == []


def test_hash_smoke_against_real_repo(run_script):
    # Deliberately does not depend on any specific file existing under
    # variable-input/job-descriptions/ (gitignored, may have ad hoc leftover
    # files in any given checkout) -- only asserts the always-committed
    # static template/ files are discovered correctly in a real environment.
    result = run_script("manifest_check.py", "hash", "--job-description", "smoke-test-nonexistent.md")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "template/contact-info.txt" in data
    assert "template/all-skills.md" in data
    assert "variable-input/job-descriptions/smoke-test-nonexistent.md" not in data
