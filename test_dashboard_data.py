"""Behaviour checks with synthetic data. No private workbook is required."""
import unittest
from dashboard_data import SHEETS, normalize, receipt, summary

def fixture():
    tabs = {}
    for name in SHEETS:
        m = "Extended Abs. Received" if name == "Poster" else "Full Paper Received"
        p = "Final Poster Received" if name == "Poster" else "Slides Received"
        tabs[name] = [["Preamble"], [], ["Paper ID", "Paper Title", "Decision", "Confirm Participation", m, p],
                      [name + "001", "Synthetic example", "Accept (Minor Revision)", "Attending", "Yes", "Yes"]]
    return tabs

class DashboardDataTests(unittest.TestCase):
    def test_all_tabs_and_receipt_denominator(self):
        tabs = fixture()
        tabs["Full Paper"].append(["FP002", "Excluded non-attendee", "Accept (as is)", "Not Attending", "Yes", "Yes"])
        tabs["Poster"].append(["PO002", "Unconfirmed", "Accept (as is)", "Not responding", "Yes", "Yes"])
        frame, _ = normalize(tabs)
        table = summary(frame)
        self.assertEqual(table["Submissions"].sum(), 6)
        self.assertEqual(table["Attending"].sum(), 4)
        self.assertEqual(table["Received"].sum(), 4)
        self.assertEqual(table["Outstanding"].sum(), 0)

    def test_blank_and_unrecognised_are_not_received(self):
        tabs = fixture()
        tabs["Poster"][-1][-1] = ""
        tabs["Short Paper"][-1][-1] = "email maybe"
        frame, issues = normalize(tabs)
        self.assertEqual(summary(frame)["Received"].sum(), 2)
        self.assertEqual(summary(frame)["Outstanding"].sum(), 2)
        self.assertTrue(issues)
        self.assertEqual(receipt(None), "Not recorded")
        self.assertEqual(receipt("No"), "Not received")

    def test_poster_abstract_is_not_poster_receipt(self):
        tabs = fixture()
        tabs["Poster"][-1][-1] = "No"
        frame, _ = normalize(tabs)
        poster = summary(frame).query("Type == 'Poster'").iloc[0]
        self.assertEqual(poster["Received"], 0)

    def test_column_positions_and_header_preamble(self):
        tabs = fixture()
        for name in SHEETS:
            tabs[name][2] = list(reversed(tabs[name][2]))
            tabs[name][3] = list(reversed(tabs[name][3]))
        frame, _ = normalize(tabs)
        self.assertEqual(summary(frame)["Received"].sum(), 4)

    def test_duplicate_ids_stop_counts(self):
        tabs = fixture()
        tabs["Full Paper"].append(tabs["Full Paper"][-1].copy())
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            normalize(tabs)

    def test_missing_tab_or_column_stop_counts(self):
        tabs = fixture()
        del tabs["Poster"]
        with self.assertRaisesRegex(ValueError, "tab missing"):
            normalize(tabs)
        tabs = fixture()
        tabs["Short Paper"][2][-1] = "Renamed column"
        with self.assertRaisesRegex(ValueError, "missing"):
            normalize(tabs)

    def test_decision_and_payment_are_not_inferred(self):
        tabs = fixture()
        tabs["Full Paper"][-1][2] = ""
        frame, _ = normalize(tabs)
        self.assertEqual(summary(frame)["Accepted"].sum(), 3)
        self.assertEqual(set(frame["Payment"]), {"Not tracked"})

if __name__ == "__main__":
    unittest.main()
