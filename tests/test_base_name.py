"""Tests for scripts/base_name.py.

Two subcommands, both pure string transforms:
  applicant-job        tailor-resume.md Step 0's output base name.
  company-title-slug   find-job-descriptions.md Step 7's auto-download slug.
"""


class TestApplicantJob:
    def test_matches_tailor_resume_step0_usage(self, run_script):
        # Exact invocation shape from tailor-resume.md Step 0.
        result = run_script(
            "base_name.py", "applicant-job",
            "--applicant-name", "Dana Whitfield",
            "--job-filename", "Acme_Corp_-_Senior_iOS_Developer.pdf",
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "dana-whitfield-acme-corp-senior-ios-developer"

    def test_only_last_extension_is_stripped(self, run_script):
        result = run_script(
            "base_name.py", "applicant-job",
            "--applicant-name", "Dana Whitfield",
            "--job-filename", "resume.tar.gz",
        )
        assert result.stdout.strip() == "dana-whitfield-resume-tar"

    def test_no_extension_filename(self, run_script):
        result = run_script(
            "base_name.py", "applicant-job",
            "--applicant-name", "Dana Whitfield",
            "--job-filename", "AcmeCorpRole",
        )
        assert result.stdout.strip() == "dana-whitfield-acmecorprole"

    def test_apostrophe_in_applicant_name(self, run_script):
        result = run_script(
            "base_name.py", "applicant-job",
            "--applicant-name", "O'Brien Anderson",
            "--job-filename", "role.md",
        )
        assert result.stdout.strip() == "o-brien-anderson-role"

    def test_consecutive_special_chars_collapse_and_strip(self, run_script):
        result = run_script(
            "base_name.py", "applicant-job",
            "--applicant-name", "Dana Whitfield",
            "--job-filename", "Acme!!Corp   Role???.pdf",
        )
        # Runs of punctuation/whitespace collapse to one hyphen each, and a
        # trailing run is stripped rather than left as a dangling hyphen.
        assert result.stdout.strip() == "dana-whitfield-acme-corp-role"

    def test_missing_required_arg_exits_nonzero(self, run_script):
        result = run_script("base_name.py", "applicant-job", "--applicant-name", "Dana Whitfield")
        assert result.returncode == 2

    def test_no_subcommand_exits_nonzero(self, run_script):
        result = run_script("base_name.py")
        assert result.returncode == 2


class TestCompanyTitleSlug:
    def test_matches_existing_repo_example(self, run_script):
        # Must match the real committed example file's naming exactly:
        # variable-input/job-descriptions/City-of-Vancouver-Solutions-Architect.md
        result = run_script(
            "base_name.py", "company-title-slug",
            "--company", "City of Vancouver",
            "--job-title", "Solutions Architect",
        )
        assert result.stdout.strip() == "City-of-Vancouver-Solutions-Architect"

    def test_first_word_stays_capitalized_even_if_minor_word(self, run_script):
        # "The" is in MINOR_WORDS, but the i > 0 guard means only non-first
        # occurrences get lowercased.
        result = run_script(
            "base_name.py", "company-title-slug",
            "--company", "The Big Company",
            "--job-title", "Engineer",
        )
        assert result.stdout.strip() == "The-Big-Company-Engineer"

    def test_acronym_company_name_preserved_when_already_uppercase(self, run_script):
        result = run_script(
            "base_name.py", "company-title-slug",
            "--company", "IFS",
            "--job-title", "Senior Lead Application Security Engineer",
        )
        assert result.stdout.strip() == "IFS-Senior-Lead-Application-Security-Engineer"

    def test_lowercase_acronym_is_not_magically_uppercased(self, run_script):
        # The script only force-uppercases each word's first character -- it
        # has no real acronym detection. Lowercase input does NOT come out
        # as "IFS"; this locks in that (documented) limitation so a future
        # reader doesn't "fix" this test around the wrong mental model.
        result = run_script(
            "base_name.py", "company-title-slug",
            "--company", "ifs",
            "--job-title", "Engineer",
        )
        assert result.stdout.strip() == "Ifs-Engineer"

    def test_ampersand_splits_into_separate_words(self, run_script):
        # "&" is non-alphanumeric, so "R&D" splits into two separate words
        # ("R", "D") rather than being preserved as one token.
        result = run_script(
            "base_name.py", "company-title-slug",
            "--company", "R&D Corp",
            "--job-title", "Engineer",
        )
        assert result.stdout.strip() == "R-D-Corp-Engineer"

    def test_missing_required_arg_exits_nonzero(self, run_script):
        result = run_script("base_name.py", "company-title-slug", "--company", "Acme")
        assert result.returncode == 2
