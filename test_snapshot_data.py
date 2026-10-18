import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dashboard_data import normalize
from test_dashboard_data import fixture
from snapshot_data import make_snapshot, save_snapshot, read_snapshot, validate_snapshot, REPORT_FIELDS

class SnapshotTests(unittest.TestCase):
    def payload(self):
        frame, issues = normalize(fixture())
        frame['Email'] = 'private@example.invalid'
        frame['Reviewer Name'] = 'Private Reviewer'
        with patch('snapshot_data.read_excel', return_value=(frame, issues)):
            return make_snapshot(b'synthetic', '18 Oct 2026 4 PM MYT')

    def test_private_source_fields_are_omitted(self):
        payload = self.payload()
        self.assertEqual(set(payload['records'][0]), set(REPORT_FIELDS))
        self.assertNotIn('private@example.invalid', str(payload))
        self.assertNotIn('Private Reviewer', str(payload))

    def test_saved_report_is_shared_and_replacement_is_read(self):
        frame, issues = normalize(fixture())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'data'/'status.json'
            with patch('snapshot_data.read_excel', return_value=(frame, issues)):
                save_snapshot(b'synthetic', path, 'first export')
            first, _, metadata = read_snapshot(path)
            self.assertEqual(len(first), 4)
            self.assertEqual(metadata['source_as_of'], 'first export')
            changed = frame.copy()
            changed.loc[0, 'Presentation'] = 'Not received'
            with patch('snapshot_data.read_excel', return_value=(changed, issues)):
                save_snapshot(b'synthetic', path, 'second export')
            second, _, metadata = read_snapshot(path)
            self.assertEqual(second.iloc[0]['Presentation'], 'Not received')
            self.assertEqual(metadata['source_as_of'], 'second export')

    def test_unknown_export_date_stays_unknown(self):
        p = self.payload()
        p['source_as_of'] = ''
        self.assertEqual(validate_snapshot(p)[2]['source_as_of'], '')

    def test_incomplete_or_duplicate_data_is_rejected(self):
        p = self.payload()
        p['records'].append(copy.deepcopy(p['records'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_snapshot(p)
        p = self.payload()
        del p['records'][0]['Presentation']
        with self.assertRaisesRegex(ValueError, 'missing or unexpected'):
            validate_snapshot(p)
        p = self.payload()
        p['prepared_at'] = '2026-10-18T16:00:00'
        with self.assertRaisesRegex(ValueError, 'timestamp'):
            validate_snapshot(p)

if __name__ == '__main__':
    unittest.main()
