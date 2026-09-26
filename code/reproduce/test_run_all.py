import tempfile
import unittest
from pathlib import Path

from reproduce.run_all import aggregate, load_runs


HEADER = "run_id,timestamp_utc,workload_family,workload,server_id,kernel_release,git_commit,method,split,repetition,window_count,anomaly_count,median_ms,p95_ms,p99_ms,throughput,unsafe_proposals,veto_count,rollback_count,raw_log_sha256\n"


class ProvenancePipelineTest(unittest.TestCase):
    def test_derives_anomaly_rate_from_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.csv"
            path.write_text(HEADER + "r1,2026-09-25T00:00:00Z,web,nginx,s1,6.4.0,abc,rules,test,1,100,3,10,20,30,40,2,1,0,deadbeef\n")
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


if __name__ == "__main__":
    unittest.main()
