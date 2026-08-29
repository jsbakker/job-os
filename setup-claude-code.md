# Setting Up Claude Code
**Note:** Claude Code is the recommended Agentic AI to use with Job OS. It is the most tested, has the best results, and Job OS commands/skills were made with Claude Code first, using its builtin capabilities.

## 1. Install

macOS/Linux:
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows (PowerShell):
```powershell
irm https://claude.ai/install.ps1 | iex
```

This is Anthropic's standalone installer — no Node.js required. (An `npm install -g @anthropic-ai/claude-code` method also exists but is deprecated in favor of the installer above.)

## 2. Sign in

You need a Claude Pro, Max, Teams, Enterprise, or Console (API) account — the free claude.ai plan does not include Claude Code access. Run `claude` from any directory and follow the login prompt once.

## 3. How it reads this repo

Start a session from the repo root:
```bash
cd /path/to/job-os
claude
```

Claude Code automatically loads `CLAUDE.md` at the start of every session. That file contains a single `@AGENTS.md` import, so all of this repo's shared instructions in `AGENTS.md` load too. Skills are auto-discovered from `.claude/skills/*/SKILL.md` — nothing to configure.

## 4. Try it

```
/tailor-resume <name-of-a-job-description-file>
```

See `AGENTS.md` for the full list of skills (`/find-job-descriptions`, `/applied`, `/career-coach`, etc.).

## Notes

- If you're repeatedly prompted for permission to read/write files or run scripts, press Shift+Tab to cycle to Auto Mode — this repo's `.claude/settings.json` pre-allowlists its own scripts, but broader actions may still prompt depending on your mode.
- Permission allowlists (`.claude/settings.json`, `.claude/settings.local.json`) are Claude-Code-specific and don't carry over to the other tools listed in `AGENTS.md`.
