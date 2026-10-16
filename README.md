# Vadym Pyrozhenko — professional CV

**Website:** https://cloudopsmaster.github.io/cv/  
**Resume:** https://cloudopsmaster.github.io/cv/Vadym_Pyrozhenko_CV.pdf

A static, accessible professional CV with detailed career information and a separate two-page A4 resume. No backend, runtime APIs, analytics, paid services or remotely loaded fonts.

## Content and source

- `data/profile.json`: candidate information, contacts, dates, detailed website content and selected PDF content. Edit professional information here.
- `templates/index.html`: semantic page structure.
- `site/styles.css`, `site/app.js`: responsive design, navigation and optional motion.
- `site/assets`: authentic portrait, self-hosted Inter font and its license, favicon and generated social card.
- `scripts/build.py`: generates the website, metadata, sitemap, robots file and social image.
- `scripts/build_pdf.py`: generates the resume with embedded Bitstream Vera fonts supplied by ReportLab.
- `scripts/validate.py`: checks content consistency, local links, two A4 pages, PDF links and embedded fonts.
- `scripts/check_browser.cjs`: browser, accessibility and responsive QA at 360, 390, 768, 1024 and 1440 pixels.

Website detail and PDF brevity are intentionally different. Employment dates and contact details are shared. Current positioning and experience indicators were supplied by the owner; actual employment titles and dates remain unchanged. See `CONTENT_REVIEW.md` for the factual boundary.

## Local build and review

Requires Python 3.11+ and Node 22 for browser QA.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build.py
.venv/bin/python scripts/validate.py
npm ci --ignore-scripts
npx playwright install chromium
npm run test:browser
python3 -m http.server 8000 --directory site
```

Open http://localhost:8000/. Opening `site/index.html` directly also shows the CV. Browser QA saves full-page screenshots and its report under `qa/`.

## GitHub Pages

GitHub Actions builds from `data/profile.json`, validates the generated content and resume, and runs Chromium/axe checks. Only a passing main-branch build can publish the `site/` artifact. Pull requests run the same checks without deploying. Pages uses GitHub Actions as its build source.

`site/build-info.json` records the deployed source commit. The Pages artifact contains only the static website, its assets and the resume. Build tools and source data are not served as website files.

PipeForge was reviewed as an option. Native GitHub Actions directly expresses this small build/validate/deploy sequence, so no additional pipeline framework or runtime bootstrap is required.

Font licenses: Inter is self-hosted under the SIL Open Font License (`site/assets/Inter-LICENSE.txt`). The PDF embeds ReportLab's bundled Bitstream Vera TrueType fonts under their bundled license.
