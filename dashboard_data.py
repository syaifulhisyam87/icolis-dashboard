"""Read-only normalization and counting for the ICOLIS tracking workbook."""
from io import BytesIO
import re
import pandas as pd

SHEETS = ("Full Paper", "Practice Paper", "Short Paper", "Poster")
YES = {"yes", "y", "true", "received", "submitted", "done", "paid"}
NO = {"no", "n", "false", "not received", "not submitted", "unpaid", "pending"}

def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()

def receipt(value):
    value = clean(value).casefold()
    if not value:
        return "Not recorded"
    if value in YES:
        return "Received"
    if value in NO:
        return "Not received"
    return "Check value"

def participation(value):
    value = clean(value).casefold()
    return {"attending": "Attending", "not attending": "Not attending",
            "not responding": "Not responding", "not responded": "Not responding",
            "withdrawn": "Withdrawn", "withdrawal": "Withdrawn",
            "": "Not recorded"}.get(value, "Check value")

def normalize(tabs):
    records, issues = [], []
    for name in SHEETS:
        if name not in tabs:
            raise ValueError(f"Required tab missing: {name}")
        rows = list(tabs[name])
        header_row = next((i for i, row in enumerate(rows[:30])
                           if "paper id" in [clean(v).casefold() for v in row]
                           and "paper title" in [clean(v).casefold() for v in row]), None)
        if header_row is None:
            raise ValueError(f"Cannot find Paper ID / Paper Title headers in {name}.")
        columns = {}
        for j, value in enumerate(rows[header_row]):
            # First Affiliation is the author's; a later duplicate belongs to reviewers.
            columns.setdefault(clean(value).casefold(), j)
        manuscript = "extended abs. received" if name == "Poster" else "full paper received"
        presentation = "final poster received" if name == "Poster" else "slides received"
        for required in ("paper id", "paper title", "decision", "confirm participation", manuscript, presentation):
            if required not in columns:
                raise ValueError(f"Required column '{required}' missing in {name}.")
        for row_number, row in enumerate(rows[header_row + 1:], header_row + 2):
            def get(key):
                j = columns.get(key)
                return clean(row[j]) if j is not None and j < len(row) else ""
            paper_id, title = get("paper id"), get("paper title")
            if not paper_id:
                if title:
                    issues.append(f"{name} row {row_number}: title without Paper ID; excluded from counts.")
                continue
            if not title:
                issues.append(f"{name} row {row_number}: {paper_id} has no title; included because it has an ID.")
            attend = participation(get("confirm participation"))
            decision = get("decision")
            item = {"Type": name, "Paper ID": paper_id, "Title": title,
                    "Country": get("country"), "Theme": get("themes/key areas"),
                    "Decision": decision or "Not recorded", "Participation": attend,
                    "Manuscript / abstract": receipt(get(manuscript)),
                    "Presentation": receipt(get(presentation)),
                    "Presentation field": clean(rows[header_row][columns[presentation]]),
                    "Payment": receipt(get("payment status")) if "payment status" in columns else "Not tracked",
                    "Decision notified": receipt(get("decision notification")),
                    "Source row": row_number}
            if decision.casefold().startswith("accept"):
                item["Decision group"] = "Accepted"
            elif decision.casefold().startswith("reject"):
                item["Decision group"] = "Rejected"
            elif not decision:
                item["Decision group"] = "Not recorded"
            else:
                item["Decision group"] = "Other / check"
            actions = []
            if attend in {"Not responding", "Not recorded", "Check value"}:
                actions.append("Confirm participation")
            if attend == "Attending":
                if item["Presentation"] != "Received":
                    actions.append("Follow up poster" if name == "Poster" else "Follow up slides")
                if item["Manuscript / abstract"] != "Received":
                    actions.append("Follow up extended abstract" if name == "Poster" else "Follow up manuscript")
                if item["Decision group"] in {"Not recorded", "Other / check", "Rejected"}:
                    actions.append("Check decision")
            item["Action"] = "; ".join(actions)
            for field, raw in [("Participation", get("confirm participation")),
                               ("Manuscript / abstract", get(manuscript)),
                               ("Presentation", get(presentation))]:
                if item[field] == "Check value":
                    issues.append(f"{name} row {row_number}: {field} has unrecognised value '{raw}'.")
            records.append(item)
    if not records:
        raise ValueError("No paper records were found in the four tracking tabs.")
    frame = pd.DataFrame(records)
    duplicates = frame.duplicated(["Type", "Paper ID"], keep=False)
    if duplicates.any():
        ids = ", ".join(frame.loc[duplicates, "Type"] + "/" + frame.loc[duplicates, "Paper ID"])
        raise ValueError(f"Duplicate paper IDs would distort counts. Correct these records first: {ids}")
    return frame, issues

def read_excel(data):
    import openpyxl
    workbook = openpyxl.load_workbook(BytesIO(data), data_only=True, read_only=True)
    try:
        return normalize({name: list(workbook[name].values) for name in SHEETS if name in workbook.sheetnames})
    finally:
        workbook.close()

def summary(frame):
    output = []
    for name in SHEETS:
        group = frame[frame["Type"] == name]
        attending = group[group["Participation"] == "Attending"]
        received = int((attending["Presentation"] == "Received").sum())
        output.append({"Type": name, "Submissions": len(group),
                       "Accepted": int((group["Decision group"] == "Accepted").sum()),
                       "Attending": len(attending), "Received": received,
                       "Outstanding": len(attending) - received,
                       "Completion %": round(100 * received / len(attending), 1) if len(attending) else None})
    return pd.DataFrame(output)
