import tempfile
import unittest
from pathlib import Path

from reproduce.run_all import aggregate, load_runs


HEADER = "run_id,timestamp_utc,workload_family,workload,server_id,kernel_release,git_commit,method,split,repetition,window_count,anomaly_count,median_ms,p95_ms,p99_ms,throughput,unsafe_proposals,veto_count,rollback_count,raw_log_sha256\n"


class ProvenancePipelineTest(unittest.TestCase):
    def test_derives_anomaly_rate_from_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.csv"
            path.write_text(HEADER + "r1,2026-09-25T00:00:00Z,web,nginx,s1,6.4.0,abc,rules,test,1,100,3,10,20,30,40,2,1,0," + 'a'*64 + '\n')
            rows = load_runs(path)
            self.assertEqual(rows[0]["anomaly_rate"], .03)
            self.assertEqual(aggregate(rows)[0]["n_runs"], 1)

    def test_rejects_duplicate_run_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.csv"
            row = "r1,2026-09-25T00:00:00Z,web,nginx,s1,6.4.0,abc,rules,test,1,100,3,10,20,30,40,2,1,0,deadbeef\n"
            path.write_text(HEADER + row + row)
            with self.assertRaisesRegex(ValueError, "unique"):
                load_runs(path)

    def test_rejects_missing_digest_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'raw.csv'
            path.write_text(HEADER.replace(',raw_log_sha256', '') +
                            'r1,t,web,nginx,s1,k,abc,rules,test,1,100,3,10,20,30,40,2,1,0\n')
            with self.assertRaisesRegex(ValueError, 'missing columns'):
                load_runs(path)

    def test_digest_validation_and_raw_file_verification(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); raw = b'actual fixture bytes'; digest = hashlib.sha256(raw).hexdigest()
            (root/digest).write_bytes(raw)
            path = root/'raw.csv'
            row = 'r1,t,web,nginx,s1,k,abc,rules,test,1,100,3,10,20,30,40,2,1,0,'
            path.write_text(HEADER + row + digest + '\n')
            load_runs(path, root)
            (root/digest).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                load_runs(path, root)
            path.write_text(HEADER + row + 'deadbeef\n')
            with self.assertRaisesRegex(ValueError, 'invalid raw-log digest'):
                load_runs(path)

    def test_separates_hardware_and_rejects_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'raw.csv'
            row = 'r1,t,web,nginx,s1,k,abc,rules,test,1,100,3,10,20,30,40,2,1,0,' + 'a'*64 + '\n'
            path.write_text(HEADER + row + row.replace('r1,', 'r2,').replace(',s1,', ',s2,'))
            self.assertEqual(len(aggregate(load_runs(path))), 2)
            path.write_text(HEADER + row.replace(',20,', ',nan,'))
            with self.assertRaisesRegex(ValueError, 'invalid p95_ms'):
                load_runs(path)


if __name__ == "__main__":
    unittest.main()
