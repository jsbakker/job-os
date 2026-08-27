# Resume Blueprint
This file defines the visual layout of the resume. See the "Project Structure" section in the `README.md`. The operative execution instructions are in `.claude/commands/tailor-resume.md`.

## Layout
The following layout places the structured data in a visual order.

Tokens inside of a pair of curly brackets are variables. Words inside of a pair of square brackets can be instructions.
```
{applicant-name} | {applicant-title}
t: {contact-info-phone} | e: {contact-info-email} | li: {contact-info-linkedin} [use li: for LinkedIn URLs; use w: for any other web link]

{summary-section-header}
{summary-paragraph}

{skills-section-header}
{all-skills-relevant-to-job-description}

{experience-section-header}
{experience-section-item-header}
{date-range} [left-aligned]   {location} [right-aligned]
Key Skills:{key-skills}
{experience-section-item-highlights-1}
{experience-section-item-highlights-2}
{experience-section-item-highlights-3}
[etc. repeat as necessary ...]

{education-section-header}
{education-section-item-header}
{date-range} [left-aligned]   {location} [right-aligned]
{education-section-item-highlights-1}
{education-section-item-highlights-2}
[etc. repeat as necessary ...]

{certifications-section-header}
[certifications, if applicable]

{publications-section-header}
[publications, if applicable, using publication title as link text, and URL as link location]

{references-section-header}
Available upon request.
```
