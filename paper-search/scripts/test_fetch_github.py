"""Behavioral checks for discovery dates, source provenance and legacy identity matching."""

from contextlib import redirect_stdout
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import benchmark_history as history
import fetch_github as fetch


def repository():
    return {"full_name": "Team/Exam", "html_url": "https://github.com/Team/Exam",
            "homepage": "https://exam.example/", "created_at": "2025-01-01T00:00:00Z",
            "pushed_at": "2026-10-19T00:00:00Z", "default_branch": "main"}


class IdentityTests(unittest.TestCase):
    def test_legacy_and_cross_source_identities_preserve_dates(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "history.jsonl"
            original = json.dumps({"name": "Exam", "first_release": "2026-09-01",
                                   "identifiers": ["arxiv:2610.12345", "repo:TEAM/Exam"],
                                   "canonical_urls": ["https://exam.example/"]}) + "\n"
            path.write_text(original)
            records, warning = history.load_records(path)
            self.assertIsNone(warning)
            for value in ["https://arxiv.org/pdf/2610.12345v3.pdf?x=1#p2",
                          "https://github.com/team/exam/releases/tag/v2",
                          "https://github.com/team/exam.git",
                          "https://exam.example/?utm_source=search#results"]:
                self.assertEqual(history.find_matches(records, [value])[0]["name"], "Exam")
            self.assertEqual(path.read_text(), original)
            self.assertEqual(records[0]["first_release"], "2026-09-01")

    def test_distinct_site_queries_and_unrelated_repos_do_not_collide(self):
        records = [{"name": "Suite A", "canonical_urls": ["https://lab.example/view?id=A"],
                    "identifiers": ["repo:team/suite-a", "doi:10.1234/example"]}]
        self.assertEqual(history.find_matches(records, ["https://lab.example/view?id=B"]), [])
        self.assertEqual(history.find_matches(records, ["https://github.com/team/suite-b"]), [])
        self.assertTrue(history.find_matches(records, ["https://doi.org/10.1234/EXAMPLE"]))

    def test_broken_history_does_not_silently_disable_deduplication(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "history.jsonl"
            path.write_text("not json\n")
            with self.assertRaises(ValueError):
                history.load_records(path)


class GitHubTests(unittest.TestCase):
    def invoke(self, root, responder, arguments):
        def get(endpoint):
            data = responder(endpoint)
            return json.dumps(data).encode(), data
        output = io.StringIO()
        with patch.object(fetch.Client, "get", side_effect=get), redirect_stdout(output):
            code = fetch.main(["--until", "2026-10-20", "--storage-root", str(root),
                               "--max-pages", "1"] + arguments)
        return code, json.loads(Path(json.loads(output.getvalue())["index"]).read_text())

    def test_both_search_routes_find_old_repos_without_claiming_new_release(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ledger = root / "artifacts/benchmark-searcher/history.jsonl"
            ledger.parent.mkdir(parents=True)
            original = json.dumps({"name": "Reported Exam", "canonical_urls": ["https://github.com/team/exam"]}) + "\n"
            ledger.write_text(original)
            code, result = self.invoke(root, lambda _: {"items": [repository()], "total_count": 1,
                                                       "incomplete_results": False}, ["--query", "embodied exam"])
            self.assertEqual(code, 0)
            self.assertEqual({q["date_filter"] for q in result["queries"]}, {"created", "pushed"})
            self.assertEqual(len(result["repositories"]), 1)
            repo = result["repositories"][0]
            self.assertEqual(repo["official_status"], "unverified")
            self.assertNotIn("first_release", repo)
            self.assertEqual(repo["history_matches"][0]["name"], "Reported Exam")
            self.assertEqual(ledger.read_text(), original)

    def test_releases_keep_published_time_prerelease_and_shanghai_date(self):
        release = {"draft": False, "prerelease": True, "tag_name": "v1-rc",
                   "created_at": "2025-01-01T00:00:00Z", "published_at": "2026-10-13T16:01:00Z",
                   "html_url": "https://github.com/team/exam/releases/tag/v1-rc"}
        event = fetch.release_evidence(release, date(2026, 10, 14), date(2026, 10, 20))
        self.assertEqual(event["date"], "2026-10-14")
        self.assertTrue(event["in_window"])
        self.assertTrue(event["prerelease"])
        self.assertFalse(event["benchmark_introduction_verified"])
        self.assertIsNone(fetch.release_evidence({**release, "draft": True}, date.min, date.max))
        self.assertFalse(fetch.release_evidence({**release, "published_at": "2026-10-13T15:59:00Z"},
                                               date(2026, 10, 14), date(2026, 10, 20))["in_window"])

    def test_empty_release_list_is_successful_evidence_fetch_not_disqualification(self):
        def respond(endpoint):
            if "/releases?" in endpoint:
                return []
            if endpoint.endswith("/readme"):
                return {"encoding": "base64", "content": "TmV3IGJlbmNobWFyay4="}
            return repository()
        with tempfile.TemporaryDirectory() as d:
            code, result = self.invoke(Path(d), respond, ["--repo", "Team/Exam"])
            self.assertEqual(code, 0)
            repo = result["repositories"][0]
            self.assertEqual(repo["release_events"], [])
            self.assertEqual(repo["official_status"], "unverified")
            self.assertIn("readme_snapshot", repo)

    def test_caps_api_incomplete_and_errors_remain_visible(self):
        for data in [{"items": [repository()] * 100, "total_count": 101},
                     {"items": [repository()], "total_count": 1, "incomplete_results": True}]:
            with self.subTest(data=data.get("incomplete_results")), tempfile.TemporaryDirectory() as d:
                code, result = self.invoke(Path(d), lambda _: data, ["--query", "exam"])
                self.assertEqual(code, 1)
                self.assertFalse(result["complete"])
                self.assertIn("coverage_limit", result["queries"][0])
        def fail(_):
            raise OSError("rate limit")
        with tempfile.TemporaryDirectory() as d:
            code, result = self.invoke(Path(d), fail, ["--query", "exam"])
            self.assertEqual(code, 1)
            self.assertIn("error", result["queries"][0])
            self.assertNotIn("total_results", result["queries"][0])


if __name__ == "__main__":
    unittest.main()
