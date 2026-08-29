# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Claude-Code-Specific Notes

- Permission allowlists for this repo's scripts, `Write`/`Edit` path scoping, and `WebFetch`/`WebSearch` access live in `.claude/settings.json` (and `.claude/settings.local.json` for personal overrides). These are Claude-Code-only — see AGENTS.md's "What does NOT port across tools" section for other agents.
- Claude Code discovers skills at `.claude/skills/`. The `.agents/skills` symlink alongside it exists only so other tools' neutral-path scanning finds the same skills — Claude Code doesn't need it.
