# Verification — shared-snapshot version, 18 October 2026

- Eleven parser/counting and snapshot tests passed. They cover attending-only receipt totals, unknown and blank entries, final poster vs abstract receipts, moved columns, schema failures, duplicate IDs, omission of email/reviewer fields, saved-file round trips, replacement data, and unknown export dates.
- Streamlit AppTest loaded the shared report without an Excel upload and without UI exceptions. Paper-type filtering and Excel preview also passed.
- A saved report was replaced in an isolated test project. On the next app run, received presentations changed from 44/65 to 43/65 as expected. No stale report cache prevented the update.
- The included report reconciles to the original attached Excel snapshot: 86 paper records, 65 attending, 41 slides and 3 final posters received among attending records, and 21 outstanding presentation receipts. These are original attachment test values, not a claim about the latest Google Sheet.
- The initial report says its source export date/time was not recorded. Regenerate it from a fresh export before treating it as current committee reporting.
- No original Excel workbook, author email column, reviewer identity column, Google keys, or Google connection code is packaged for deployment.
- The code was checked with Python 3.12, Streamlit 1.66.0, pandas 2.2.3 and openpyxl 3.1.5. No browser screenshot review was performed. No GitHub upload or Streamlit deployment was performed in the user's accounts.
- This version relies on the host's private-app access control. It is ready for deployment; it is not an online deployment until that has completed and the returned URL has been tested.
