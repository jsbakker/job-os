# Formatting
This file includes instructions for formatting the various sections and elements of the resume.

The following JSON stucture defines element distinctions for specific areas of the resume, and maps them to a CSS class.
```json
{
    "resume" : {
        "applicant-name": ".applicant-name",
        "applicant-title": ".applicant-title",
        "contact-info": ".contact-info",
        "summary-section-header": ".section-header",
        "summary-paragraph": ".summary-paragraph",
        "skills-section-header": ".section-header",
        "experience-section-header": ".section-header",
        "experience-section-item-header": ".section-item-header",
        "experience-section-item-date-location": ".date-location",
        "experience-section-item-highlights": "li",
        "education-section-header": ".section-header",
        "education-section-item-header": ".section-item-header",
        "education-section-item-date-location": ".date-location",
        "education-section-item-highlights": "li",
        "certifications-section-header": ".section-header",
        "publications-section-header": ".section-header",
        "references-section-header": ".section-header",
    }
}
```

The following CSS structure defines styles to be mapped to the above areas of the resume.
```css
.applicant-name {
    font-size: 14pt;
    font-weight: bold;
    color: black;
}

.applicant-title {
    font-size: 14pt;
    font-weight: normal;
    color: black;
}

.contact-info {
    font-size: 8pt;
    color: black;
    padding-top: 0px;
    margin-top: 0px;
}

.section-header {
    font-size: 11pt;
    font-weight: bold;
    color: black;
    padding-bottom: 2px;
    margin-bottom: 2px;
    text-align: center;
}

.summary-paragraph {
    text-align: justify;
}

.section-item-header {
    font-size: 9pt;
    font-weight: bold;
    color: black;
    padding-bottom: 2px;
    margin-bottom: 2px;
}

.date-location {
    display: flex;
    justify-content: space-between;
    font-size: 9pt;
    padding-top: 2px;
    margin-top: 2px;
    line-height: 1.285;
}

.job-skills-title {
    font-size: 8pt;
    font-weight: bold;
    font-style: italic;
    color: black;
    padding-top: 2px;
    margin-top: 2px;
}

.job-skills {
    font-size: 8pt;
    font-style: italic;
    color: black;
    padding-top: 2px;
    margin-top: 2px;
}

p {
    font-size: 9pt;
    padding-top: 2px;
    margin-top: 2px;
    line-height: 1.285;
}

li {
    font-size: 9pt;
    padding-top: 2px;
    margin-top: 2px;
    line-height: 1.285;
}

* {
    font-family: "Avenir Book", "Helvetica Neue", Arial, sans-serif !important;
    font-size: 9pt;
    letter-spacing: 0.05em;
}
```
