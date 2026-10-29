"""Run with: python3 -m unittest discover -s <skill-dir>/scripts -p 'test_*.py'."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import date
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import fetch_arxiv as fetch


def feed(paper_id="2610.12345v2", total=1, published="2026-10-18T01:00:00Z"):
    return f'''<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:o="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:x="http://arxiv.org/schemas/atom">
      <o:totalResults>{total}</o:totalResults><entry>
      <id>http://arxiv.org/abs/{paper_id}</id><title>A New Benchmark</title>
      <summary>Robot agent evaluation.</summary><published>{published}</published>
      <updated>2026-10-19T01:00:00Z</updated>
      <author><name>A Researcher</name><x:affiliation>A University</x:affiliation></author>
      <category term="cs.AI"/></entry></feed>'''.encode()


class FetchTests(unittest.TestCase):
    def test_curl_preserves_binary_response(self):
        payload = b"%PDF-1.7\n\x00\xff"
        with patch.object(fetch.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, payload, b"")) as run:
            self.assertEqual(fetch.Client().get("https://arxiv.org/pdf/2610.21180v1"), payload)
        self.assertEqual(run.call_args.args[0][0], "curl")
        self.assertFalse(run.call_args.kwargs.get("shell", False))

    def test_curl_retries_final_http_response_and_honors_retry_after(self):
        def limited(command, **kwargs):
            Path(command[command.index("--dump-header") + 1]).write_text(
                "HTTP/1.1 200 Connection established\r\n\r\n"
                "HTTP/2 429\r\nRetry-After: 7\r\n\r\n")
            return subprocess.CompletedProcess(command, 22, b"", b"HTTP 429")
        calls = []
        def respond(command, **kwargs):
            calls.append(command)
            return limited(command, **kwargs) if len(calls) == 1 else subprocess.CompletedProcess(command, 0, feed(), b"")
        with patch.object(fetch.subprocess, "run", side_effect=respond) as run:
            with patch.object(fetch.time, "sleep") as sleep:
                self.assertEqual(fetch.Client().get(fetch.API), feed())
            self.assertEqual(run.call_count, 2)
            self.assertIn(7, [c.args[0] for c in sleep.call_args_list])

    def test_curl_http_404_and_long_retry_after_do_not_retry(self):
        for status, retry_after in [(404, ""), (429, "120"), (503, "Wed, 21 Oct 2026 07:28:00 GMT")]:
            with self.subTest(status=status, retry_after=retry_after):
                def respond(command, **kwargs):
                    Path(command[command.index("--dump-header") + 1]).write_text(
                        f"HTTP/2 {status}\nRetry-After: {retry_after}\n\n")
                    return subprocess.CompletedProcess(command, 22, b"", b"HTTP failure")
                with patch.object(fetch.subprocess, "run", side_effect=respond) as run:
                    with self.assertRaisesRegex(OSError, "curl exited 22"):
                        fetch.Client().get(fetch.API)
                    self.assertEqual(run.call_count, 1)

    def test_versions_and_fulltext_metadata(self):
        total, papers = fetch.parse_feed(feed())
        self.assertEqual(total, 1)
        self.assertEqual(papers[0]["id"], "2610.12345")
        self.assertEqual(papers[0]["html_url"], "https://arxiv.org/html/2610.12345v2")
        self.assertEqual(papers[0]["authors"][0]["affiliations"], ["A University"])
        event = papers[0]["release_dates"][0]
        self.assertEqual(event["source"], "arxiv_v1")
        self.assertEqual(event["url"], "https://arxiv.org/abs/2610.12345v1")
        self.assertEqual(event["timestamp"], "2026-10-18T01:00:00Z")
        self.assertEqual(fetch.normalize_id("https://arxiv.org/pdf/2610.12345v3.pdf?x=1#p2"), "2610.12345")

    def test_shanghai_query_dates(self):
        query = fetch.build_query("robotics", date(2026, 10, 18), date(2026, 10, 19))
        self.assertIn("submittedDate:[202610171600 TO 202610191559]", query)
        self.assertIn("cat:cs.RO", query)

    def test_local_screen_rejects_unrelated_query_hits(self):
        _, papers = fetch.parse_feed(feed())
        paper = papers[0]
        self.assertTrue(fetch.matches_area(paper, "robotics"))
        self.assertTrue(fetch.matches_area(paper, "agents"))
        self.assertFalse(fetch.matches_area(paper, "continual-learning"))
        paper["abstract"] = "A long\u2011horizon robot evaluation."
        self.assertTrue(fetch.matches_area(paper, "long-horizon"))

    def test_3d_cad_is_independent_of_robot_and_agent_terms(self):
        examples = [
            ("BlenderWorld", "A benchmark for 3D creation from real-world references.", ["cs.CV"]),
            ("Functional design", "An evaluation of CAD mechanisms in simulation.", ["cs.GR"]),
            ("Editable solids", "A FreeCAD testbed for parametric modelling.", ["cs.HC"]),
        ]
        for title, abstract, categories in examples:
            with self.subTest(title=title):
                paper = {"title": title, "abstract": abstract, "categories": categories}
                self.assertTrue(fetch.matches_area(paper, "3d-cad"))
                self.assertFalse(fetch.matches_area(paper, "agents"))
                self.assertFalse(fetch.matches_area(paper, "robotics"))
        for title, abstract in [
            ("CADS", "A benchmark for sequential biological screens."),
            ("3D segmentation", "An evaluation of point cloud perception."),
        ]:
            with self.subTest(title=title):
                self.assertFalse(fetch.matches_area(
                    {"title": title, "abstract": abstract, "categories": ["cs.CV"]}, "3d-cad"))

    def test_default_fetch_discovers_3d_only_paper_and_keeps_history_read_only(self):
        payload = feed().replace(b"Robot agent evaluation.", b"Blender scene creation benchmark.")
        with tempfile.TemporaryDirectory() as d:
            output = io.StringIO()
            with patch.object(fetch.Client, "get", return_value=payload), redirect_stdout(output), redirect_stderr(io.StringIO()):
                code = fetch.main(["--storage-root", d, "--until", "2026-10-19"])
            result = json.loads(Path(json.loads(output.getvalue())["index"]).read_text())
            self.assertEqual(code, 0)
            self.assertEqual(result["papers"][0]["matched_areas"], ["3d-cad"])
            self.assertFalse((Path(d) / "artifacts/benchmark-searcher/history.jsonl").exists())

    def test_error_feed_is_not_empty_success(self):
        with self.assertRaisesRegex(ValueError, "API error"):
            fetch.parse_feed(feed("https://arxiv.org/api/errors#badquery"))
        with self.assertRaises(ValueError):
            fetch.parse_feed(b"<html>Unavailable</html>")

    def run_fetch(self, root, response, extra=None):
        output = io.StringIO()
        with patch.object(fetch.Client, "get", return_value=response), redirect_stdout(output), redirect_stderr(io.StringIO()):
            code = fetch.main(["--storage-root", str(root), "--until", "2026-10-19",
                               "--areas", "robotics", "agents", "--max-pages", "1"] + (extra or []))
        summary = json.loads(output.getvalue())
        return code, json.loads(Path(summary["index"]).read_text())

    def test_live_runs_are_separate_and_history_is_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ledger = root / "artifacts/benchmark-searcher/history.jsonl"
            ledger.parent.mkdir(parents=True)
            original = json.dumps({"name": "Prior suite", "identifiers": ["arxiv:2610.12345v1"], "report": "prior.md"}) + "\n"
            ledger.write_text(original)
            code, result = self.run_fetch(root, feed())
            self.assertEqual(code, 0)
            self.assertEqual(result["since"], "2026-10-13")
            self.assertEqual(result["until"], "2026-10-19")
            self.assertEqual(len(result["papers"]), 1)  # Cross-area paper is merged.
            self.assertEqual(result["papers"][0]["matched_areas"], ["robotics", "agents"])
            self.assertEqual(result["new_candidate_ids"], [])  # v2 is not a new paper.
            self.run_fetch(root, feed())
            self.assertEqual(len(list((ledger.parent / "fetches").glob("*/index.json"))), 2)
            self.assertEqual(ledger.read_text(), original)

    def test_truncation_and_old_first_submission(self):
        with tempfile.TemporaryDirectory() as d:
            code, result = self.run_fetch(Path(d), feed(total=10, published="2025-01-01T00:00:00Z"))
            self.assertEqual(code, 1)
            self.assertTrue(result["queries"][0]["truncated"])
            self.assertEqual(result["papers"], [])  # Recent update cannot revive an old paper.

    def test_default_week_boundary_in_shanghai(self):
        for published, expected_count in [("2026-10-12T15:59:00Z", 0), ("2026-10-12T16:00:00Z", 1)]:
            with self.subTest(published=published), tempfile.TemporaryDirectory() as d:
                code, result = self.run_fetch(Path(d), feed(published=published))
                self.assertEqual(code, 0)
                self.assertEqual(len(result["papers"]), expected_count)

    def test_failure_manifest_survives_and_does_not_claim_zero_matches(self):
        with tempfile.TemporaryDirectory() as d:
            code, result = self.run_fetch(Path(d), b"<html>Failure</html>")
            self.assertEqual(code, 1)
            self.assertFalse(result["complete"])
            self.assertIn("error", result["queries"][0])
            self.assertNotIn("total_results", result["queries"][0])


if __name__ == "__main__":
    unittest.main()
