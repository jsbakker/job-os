---
name: match-resume-style
description: Regenerate formatting.md and blueprint.md to match the visual style of a reference resume, adapting anything that would hurt ATS parsing
---

Update the resume style to match this reference resume: $ARGUMENTS

*(In Claude Code, `$ARGUMENTS` is what follows `/match-resume-style` in the slash palette. In agents without slash syntax, treat this as the reference resume path the user named in their request.)*

`formatting.md` (CSS) and `blueprint.md` (section layout/order) define the one look every `/tailor-resume` run produces. By default they encode the repo owner's own hand-picked style — this command lets anyone point at a resume whose look they actually want instead, and have those two files regenerated to match it, without inheriting someone else's design. The one non-negotiable constraint: never adopt a style element that would hurt ATS parsing, even if the reference resume uses it. When a reference element is ATS-risky, adapt it to the closest safe equivalent rather than silently dropping the idea, and say exactly what was changed and why.

---

## Help Check

(This exact-match escape hatch is for Claude Code's `/match-resume-style help` slash syntax; other agents should just answer help questions about this skill conversationally using the Usage block below.)

If `$ARGUMENTS`, trimmed of whitespace, equals `help` (case-insensitive) — and only in that exact case, not as part of a real file path — print the block below and stop. Do not run any other step.

```
/match-resume-style — Regenerates formatting.md and blueprint.md to match a reference resume's visual style (colors, fonts, header treatment, spacing, section order), adapting anything that would hurt ATS parsing instead of copying it blindly.

Usage:
  /match-resume-style <path-to-reference-resume>

What it does:
  - Reads the reference resume (PDF, image, or Word doc) and visually analyzes its style: colors, font character, header treatment, spacing density, bullet style, and section order
  - Screens every extracted element against this repo's own ATS rules (the same checklist /tailor-resume enforces on every generated resume) — risky elements get adapted to a safe equivalent, not copied as-is or silently dropped
  - Shows you the proposed style and every ATS adaptation made, and waits for confirmation before writing anything
  - Renders a preview PDF using your real template/ data so you can see the actual result, not just a description
  - Updates formatting.md and blueprint.md only — never touches your template/career data or tracking history

Gotchas:
  - Can't identify an exact font family with confidence from a rendered page — it approximates with a similar, widely-supported font stack rather than guessing a specific font name
  - Structural elements that break ATS parsing (multi-column/sidebar layouts, icons, photos, decorative graphics) are never adopted outright, even if you'd prefer them — they get adapted (e.g. a sidebar's accent color carries over to section headers, but the columns don't)
  - Both files are already git-tracked, so `git checkout -- formatting.md blueprint.md` reverts to the previous style if you don't like the result

Example:
  /match-resume-style ~/Desktop/my-old-resume.pdf
```

---

## Step 1 — Resolve the Reference File

If `$ARGUMENTS`, trimmed of whitespace, is empty, ask the user directly for the path to the resume whose style they want to match — it can be anywhere on disk. Otherwise treat the entirety of `$ARGUMENTS` as the file path.

Confirm the file exists and is readable before doing anything else. If it doesn't, tell the user and stop — don't guess at a nearby filename, and don't touch `formatting.md` or `blueprint.md`.

---

## Step 2 — Get the Reference Resume Into a Viewable Form

- `.pdf`, `.png`, `.jpg`, `.jpeg` → read it directly with visual rendering. Most coding agents can render PDF/image pages visually, which is what makes visual style analysis possible here (not just text extraction).
- `.docx`, `.doc`, `.rtf` → convert to PDF first (same `textutil` tool `/import-applications` uses for Word documents), into a temp path, then read that:
  ```bash
  TMPFILE=$(mktemp -t match-resume-style).pdf
  textutil -convert pdf -output "$TMPFILE" "<path>"
  ```
  Read `$TMPFILE` with the same visual rendering, then clean it up (`rm "$TMPFILE"`) once you're done with it.
- If the file is scanned-image-only, encrypted, or otherwise yields no usable visual content, tell the user plainly and stop rather than guessing at a style from nothing.

---

## Step 3 — Extract the Style, Honestly

Look at the rendered resume and identify:

- **Colors** — accent color(s) used for the name, headers, or dividers, and body text color. An approximate hex value is fine; this isn't colorimetry.
- **Font character** — serif vs. sans-serif, weight (light/regular/bold-leaning), condensed vs. wide, any letter-spacing tendency. Do **not** claim to identify the exact font family with confidence — that's not reliably possible from a rendered page. Describe the character instead, and you'll choose a widely-supported CSS font stack with a similar feel in Step 6.
- **Header treatment** — name/title size and weight, section header style (centered vs. left-aligned, bold, all-caps, underlined, background-shaded, bordered).
- **Spacing density** — compact vs. airy line spacing and section padding.
- **Bullet symbol** — what character is actually used for highlight bullets.
- **Date-range style** — format and punctuation used (noting only for awareness; the output format is still governed by the ATS-safe rules in Step 4, which always win).
- **Section order** — the sequence of sections as they appear top to bottom.
- **Structural elements** — explicitly note anything beyond plain single-column text: multi-column or sidebar layouts, icons, a photo/headshot, tables, text boxes, decorative graphics, QR codes, etc. Do not adopt any of these yet — they're screened in Step 4.

---

## Step 4 — ATS Red-Flag Screening

Cross-check everything extracted in Step 3 against the exact ATS rules `tailor-resume/SKILL.md` Step 8 already enforces on every generated resume: no tables, text boxes, or multi-column layouts; no images or embedded graphics; plain-word section headers only; consistent, parseable dates with plain hyphens; plain bullet characters only (`•` or `-`, never a custom Unicode glyph); no photos.

For every element that conflicts with those rules, don't just drop it silently — adapt it to the closest safe equivalent and record what you did:

| Reference element | Why it's risky | Adaptation |
|---|---|---|
| Multi-column / sidebar layout | ATS parsers read left-to-right, top-to-bottom and can scramble sidebar content order | Keep single column; carry the sidebar's accent color into section headers instead |
| Icons next to contact info or section headers | Images/glyphs may not parse; some ATS engines choke on them entirely | Plain text labels only (this repo already uses `t:`/`e:`/`li:`) |
| Custom Unicode bullet glyphs (▪, ➤, ✓, etc.) | Explicitly flagged in this repo's own ATS checklist | Plain `•` or `-` |
| Photo / headshot | Already disallowed outright; also generally discouraged on resumes for bias/legal reasons in North America | Omit entirely, no substitute owed |
| Tables used for layout (e.g. a skills grid) | ATS parsers can misread table cell order or merge content unpredictably | Recreate the same information as plain flowing text or a simple comma-separated list |

Elements that are **not** ATS conflicts — adopt these directly: accent colors, all-caps or bold headers, header background shading or bottom borders (as CSS on a `<p>`/`<span>`, never an actual `<table>`), justified body text, section reordering, spacing density, font weight/size proportions.

---

## Step 5 — Confirm Before Writing

Show the user a plain-text summary before touching any file:

```
Proposed style, based on <reference file>:

  Accent color   : <hex/description>
  Font stack     : <chosen CSS font-family stack> (approximating: <serif/sans-serif, weight, character>)
  Header style   : <e.g. "centered, bold, all-caps, accent-colored">
  Spacing        : <compact/airy>
  Bullet symbol  : <• or ->
  Section order  : <e.g. "Summary, Skills, Experience, Education, Certifications, Publications, References">

ATS adaptations made (elements from the reference that couldn't be adopted as-is):
  - <element> — <why it's risky> — adapted to: <substitute>
  [or "none — nothing in the reference conflicted with ATS-safe formatting"]

Proceed with updating formatting.md and blueprint.md to this style?
```

Do not proceed to Step 6 until the user confirms, or adjusts and re-confirms.

---

## Step 6 — Write formatting.md

Keep the existing JSON element-mapping structure and every existing CSS class name exactly as they are (`tailor-resume/SKILL.md`'s HTML-class-application logic depends on those class names existing verbatim: `.applicant-name`, `.applicant-title`, `.contact-info`, `.section-header`, `.summary-paragraph`, `.section-item-header`, `.job-skills-title`, `.job-skills`, plus the bare `p`, `li`, and `*` selectors). Only the style *values* inside those rules change — colors, font-family stack, font sizes, spacing, header treatment — per the confirmed style from Step 5.

---

## Step 7 — Write blueprint.md

Keep the token/placeholder structure (`{applicant-name}`, `{summary-paragraph}`, etc.) and the single-column linear flow exactly as they are — only the section order changes, and only if the confirmed style in Step 5 reorders it from the current default.

---

## Step 8 — Render a Preview

Invoke the `load-career-profile` skill in `sample` mode to load a small representative sample of real `template/` data (contact info, all-skills, one or two experience entries — not placeholder/fake content). Build the sample resume from that data, formatted per the new `blueprint.md`, and render it through the same pipeline every tailored resume uses:

```bash
pandoc output/style-preview.md -o output/style-preview.pdf --pdf-engine=weasyprint -c output/resume-style.css
```

(Regenerate `output/resume-style.css` from the new `formatting.md` first, exactly as `/tailor-resume` Step 5 does.) Tell the user the preview PDF's path so they can actually see the result.

---

## Step 9 — Report

```
Resume style updated.

  Reference        : <path to reference resume>
  Updated          : formatting.md, blueprint.md
  Preview          : output/style-preview.pdf

ATS adaptations made:
  - <element> — <why it's risky> — adapted to: <substitute>
  [or "none"]

Future /tailor-resume runs will use this style. Both files are git-tracked —
`git checkout -- formatting.md blueprint.md` reverts to the previous style if needed.
```
