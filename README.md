# Career Atlas 2027 — International Careers / Dubai

A GitHub Pages application tracker featuring international employers, searchable company profiles, saved firms, job postings, published deadlines where available, private notes and role-by-role application tracking.

**Coverage:** 177 employer directory entries, 44 configured official recruiting feeds, and 29+ curated/feed job records as of 12 November 2026. Coverage is incomplete: several large ATS boards exceed the collector's full-scan limit; 133 employers lack a configured vacancy feed. Some employers use multiple recruiting sites: Fidelity International's main Workday feed does not cover its separate Tal.net Early Careers programmes board. A successful scan of one platform does not prove the employer has no other vacancies.

## Set up automatic updates

1. Create a public, empty repository at https://github.com/new, for example `career-watch-2027`.
2. Download and unzip `Career_Atlas_2027_GitHub_Ready_DEPLOY_FIXED.zip`. Copy *all the files inside*, including the hidden `.github` folder, into the new repository using GitHub Desktop. Commit and push to `main`.
3. Under **Settings → Pages**, select **GitHub Actions** as the source (NOT Deploy from a branch). This is required so the scheduled updater can publish its refreshed jobs without relying on a separate push-triggered deployment.
4. Under **Settings → Actions → General → Workflow permissions**, allow **Read and write permissions** and save. Ensure the repository allows Actions and the `main` branch is not blocked from updates by protection rules.
5. Open **Actions → Update official job feeds and publish site → Run workflow**. Confirm that the workflow succeeds; check `data/jobs.json` for `lastSuccessfulAt` and `sources`, and verify the Pages deployment.
6. Visit `https://YOUR_USERNAME.github.io/career-watch-2027/`. Check the Feed Health section. The scheduled workflow runs at approximately **08:17 Dubai time** (04:17 UTC) daily; GitHub may delay or disable scheduled runs.

For an *existing* GitHub repository, back up your private notes from the old site, replace the tracked project files with this package, commit, push, and manually run the workflow. Never upload the private application backup to a public repository.

## Recent-posting accuracy and platforms

- The **Added this week** filter and dashboard show jobs first added to the tracker in the previous seven days, not necessarily jobs the employer published during that period. A true employer post date is shown separately only when verified.
- The title filter excludes general commercial sales/business development but now **allows investment/institutional sales internships and sales, trading and structuring roles**.
- Fidelity International uses two platforms: the configured Workday feed and a separate <https://fidelityinternational.tal.net/vx/lang-en-GB/mobile-0/brand-5/candidate/jobboard/vacancy/1/adv/> Early Careers board. The Tal.net feed is **not automatically monitored**. The Dubai MEA Sales Internship is saved as a curated official-board link that needs manual revalidation.
- Only the configured providers can be automatically checked. Large public Workday job boards exceeding the 1,200-position full-scan limit are flagged as incomplete; new jobs at those employers can be missed until dedicated, verified integrations are added. Don't infer that zero tracked jobs means zero employer vacancies.
- The job update workflow runs on a daily schedule and when its filter/configuration data is changed on main. It can be delayed by GitHub Actions. The website may also temporarily use bundled job data while a fetch fails.

## How the vacancy data works

- `config/sources.json` lists the **five** configured Greenhouse boards. The updater collects publicly advertised UAE-located roles matching finance, investing, research, risk and strategy keywords. General commercial sales roles are excluded, but investment sales and markets programmes are retained.
- Supported-feed postings are marked as freshly confirmed only when the source's successful check matches the recorded listing. Initially collected job links are *reference snapshots*: clicking them may show an expired application, so verify directly.
- If a feed fails, its previous records remain, flagged as unconfirmed rather than incorrectly removed. A position absent from a successfully checked feed is labelled *not in latest feed*, not definitively closed.
- Verified deadlines come only from employer-published sources. Unknown deadlines are shown as unknown. User-entered dates are personal reminders and not presented as employer deadlines.
- Filters for experience, MBA, UAE nationals, location, internships and CFA suitability are conservative indicators, not guarantees of eligibility. Always review the full employer posting.
- The website loads the public `data/jobs.json` file when opened and periodically while open. Scheduled updates only begin **after GitHub deployment**.
- Separately, the existing ChatGPT daily job-monitoring task can notify you about employers not supported by these feeds. Its alerts do **not** automatically change this site's job database.

## Consulting firms and real vacancy coverage (12 November 2026)

- **32 consulting, strategy and deals employer entries** are included, including distinct **PwC Deals / PwC Consulting** and **Capgemini Invent / Capgemini** divisions. Coverage status is displayed on each firm card: **Feed checked**, **Partial coverage**, **Feed failed**, or **Not auto-monitored**.
- Among these consulting entries, **4 have successfully checked automatic feeds** (FTI Consulting, Protiviti, Roland Berger, Teneo), **2 have failed feeds** (Accenture Strategy, Booz Allen Hamilton), and **26 do not have an automatic vacancy feed**. The directory is **not a complete vacancy monitor** for the other 26.
- Curated employer-posting links have been added for PwC's 2027 Deals and Consulting summer programmes, BCG Senior Associate (Dubai), Kearney Foresight Senior Business Analyst / Associate (Dubai), Capgemini Insights & Data 2026/27 Internship (Dubai; distinct from Invent), McKinsey Business Analyst and Business Analyst Intern (multi-office listings including Abu Dhabi), and Grant Thornton Forensics Associate Consultant (Dubai). Some require *undergraduate status*, *2+ years after graduation* or *3–7 years of experience*. Their presence in the tracker does **not** verify applicant eligibility or a live application window.
- Vacancy status and published deadlines should be verified on the **specific employer posting**, not guessed from an old snapshot. All job records with a *passed recorded employer deadline* or **missing from the latest successful feed** are shown under **Archived / deadlines passed**, not in default current results. Records remain in JSON to preserve application notes and history.
- Official portal coverage is not exhaustive: some employers operate multiple candidate portals, legacy/JS-only sites cannot be fully read by the current discovery script, and very large Workday boards exceed the collector's scan limit. Search results and saved careers URLs should never be interpreted as a complete list of vacancies.
- Consulting-specific opportunities should be reviewed in the **Browse firms → Consulting & deals** filter, including firms without listed direct jobs. Clicking **View firm** opens the official recruiting portal.

## Private CV-to-job matching

- Open **Private CV matching** above the job openings list, then paste the text of your CV and select **Save locally & rate jobs**. For PDF and Word files, copy the selectable text rather than uploading the file.
- **No CV, employer history, educational history, name, email, phone, or other personal profile is committed to this public repository.** The site ships generic matching rules only.
- The CV is retained exclusively in that browser's `localStorage`. Comparisons run entirely client-side against JDs already in `data/jobs.json`; the implementation does not transmit the CV to GitHub, to an API, or to any employer.
- Scores are rule-based indicative skills/JD matches, **not application success probabilities**. The interface explains detected evidence, skills not evidenced in the CV, graduation/MBA/nationality/seniority checks, and cases where the complete JD is missing. A full JD means a recorded snapshot; verify the live employer site.
- CV scores recalculate when you revisit the site or when stored job data refreshes while the site is open. They do not run independently while your browser is closed.
- Select **Delete local CV** to erase this site's saved CV on that browser. Application-note backups do not contain the CV. Other devices and browsers require separate local CV entry.
- Treat any browser that stores your CV as private: other people or browser extensions with access to that browser profile may be able to access its local data.
- The public employer directory contains 177 companies; only vacancies for which the repository has stored full job descriptions can receive a numerical score. Not every employer is fully monitored or has a current vacancy.

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

## International insight programs, mentorships and events

- Visit `events.html` or select **Events & programs** in the main Career Atlas navigation.
- Dataset: `data/events.json`; initially researched 5 November 2026. Coverage: Hong Kong, UAE, France, Netherlands and Singapore, plus relevant cross-border virtual events.
- Each record includes organization, title, event category, regions/location, date, verified employer-published deadline if available, eligibility details, restrictions, source URL, and application status. **Open** is not the same as **eligible**: where external-campus or local residency rules are unclear, the record says so explicitly.
- Filter by country, priority, application status or keyword. Update **My progress** and personal notes; these are stored in your own browser (localStorage) rather than committed to the public repository. Use **Export my progress** for a backup; progress is not automatically synchronized across browsers.
- The source data is curated and NOT an automated scrape of all event websites. An additional ChatGPT recurring watch checks relevant employer and organizer pages, reports material changes, and attempts to update `data/events.json` using the GitHub connection when available. Do not assume a scheduled check or failed connection updated the repository; inspect the commit or the recorded last-reviewed date.
- The Pages workflow `.github/workflows/publish-events.yml` republishes the static site when event data or the events page changes. The separate daily job-feeds workflow continues monitoring vacancies. These are independent systems.
- Never invent event dates, published deadlines, or eligibility, and never infer that a Hong Kong/Singapore program accepts UOWD students merely because the degree issuer has an Australian campus. Past-cycle dates must be labeled as historical.
