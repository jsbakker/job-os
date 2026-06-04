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
        "skills-section-header": ".section-header",
        "experience-section-header": ".section-header",
        "experience-section-item-header": ".section-item-header",
        "experience-section-item-highlights": "li",
        "education-section-header": ".section-header",
        "education-section-item-header": ".section-item-header",
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
    font-size: 18pt;
    font-weight: bold;
    color: black;
    /* border: transparent; */
}

.applicant-title {
    font-size: 18pt;
    font-weight: normal;
    color: black;
    /* border: transparent; */
}

.contact-info {
    font-size: 10pt;
    color: black;
}

.section-header {
    font-size: 12pt;
    font-weight: bold;
    color: black;
    /* border: transparent; */
}

.section-item-header {
    font-size: 10.5pt;
    font-weight: bold;
    color: black;
    /* border: transparent; */
}

.job-skills-title {
    font-size: 9pt;
    font-weight: bold;
    font-style: italic;
    color: black;
}

.job-skills {
    font-size: 9pt;
    font-style: italic;
    color: black;
}

p {
    font-size: 10pt;
}

* {
    font-family: "Avenir Book", "Helvetica Neue", Arial, sans-serif !important;
}
```
