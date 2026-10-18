"""Convert a fresh Excel export to the shared JSON report. No Google setup."""
import argparse
from pathlib import Path
from snapshot_data import save_snapshot

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", nargs="?", help="Path to the tracking .xlsx export")
    parser.add_argument("--as-of", default=None, help="Date/time the source was exported; leave blank if unknown")
    args = parser.parse_args()
    workbook = args.workbook or input("Path to your latest ICOLIS tracking Excel export: ")
    path = Path(workbook.strip().strip('"').strip("'"))
    as_of = args.as_of if args.as_of is not None else input("Source export date/time (e.g. 18 Oct 2026 4:30 PM MYT; Enter if unknown): ")
    destination = Path(__file__).parent / "data" / "status.json"
    try:
        count = save_snapshot(path.read_bytes(), destination, as_of)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Report not replaced: {error}") from error
    print(f"Prepared {count} paper records in {destination}")
    print("Upload this status.json to the data folder of your PRIVATE GitHub repository and commit the change.")
    print("A local Excel preview upload does not update the online shared report.")

if __name__ == "__main__":
    main()
