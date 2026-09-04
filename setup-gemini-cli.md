# Setting Up Google Gemini CLI
**Note:** Tested, but ran out of usage limit on gemini-3.5-flash model with a free account. Changed model to gemini-3.1-flash-lite to complete the resume tailoring. Was able to tailor the resume + cover-letter, give detailed match score, and asking salary recommendation. Did not respect all of the formatting or font, left out some experience with no explanation, and resume was one page. Low quality could be due to dropping down to an even lower free model halfway through. Separately from the model-downgrade confound, `AGENTS.md`'s "Report-template fidelity across agents" section diagnoses and addresses a real, model-independent cause of vague/generic sub-score rationale on Gemini CLI specifically — worth re-testing on a consistent model after that change to isolate which issue was which.

## 1. Install

```bash
npm install -g @google/gemini-cli
```
Requires Node.js 18+. To try it without installing: `npx @google/gemini-cli`.

## 2. Sign in

Run `gemini` from any directory and sign in with a Google account, or configure a Google AI Studio API key / Vertex AI token. As of mid-2026, Google moved free-tier access to a separate closed-source "Antigravity CLI" — continued use of the open-source Gemini CLI needs a paid AI Studio key or Vertex AI token. Check the [official docs](https://geminicli.com/docs/get-started/installation/) if `gemini` reports no available access.

## 3. How it reads this repo

Start Gemini CLI from the repo root:
```bash
cd /path/to/job-os
gemini
```

Then sign in with either google, or use your Gemini API key, which can be generated at [Google AI Studio](aistudio.google.com).

Gemini CLI reads `AGENTS.md` natively. It also supports the Agent Skills format this repo's `.claude/skills/*/SKILL.md` files use — **Agent Skills support landed in Gemini CLI around January 2026**, so if skills aren't being picked up, run `gemini --version` and update (`npm install -g @google/gemini-cli@latest`) before assuming something else is wrong.

## 4. Try it

No slash syntax for this repo's skills — ask naturally:
```
tailor my resume for <name-of-a-job-description-file>
```
Gemini CLI injects the name and description of every discovered skill into its system prompt and calls the matching one automatically. See `AGENTS.md` for the full skill list.

## Notes

- Gemini CLI has its own separate custom-commands mechanism (`.gemini/commands/*.toml`) predating Agent Skills — this repo doesn't use it, so no `.gemini/` directory is needed.
- Gemini CLI's own approval/sandboxing settings are configured separately from anything in this repo.
