"""Save reporting fields, not the original workbook, for a shared deployment."""
from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd
from dashboard_data import SHEETS, read_excel

REPORT_FIELDS = ["Type", "Paper ID", "Title", "Country", "Theme", "Decision",
                 "Participation", "Manuscript / abstract", "Presentation",
                 "Presentation field", "Payment", "Decision notified", "Source row",
                 "Decision group", "Action"]

def make_snapshot(workbook_bytes, source_as_of=""):
    frame, issues = read_excel(workbook_bytes)
    return {"format_version": 1, "prepared_at": datetime.now(timezone.utc).isoformat(),
            "source_as_of": source_as_of.strip(), "issues": issues,
            "records": frame[REPORT_FIELDS].to_dict(orient="records")}

def save_snapshot(workbook_bytes, destination, source_as_of=""):
    result = make_snapshot(workbook_bytes, source_as_of)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Validate the complete payload before replacing the shared report.
    text = json.dumps(result, ensure_ascii=False, indent=2)
    validate_snapshot(json.loads(text))
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(text + "\n", encoding="utf-8")
    temporary.replace(destination)
    return len(result["records"])

def validate_snapshot(payload):
    if not isinstance(payload, dict) or payload.get("format_version") != 1:
        raise ValueError("Unsupported shared report format. Regenerate data/status.json using prepare_snapshot.py.")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("The shared report contains no paper records.")
    if any(not isinstance(r, dict) or set(r) != set(REPORT_FIELDS) for r in records):
        raise ValueError("The shared report has missing or unexpected fields. Regenerate it from the workbook.")
    frame = pd.DataFrame(records, columns=REPORT_FIELDS)
    for field in set(REPORT_FIELDS) - {"Source row"}:
        if not frame[field].map(lambda v: isinstance(v, str)).all():
            raise ValueError(f"Invalid text field in shared report: {field}")
    if not frame["Type"].isin(SHEETS).all() or frame["Paper ID"].str.strip().eq("").any():
        raise ValueError("Invalid paper type or ID in the shared report.")
    if frame.duplicated(["Type", "Paper ID"]).any():
        raise ValueError("Duplicate paper IDs in the shared report.")
    for field in ("Presentation", "Manuscript / abstract", "Decision notified"):
        if not frame[field].isin(["Received", "Not received", "Not recorded", "Check value"]).all():
            raise ValueError(f"Invalid receipt status in shared report: {field}")
    if not frame["Participation"].isin(["Attending", "Not attending", "Not responding", "Not recorded", "Withdrawn", "Check value"]).all():
        raise ValueError("Invalid participation status in shared report.")
    if not frame["Decision group"].isin(["Accepted", "Rejected", "Not recorded", "Other / check"]).all():
        raise ValueError("Invalid decision status in shared report.")
    try:
        prepared = datetime.fromisoformat(payload["prepared_at"])
        if prepared.tzinfo is None:
            raise ValueError("Missing timezone")
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid report preparation timestamp.") from error
    if not isinstance(payload.get("source_as_of", ""), str):
        raise ValueError("Invalid source status date.")
    issues = payload.get("issues", [])
    if not isinstance(issues, list) or not all(isinstance(v, str) for v in issues):
        raise ValueError("Invalid data checks in shared report.")
    return frame, issues, {k: payload.get(k, "") for k in ("prepared_at", "source_as_of")}

def read_snapshot(path):
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Cannot read data/status.json. Include the data folder in your GitHub upload.") from error
    return validate_snapshot(payload)
