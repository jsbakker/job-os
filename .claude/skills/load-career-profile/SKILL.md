---
name: load-career-profile
description: Load the applicant's static career data (template/) and stated career direction (variable-input/career-goals/) into context. Supports three modes via args -- full (default) reads every template/ file, used by /tailor-resume, /career-coach, /find-job-descriptions; full-with-side-notes reads the same plus each experience entry's Side Notes section, used by /prep-interview; sample reads only a small representative subset, used by /match-resume-style for a style preview. Internal helper skill, not for direct end-user invocation.
---

Load the applicant's career profile. Mode: $ARGUMENTS (trimmed, case-insensitive; empty or unrecognized defaults to `full`).

## Mode: full (default)

Read, in full:
1. `template/contact-info.txt`
2. `template/all-skills.md`
3. `template/education.md`
4. `template/certifications.md`
5. `template/publications.md`
6. Every file under `template/experience/` (recursively) — date ranges come from filenames (`YYYY-MM_YYYY-MM.md`); read each entry's Highlights and Key Skills sections. **Do not read or surface `# Side Notes (for context)` in this mode.**
7. Every file under `variable-input/career-goals/`

## Mode: full-with-side-notes

Everything in `full`, plus: also read each experience entry's `# Side Notes (for context)` section. Tag anything drawn from Side Notes as off-resume background wherever the calling command surfaces it — the caller owns the exact tagging language; this skill just makes the content available.

## Mode: sample

Read only:
1. `template/contact-info.txt`
2. `template/all-skills.md`
3. One or two representative (prefer most recent) `template/experience/*.md` entries — Highlights + Key Skills only, no Side Notes.

Do not read `education.md`/`certifications.md`/`publications.md`/`career-goals/` in this mode.

## After Loading

State in one line which mode ran and what was loaded, e.g. "Career profile loaded (full): 8 experience entries, all-skills.md, education.md, certifications.md, publications.md, 3 career-goals file(s)." so the caller's next step can proceed without re-reading this list.
