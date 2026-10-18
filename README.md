# ICOLIS 2026 — shared committee dashboard

This version runs on Streamlit Community Cloud without Google Cloud Console, service accounts or Apps Script. All committee viewers see the same saved report. It is an online dashboard with **manual data updates**, not an automatic Google Sheets connection.

## What to upload to GitHub now

Keep the GitHub repository **Private**. Upload the following files from the extracted `icolis-dashboard` folder into the repository root:

- `app.py`
- `dashboard_data.py`
- `snapshot_data.py`
- `prepare_snapshot.py`
- `requirements.txt`
- `README.md`
- The entire `data` folder, containing `status.json`

Optional: `.streamlit/config.toml` for the colour scheme, and the test files for developer verification. The dashboard works without the optional theme file. Do not upload the original Excel workbook, previous Google credentials, or any `secrets.toml` file.

The repository root must contain `app.py`; do not upload the ZIP itself. Preserve the `data/status.json` subfolder path. In GitHub, use **Add file → Upload files**, drag the listed files and the `data` folder, then **Commit changes**. If GitHub will not accept a folder, create `data/status.json` using **Add file → Create new file**, and paste the complete contents of the local `data/status.json` file.

The included first report was prepared from the original Excel attachment in this conversation. Its source export time is unknown. It is explicitly labelled as an initial snapshot; regenerate it from a fresh export before treating the figures as current.

## Deploy on Streamlit

1. Sign in at <https://share.streamlit.io/> with your GitHub account.
2. Choose **Create app** and the option for an existing GitHub app.
3. Choose your private `icolis-dashboard` repository, branch `main`, main file `app.py`.
4. Use Python **3.12** in Advanced settings. This is the version used for the execution checks.
5. No Google secrets, JSON keys, API enablement or Apps Script deployment is needed for this version.
6. Click **Deploy** and wait for the dashboard to load. Use the exact URL returned by Streamlit.
7. In **Settings → Sharing**, verify **Only specific people can view this app**. Add authorised committee viewers. The repository and app must remain private because the snapshot contains committee reporting data. The app relies on Streamlit's hosting access control; it has no separate password form.
8. Test the deployed URL using an authorised committee account and confirm that the source is **Shared committee snapshot**. Everyone sees this same saved data.
9. After the online test succeeds, you can close local PowerShell and switch off your laptop. The online dashboard runs on Streamlit's servers. Inactive Community Cloud apps can sleep and may need to wake when someone reopens the link; this is not a guaranteed always-on service.

Streamlit currently allows one private Community Cloud app at a time. If your private slot is already used, keep this reporting data private and use an approved alternative workspace or host.

## Update the report after downloading a fresh Excel export

1. Download the tracking workbook using Google Sheets **File → Download → Microsoft Excel (.xlsx)**, if your access permits downloads. You do not need access to Extensions. If download is blocked, ask the owner for a fresh exported file.
2. In Anaconda PowerShell, run:

```powershell
conda activate icolis-dashboard
cd "C:\Users\Syaiful\icolis-dashboard"
python prepare_snapshot.py
```

3. When prompted, enter the full path to that fresh `.xlsx` file. Enter its actual export date/time if known, e.g. `18 Oct 2026 4:30 PM MYT`. Leave it blank if unknown; do not enter the preparation time as though it were the source export time.
4. The command replaces the local `data/status.json` only after the data passes validation. It does not change the Excel workbook or Google Sheet.
5. In your **private** GitHub repository, open the `data` folder → **Add file → Upload files**. Upload the newly generated `status.json` and commit the change, replacing the existing file.
6. Streamlit redeploys changes from GitHub. Wait for the update to finish, then reopen or refresh the dashboard. Confirm the preparation date, source export label and expected counts before reporting to the committee.

The laptop is needed only when you choose to prepare/upload an update. It does not need to remain on for viewers to access the saved report. **Excel preview uploads are personal session previews; they do not update the shared report.**

## Run locally

You can reuse your existing Anaconda environment. Stop the old app with **Ctrl+C** before replacing the project files with this updated package. Then:

```powershell
conda activate icolis-dashboard
cd "C:\Users\Syaiful\icolis-dashboard"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No Excel upload is required for the default shared report. **Excel preview** remains available for checking another workbook without changing the shared data.

## Reporting rules

- One non-empty Paper ID within each type is one submission. Duplicate IDs within a tab stop reporting. IDs in different paper types are separate records.
- All four existing tabs are parsed: Full Paper, Practice Paper, Short Paper and Poster. Headers are found by name, not fixed column positions.
- Accepted decisions include Accept as is, Minor Revision and Major Revision. Acceptance and attendance are separate measures; blank decisions are not assumed accepted.
- Presentation receipt totals and completion denominators include **Attending** records only. Not attending, Not responding, Withdrawn and blank participation are excluded from those measures.
- Oral paper receipts use `Slides Received`; posters use `Final Poster Received`. Extended abstracts are not counted as final posters.
- Manuscript follow-up uses `Full Paper Received` for oral papers and `Extended Abs. Received` for posters.
- Blank receipt entries remain **Not recorded**; explicit No values mean **Not received**. Only recognised affirmative statuses count as received. Unexpected values are flagged.
- Outstanding means receipt has not been confirmed in the tracker, including No, blank and unrecognised entries. It does not establish whether an attachment was sent by email.
- Missing Payment Status columns mean **Not tracked**. Blank payment entries are not assumed unpaid.
- Filters apply to every displayed KPI, chart, table and download. Records are paper submissions, not unique people.
- Author emails, reviewer identities and review scores are omitted from the saved reporting file. Paper titles, IDs, country, theme and operational status fields remain for the authorised committee.

## Dates and refresh

The report shows its preparation time in Malaysia time and a separate manually supplied source export date/time. If the source export time is unknown, the dashboard says so. It never labels an unknown snapshot as the current Google Sheet.

The page can reread its saved report every minute while open; **this does not fetch Google Sheets or make the data current**. Updates reach all viewers only after `data/status.json` is replaced in GitHub and Streamlit has deployed that change. There is no background updater or historical trend database.

## Checks

```powershell
python -m unittest -v test_dashboard_data.py test_snapshot_data.py
```

See `VALIDATION.md` for completed checks and limits. Official deployment and sharing references checked 18 October 2026:

- <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy>
- <https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app>
