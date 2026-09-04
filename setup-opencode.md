# Setting Up OpenCode
**Warning:** Tested, but OpenCode does not have native PDF reading support for the job description. Converted to .md, which is what the find-job-descriptions pulls down, TBF, and continued. Taking very long, stopped giving progress indicator, but insists it is still working on it. It never finished.

OpenCode supports 75+ model providers, including running fully offline against a local Ollama model — see the dedicated section below if that's what you're after.

## 1. Install

```bash
curl -fsSL https://opencode.ai/install | bash
# you may need to run `source ~/.zshrc` after (or .bashrc for bash)
```
Alternatives: `npm install -g opencode-ai`, `brew install anomalyco/tap/opencode`, or via Bun/pnpm/Yarn — see the [official docs](https://opencode.ai/docs/) for all options.

## 2. Sign in

Run `opencode` from any directory. On first run it walks you through picking and authenticating a model provider (Anthropic, OpenAI, Google, a local Ollama server, and many others). If you want the fully offline, no-account path, skip straight to "Running fully offline with a local Ollama model" below.

## 3. How it reads this repo

Start OpenCode from the repo root:
```bash
cd /path/to/job-os
opencode
```

OpenCode reads `AGENTS.md` natively for project instructions, and discovers this repo's skills from `.claude/skills/*/SKILL.md` / `.agents/skills/` automatically — no extra configuration needed regardless of which model provider you've picked.

## 4. Try it

No slash syntax for this repo's skills — ask naturally:
```
tailor my resume for <name-of-a-job-description-file>
```

## Running fully offline with a local Ollama model

This is the genuinely no-account, no-cost path: no cloud sign-in, no API key, nothing leaves your machine.

### Step 1 — Install Ollama

macOS/Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
macOS alternative: `brew install ollama`. Windows: download the installer from [ollama.com/download](https://ollama.com/download).

Ollama runs as a background service after install. Confirm it's actually up before continuing:
```bash
ollama --version
curl http://localhost:11434
```
The `curl` should print `Ollama is running`. If it doesn't, start it manually with `ollama serve` in its own terminal.

### Step 2 — Pick a model that fits your hardware

Ollama models are free to download, but size determines whether they're actually usable — a model too large for your RAM will swap to disk or fail to load, not just run slowly. As a starting point:

| Your RAM (or GPU VRAM) | Realistic model tag |
|---|---|
| 8 GB | `qwen2.5-coder:7b` |
| 16 GB | `qwen2.5-coder:14b` |
| 32 GB+, or a dedicated GPU | `qwen2.5-coder:32b` or `qwen3-coder:30b` |

If you're unsure, start with the 7B tier — you can always pull a larger tag later once you've confirmed the basics work.

**Be honest about what a small local model can actually do here.** This repo's skills are dense, multi-step instructions written and tuned against frontier hosted models — `tailor-resume` alone is an 11-step pipeline involving structured JSON payloads and script calls. A 7B–14B local model may follow the early steps fine and then lose the thread, skip a step, or invent structure that isn't there. That's a real limitation of the model, not a bug in this repo's skills. If something goes wrong offline, try a larger model or a cloud provider before assuming a skill itself is broken.

### Step 3 — Launch OpenCode against it

**Simplest path** (Ollama 0.15+, no config file needed):
```bash
ollama launch opencode --model qwen2.5-coder:7b
```
This pulls the model if you don't already have it, and starts OpenCode pre-wired to it. Swap in whatever tag you picked in Step 2.

**If that command doesn't exist yet** (older Ollama) or you want a persistent setup instead of specifying `--model` every time, configure OpenCode manually:
```bash
ollama pull qwen2.5-coder:7b
```
Create `~/.config/opencode/opencode.json`:
```json
{
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://localhost:11434/v1" },
      "models": {
        "qwen2.5-coder:7b": {}
      }
    }
  }
}
```
Then run `opencode models ollama` to confirm the model is visible, and launch `opencode` and pick it from the model picker.

### Step 4 — Fix the context-window trap before you rely on this

Ollama defaults every model to a **4,096-token context window**, even when the model itself supports far more. This repo's skills routinely read several files in one go (career profile, job description, formatting rules) that can exceed 4,096 tokens easily — the failure mode isn't a clear error, it's silent truncation and confused output. Override it before you start relying on this setup:
```bash
OLLAMA_CONTEXT_LENGTH=32768 ollama serve
```
If Ollama is already running as a background service, stop it first, or set this variable in your OS's service-environment config so it persists across reboots (see [Ollama's FAQ](https://docs.ollama.com/faq)). 32k is a reasonable floor for this repo; raise it if your hardware allows.

### Step 5 — Verify it actually works, end to end

From the repo root, with Ollama running and the context window fixed:
```bash
opencode
```
Ask something only answerable from this repo's files, without pointing at them directly — e.g. "what does job-tracker.html do?" (answerable only from `AGENTS.md`) or "what skills are available in this repo?" If it can't answer sensibly, either it isn't reading `AGENTS.md`/`.claude/skills/` correctly (check Steps 3–4), or the model is too small to make sense of them (go back to Step 2 and size up). Confirm this works before trusting it with a real `/tailor-resume` run.

### Known gaps with this path

- `tailor-resume` and `ats-validate` need native PDF text extraction, and `match-resume-style` needs visual PDF rendering — not every local model/runtime combination supports this. If a PDF-involving step fails silently or errors oddly, this is the likely cause.
- Web search/fetch support depends on your OpenCode version and configuration, not just the model. Skills that use it (`career-coach`'s market research, `find-job-descriptions`, the salary-research part of `tailor-resume`) are written to skip that research and flag it explicitly rather than fail outright — so expect thinner output on those specific parts offline, not a hard crash.

## Notes

- OpenCode has its own separate custom-commands mechanism (`.opencode/command/*.md`, an OpenCode-specific format predating Agent Skills) — this repo doesn't use it, so no `.opencode/` directory is needed.
- OpenCode's own permission model is configured separately from anything in this repo.
