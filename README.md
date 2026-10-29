# Career Atlas 2027 — International Careers / Dubai

A GitHub Pages application tracker featuring international employers, searchable company profiles, saved firms, job postings, published deadlines where available, private notes and role-by-role application tracking.

**Coverage:** 177 consolidated international employers. The static package includes curated job links for reference, plus five configured official Greenhouse recruitment boards (Schonfeld, Addepar, Teneo, Guidepoint, Third Bridge). These boards do not necessarily have matching vacancies today. Most employers, including international banks and consulting firms, are not automatically monitored by this repository.

## Set up automatic updates

1. Create a public, empty repository at https://github.com/new, for example `career-watch-2027`.
2. Download and unzip `Career_Atlas_2027_GitHub_Ready_DEPLOY_FIXED.zip`. Copy *all the files inside*, including the hidden `.github` folder, into the new repository using GitHub Desktop. Commit and push to `main`.
3. Under **Settings → Pages**, select **GitHub Actions** as the source (NOT Deploy from a branch). This is required so the scheduled updater can publish its refreshed jobs without relying on a separate push-triggered deployment.
4. Under **Settings → Actions → General → Workflow permissions**, allow **Read and write permissions** and save. Ensure the repository allows Actions and the `main` branch is not blocked from updates by protection rules.
5. Open **Actions → Update official job feeds and publish site → Run workflow**. Confirm that the workflow succeeds; check `data/jobs.json` for `lastSuccessfulAt` and `sources`, and verify the Pages deployment.
6. Visit `https://YOUR_USERNAME.github.io/career-watch-2027/`. Check the Feed Health section. The scheduled workflow runs at approximately **08:17 Dubai time** (04:17 UTC) daily; GitHub may delay or disable scheduled runs.

For an *existing* GitHub repository, back up your private notes from the old site, replace the tracked project files with this package, commit, push, and manually run the workflow. Never upload the private application backup to a public repository.

## How the vacancy data works

- `config/sources.json` lists the **five** configured Greenhouse boards. The updater collects publicly advertised UAE-located roles with targeted finance, investing, research, risk and strategy keywords, and filters out clearly sales-oriented and very senior titles.
- Supported-feed postings are marked as freshly confirmed only when the source's successful check matches the recorded listing. Initially collected job links are *reference snapshots*: clicking them may show an expired application, so verify directly.
- If a feed fails, its previous records remain, flagged as unconfirmed rather than incorrectly removed. A position absent from a successfully checked feed is labelled *not in latest feed*, not definitively closed.
- Verified deadlines come only from employer-published sources. Unknown deadlines are shown as unknown. User-entered dates are personal reminders and not presented as employer deadlines.
- Filters for experience, MBA, UAE nationals, location, internships and CFA suitability are conservative indicators, not guarantees of eligibility. Always review the full employer posting.
- The website loads the public `data/jobs.json` file when opened and periodically while open. Scheduled updates only begin **after GitHub deployment**.
- Separately, the existing ChatGPT daily job-monitoring task can notify you about employers not supported by these feeds. Its alerts do **not** automatically change this site's job database.

## Privacy and portability

Application status, dates, notes, saved companies and follow-up plans are stored **locally in the browser**, not on GitHub. Export a JSON backup in **Notes** for safekeeping or importing on another browser. Browser data is not synchronised across devices.

## Project files

- `index.html`: GitHub Pages website.
- `index.template.html`, `scripts/app.js`, `scripts/build_site.py`: interface and static rebuild.
- `data/companies.json`: 177 international company records.
- `data/jobs.json`: curated and refreshed job records with feed status.
- `config/sources.json`: official job-board feeds.
- `scripts/update_jobs.py`: Greenhouse feed polling and reconciliation.
- `.github/workflows/update-jobs.yml`: scheduled GitHub Action.
- `tests/test_update.py`: regression tests.

To validate: `python -m unittest discover -s tests -v` then `python scripts/build_site.py`. Test an actual fetch with `python scripts/update_jobs.py` in an internet-enabled runtime.

## Deployment note

The workflow explicitly publishes the site using `actions/deploy-pages` on every daily run. This is important because commits pushed using GitHub Actions’ built-in `GITHUB_TOKEN` do not trigger an ordinary branch-based GitHub Pages rebuild. You do not need a personal access token or external API keys for the five current public Greenhouse boards.
