# Setting Up OpenAI Codex CLI
**Note:** Tested, but output not as good as Claude. This wrote a Swift program just to read/write PDF, while the SKILL.md file already says how to handle PDFs. The tailored resume + cover-letter had a higher job match (total only) than Claude Code, but recommended salary ask was a lower pay. The formatting was respected fully. The "total only" symptom is diagnosed and addressed in `AGENTS.md`'s "Report-template fidelity across agents" section — re-test after that change lands to see if sub-scores now come through.

## 1. Install

```bash
npm install -g @openai/codex
```
Requires Node.js 18+. Double-check the package name — the unscoped `codex` package on npm is an unrelated, older project.

macOS alternative:
```bash
brew install --cask codex
```

## 2. Sign in

Run `codex` from any directory and follow the login flow (a ChatGPT Plus/Pro/Team/Enterprise account, or an OpenAI API key). Verify the install with `codex --version`.

## 3. How it reads this repo

Start Codex from the repo root:
```bash
cd /path/to/job-os
codex
```

Codex reads `AGENTS.md` natively as the project's always-on instructions — no import needed, unlike Claude Code. It also discovers skills by scanning `.agents/skills/` from your current directory up to the repo root; this repo's `.agents/skills` symlink points at `.claude/skills/`, so every skill is visible to Codex automatically.

## 4. Try it

Codex has no slash-command syntax for this repo's skills — just ask in plain language:
```
tailor my resume for <name-of-a-job-description-file>
```
Codex matches your request against each skill's `description` and loads the matching one. See `AGENTS.md` for what each skill does.

## Notes

- Codex has its own approval/sandbox modes (e.g. auto-approve file edits, restrict network access) — configure these separately if you want fewer confirmation prompts; this repo's Claude-Code-specific `.claude/settings.json` has no effect here.
- OpenAI deprecated the older "custom prompts" mechanism (`.codex/prompts/`) in favor of Agent Skills — this repo only uses Skills, so nothing to migrate.
