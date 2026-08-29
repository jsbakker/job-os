# Setting Up GitHub Copilot CLI
**Note:** Tested, generated tailored resume + cover-letter with expected style and formatting. However, it only have a total match score, no recommended salary asking range, and excluded experience with no explanation.

## 1. Install

```bash
npm install -g @github/copilot
```
Requires Node.js 22+ and npm 10+. Homebrew, WinGet, and a standalone install script are also available — see the [official docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli) if npm doesn't suit your setup.

## 2. Sign in

Run `copilot` from any directory. If you're not already logged in, it prompts you to run `/login` and walks you through GitHub authentication. Requires an active GitHub Copilot subscription (Pro, Pro+, Business, or Enterprise).

## 3. How it reads this repo

Start Copilot CLI from the repo root:
```bash
cd /path/to/job-os
copilot
```

Copilot CLI reads `AGENTS.md` natively (it also recognizes `CLAUDE.md`/`GEMINI.md` if present, and its own `.github/copilot-instructions.md`, but this repo only needs `AGENTS.md`). It also supports the Agent Skills format, so `.claude/skills/*/SKILL.md` is discovered automatically — no extra configuration needed.

## 4. Try it

No slash syntax for this repo's skills — ask naturally:
```
tailor my resume for <name-of-a-job-description-file>
```
Copilot CLI matches your request against each skill's description and loads the matching one. See `AGENTS.md` for the full skill list.

## Notes

- Copilot CLI has its own permission/allow-list model for file edits and shell commands, separate from this repo's Claude-Code-specific `.claude/settings.json` — configure it directly in Copilot CLI if you want fewer confirmation prompts.
- Copilot CLI also historically read Claude Code's older `.claude/commands/*.md` slash-command format directly. This repo has fully migrated to Agent Skills, so that path no longer exists here — nothing to worry about either way.
