"""ICOLIS committee dashboard. Run: python -m streamlit run app.py"""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import streamlit as st
from dashboard_data import SHEETS, read_excel, summary
from snapshot_data import read_snapshot

st.set_page_config(page_title="ICOLIS 2026 | Committee Dashboard", page_icon="📋", layout="wide")

@st.cache_data(show_spinner=False)
def load_upload(data):
    return read_excel(data)

st.sidebar.title("ICOLIS 2026")
mode = st.sidebar.radio("Data source", ["Shared committee snapshot", "Excel preview"])
upload = None
if mode == "Excel preview":
    st.sidebar.caption("Preview only. An upload here does not change the shared committee snapshot.")
    upload = st.sidebar.file_uploader("Upload the tracking workbook", type=["xlsx"])
else:
    st.sidebar.caption("All viewers see the saved report. To update it, replace data/status.json in the private GitHub repository.")

st.title("ICOLIS 2026")
st.caption("Organising committee · Submission and presentation status")
auto = st.sidebar.toggle("Check saved report every minute", value=True, disabled=mode != "Shared committee snapshot")
if st.sidebar.button("Refresh now"):
    st.rerun()
selected_types = st.sidebar.multiselect("Paper type", list(SHEETS), default=list(SHEETS))
attendance = st.sidebar.multiselect("Participation", ["Attending", "Not attending", "Not responding", "Not recorded", "Withdrawn", "Check value"])
query = st.sidebar.text_input("Find paper ID or title")
st.sidebar.caption("Receipt totals count attending submissions only. Blank entries remain 'Not recorded'.")

@st.fragment(run_every=60 if auto and mode == "Shared committee snapshot" else None)
def dashboard():
    if mode == "Excel preview" and upload is None:
        st.info("Upload your ICOLIS tracking workbook to preview it. This does not replace the saved report shared with other viewers.")
        return
    try:
        if mode == "Shared committee snapshot":
            frame, issues, metadata = read_snapshot(Path(__file__).parent / "data" / "status.json")
            st.info("SHARED SNAPSHOT · Online report with manual data updates. It does not synchronise automatically with Google Sheets.")
            prepared = datetime.fromisoformat(metadata["prepared_at"]).astimezone(ZoneInfo("Asia/Kuala_Lumpur"))
            st.caption("Report prepared: " + prepared.strftime("%d %b %Y, %I:%M %p MYT") + " · Source status as of: " + (metadata.get("source_as_of") or "export time not recorded; verify against your latest workbook"))
        else:
            frame, issues = load_upload(upload.getvalue())
            st.warning("EXCEL SNAPSHOT — figures reflect the uploaded file, not the current Google Sheet.")
    except Exception as error:
        # Avoid displaying credentials, tokens, request URLs, or server tracebacks.
        if isinstance(error, ValueError):
            st.error(str(error))
        else:
            st.error("Cannot load the report. Ensure data/status.json is included in the deployment, or upload a valid workbook in Excel preview.")
        return
    filtered = frame[frame["Type"].isin(selected_types)].copy()
    if attendance:
        filtered = filtered[filtered["Participation"].isin(attendance)]
    if query:
        filtered = filtered[filtered["Paper ID"].str.contains(query, case=False, regex=False) | filtered["Title"].str.contains(query, case=False, regex=False)]
    st.caption(f"Showing {len(filtered)} of {len(frame)} tracked submissions · All figures below follow the sidebar filters.")
    if filtered.empty:
        st.info("No submissions match these filters.")
        return
    attending = filtered[filtered["Participation"] == "Attending"]
    oral = attending[attending["Type"] != "Poster"]
    posters = attending[attending["Type"] == "Poster"]
    slides = int((oral["Presentation"] == "Received").sum())
    poster_received = int((posters["Presentation"] == "Received").sum())
    for col, label, value in zip(st.columns(4), ["Tracked submissions", "Accepted decisions", "Attending", "Participation to confirm"],
        [len(filtered), int((filtered["Decision group"] == "Accepted").sum()), len(attending), int(filtered["Participation"].isin(["Not responding", "Not recorded", "Check value"]).sum())]):
        col.metric(label, value)
    st.subheader("Presentation readiness")
    for col, label, value in zip(st.columns(4), ["Slides received", "Posters received", "Total presentations received", "Presentations outstanding"],
        [f"{slides} / {len(oral)}", f"{poster_received} / {len(posters)}", f"{slides + poster_received} / {len(attending)}", len(attending) - slides - poster_received]):
        col.metric(label, value)
    if len(attending):
        st.progress((slides + poster_received) / len(attending), text="Received presentation files among attending submissions")
    st.caption("Slides: Full, Practice and Short Paper tabs. Posters: Final Poster Received. Outstanding includes No, blanks, and unrecognised values; it means receipt is not confirmed in the sheet.")
    table = summary(filtered)
    table = table[table["Type"].isin(selected_types)]
    st.dataframe(table, hide_index=True, width="stretch")
    a, b = st.columns(2)
    with a:
        st.subheader("Received and outstanding")
        st.bar_chart(table.set_index("Type")[["Received", "Outstanding"]], stack=True, color=["#287a64", "#d39a36"])
    with b:
        st.subheader("Participation status")
        st.bar_chart(filtered["Participation"].value_counts(), color="#375b85")
    st.subheader("Follow-up list")
    follow = filtered[filtered["Action"] != ""]
    columns = ["Type", "Paper ID", "Title", "Participation", "Presentation", "Manuscript / abstract", "Action", "Source row"]
    st.dataframe(follow[columns], hide_index=True, width="stretch")
    st.download_button("Download follow-up list (CSV)", follow[columns].to_csv(index=False).encode("utf-8-sig"), "icolis-follow-up.csv", "text/csv")
    with st.expander("Submission details and decisions"):
        st.dataframe(filtered.drop(columns=["Action"]), hide_index=True, width="stretch")
        st.download_button("Download filtered report (CSV)", filtered.to_csv(index=False).encode("utf-8-sig"), "icolis-status.csv", "text/csv")
    with st.expander("Counting rules and data checks"):
        st.write("One submission is one non-empty Paper ID within a paper type. Exact duplicate IDs within a tab stop the report. An accepted decision includes the minor and major revision categories. Attendance and acceptance are counted separately.")
        st.write("Blank receipt values mean Not recorded. Only explicit affirmative values count as received. Non-attendance, withdrawal, and non-response are excluded from presentation receipt totals and their denominators. Payment fields absent from a tab mean Not tracked; blank payments are not treated as unpaid.")
        st.write("Manuscripts use Full Paper Received for oral papers and Extended Abs. Received for posters. Author email addresses, reviewer identities, and review scores are not displayed or exported.")
        st.write("No record of historical changes is kept, so this app does not estimate submission trends or receipt dates.")
        if issues:
            for issue in issues:
                st.warning(issue)
        else:
            st.success("No duplicate IDs or unrecognised core status values detected.")

dashboard()
