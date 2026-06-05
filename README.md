# Agentic Resume Blueprint
A templated blueprint to tailor your resume to specific job descriptions. This project uses agentic AI to build a specialized version of your resume from the modularized template.


## Problem Statement
The modern job search requires tailoring a specialized resume for each individual job decription, if you don't want to be filtered out by ATS before any actual human sees your application.

Applicant Tracking Systems (ATS) can look for keywords for a role, and reject your application if your resume does not match. Even if a keyword is present, structure or formatting inconsistencies can disqualify it from being parsed correctly.

Manually tailoring your resume to optimize it for each job application can be very time-consuming - and it still may not be ATS-friendly. You can use AI to tailor your resue to a specific job description, but there will be hallucinations that need editing. In worse cases, the hallucinations can make the applicant look like a liar.


## Solution
The solution is to provide data that is the most relevant to the postion you're applying for. When you create a very detailed resume, the experience section can get too long, and you have to trade off between cutting one proud accomplishment over another.

If we provide all of the information and let AI filter out what is most relevant based on a job description, it makes the decisions a bit easier.

Why would I need this, if LinkedIn has built-in AI that already does it? I've seen what LinkedIn AI can do, and it was too flawed to feel comfortable letting it represent me on a professional level.

If we prescribe a structure, format and style, and instruct AI using agent skills, we can put our own standards and quality measures on it. We can control many elements of a resume to be deterministic.


## Requirements
- Text editor (preferably with Markdown support)
- pandoc
- weasyprint

`brew install pandoc weasyprint`


## Instructions
To generate a resume:

1. Populate your applicant information into the template as per the provided  "Project Structure" section below.
2. Populate the career goals with your intentions. See `career-goals/goals.md`.
3. Place a job descrption file in the `job-descriptions` folder. It can be markdown, plain text, or even a PDF.
4. Open Claude Code in the root folder. E.g.:
```bash
cd <path-to-repo>
claude
```
5. Pass the job description to the tailor-resume Claude skill. E.g.:
```bash
/tailor-resume <name-of-job-desctiption-file>
```
6. Review the claude output for job match and ATS validation.
7. View the output PDF in the resulting `output` folder.


## Project Structure
```
root
├─ blueprint.md
├─ CLAUDE.md
├─ formatting.md
├─ template
│  ├─ all-skills.md
│  ├─ certifications.md
│  ├─ contact-info.txt
│  ├─ education.md
│  ├─ experience/
│  |  └─ <YYYY-MM_YYYY-MM>.md
│  └─ publications.md
├─ variable-input
│  ├─ career-goals
│  └─ job-descriptions
└─ README.md
```

### .claude (hidden)
Includes settings for permissions to `output` folder, and defintions for resume-building commands.

### blueprint.md
Includes the plan for building the resume from its modularized parts.

### CLAUDE.md
Instructions for Claude Code on how to use this project. Loaded into every new session.

### formatting.md
Includes the specifics for formatting.

### template/contact-info.txt
The applicant's name, title, phone, email, and web link (typically LinkedIn). Used to populate the resume header. LinkedIn URLs are labelled `li:` in the output; other web links use `w:`.

### template/all-skills.md
Includes a high-level list of all of the applicant's skills.

### template/certifications.md
Includes a list of certifications the applicant has. Optional.

### template/education.md
Includes a list of education that the applicant has.

### template/experience/*.md
Each file describes a single entry of work history.

### template/publications.md
Includes the names and links to any written work published by the applicant. Optional.

### variable-input/career-goals/*.md
One or many career goals, combined or as standalone career paths, should be specified.

### variable-input/job-descriptions/*
Place job descrptions here. They can be markdown, plain text, or a PDF.

Using a link to an online job posting is not recommended, as some sites block robots 

### README.md
This current file.
