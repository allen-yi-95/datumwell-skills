#!/usr/bin/env python3
"""Fetch GitHub discovery candidates or selected repo evidence; never write history.

Search both created and pushed dates. Neither is a verified benchmark release.
Use --repo for metadata, README and paginated Releases of selected candidates.
"""

import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlencode

from benchmark_history import find_matches, load_records
from fetch_arxiv import Client as CurlClient, LOCAL_TZ, storage_root


def search_queries(keywords, since, until):
    # A one-day discovery buffer covers UTC/Shanghai boundaries. Date eligibility
    # is decided from source evidence, never these coarse repository timestamps.
    start = since - timedelta(days=1)
    return [{"keywords": words, "date_filter": field,
             "query": f"{words} in:name,description,readme {field}:{start}..{until} fork:false archived:false"}
            for words in keywords for field in ("created", "pushed")]


def release_evidence(release, since, until):
    if release.get("draft") or not release.get("published_at"):
        return None
    stamp = datetime.fromisoformat(release["published_at"].replace("Z", "+00:00"))
    day = stamp.astimezone(LOCAL_TZ).date()
    return {"source": "github_release", "date": str(day), "timestamp": release["published_at"],
            "url": release["html_url"], "tag": release.get("tag_name"),
            "prerelease": bool(release.get("prerelease")), "in_window": since <= day <= until,
            "benchmark_introduction_verified": False}


class Client:
    def __init__(self, transport, timeout):
        self.transport, self.timeout = transport, timeout
        self.curl = CurlClient(timeout)

    def get(self, endpoint):
        if self.transport == "curl":
            payload = self.curl.get("https://api.github.com/" + endpoint)
        else:
            try:
                response = subprocess.run(["gh", "api", "--method", "GET", endpoint],
                                          capture_output=True, timeout=self.timeout)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise OSError(f"gh API request failed: {error}") from error
            if response.returncode:
                raise OSError(response.stderr.decode(errors="replace").strip())
            payload = response.stdout
        parsed = json.loads(payload)
        if isinstance(parsed, dict) and "message" in parsed and "documentation_url" in parsed:
            raise ValueError(parsed["message"])
        return payload, parsed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--until", type=date.fromisoformat, default=datetime.now(LOCAL_TZ).date())
    parser.add_argument("--since", type=date.fromisoformat)
    parser.add_argument("--query", action="append", default=[], help="Keywords only; repeat for separate queries")
    parser.add_argument("--repo", action="append", default=[], help="Selected owner/name; repeat as needed")
    parser.add_argument("--storage-root", type=Path, default=storage_root())
    parser.add_argument("--transport", choices=["gh", "curl"], default="gh")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=40)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    args.since = args.since or args.until - timedelta(days=6)
    if (args.since > args.until or args.max_pages < 1 or args.timeout < 1
            or not (args.query or args.repo)
            or any(not re.fullmatch(r"[\w.-]+/[\w.-]+", repo) for repo in args.repo)):
        parser.error("Supply --query or --repo with valid dates, pagination and owner/name")
    queries = search_queries(list(dict.fromkeys(args.query)), args.since, args.until)
    if args.dry_run:
        print(json.dumps({"queries": queries, "selected_repositories": args.repo}, indent=2))
        return 0
    base = args.storage_root.resolve() / "artifacts/benchmark-searcher"
    history, warning = load_records(base / "history.jsonl")
    fetches = base / "fetches"
    fetches.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix=datetime.now(LOCAL_TZ).strftime("%Y-%m-%d_%H%M%S-github-"), dir=fetches))
    result = {"source": "github", "transport": args.transport, "since": str(args.since),
              "until": str(args.until), "fetched_at": datetime.now(LOCAL_TZ).isoformat(),
              "warnings": [warning] if warning else [], "queries": [], "repositories": []}
    client, repositories = Client(args.transport, args.timeout), {}

    def get(endpoint, filename):
        payload, data = client.get(endpoint)
        (run / filename).write_bytes(payload)
        return data

    for number, query in enumerate(queries):
        status = {**query, "complete": False, "received": 0, "pages": []}
        result["queries"].append(status)
        try:
            for page in range(1, min(args.max_pages, 10) + 1):
                endpoint = "search/repositories?" + urlencode({"q": query["query"], "sort": "updated",
                                                             "order": "desc", "per_page": 100, "page": page})
                filename = f"search-{number + 1}-{page}.json"
                data = get(endpoint, filename)
                batch, total = data["items"], data["total_count"]
                status["total_results"] = total
                status["pages"].append({"endpoint": endpoint, "raw": filename, "count": len(batch)})
                status["received"] += len(batch)
                status["incomplete_results"] = status.get("incomplete_results", False) or bool(data.get("incomplete_results"))
                for repo in batch:
                    key = repo["full_name"].lower()
                    if key not in repositories:
                        repositories[key] = {"full_name": repo["full_name"], "url": repo["html_url"],
                                             "description": repo.get("description"), "homepage": repo.get("homepage"),
                                             "created_at": repo.get("created_at"), "pushed_at": repo.get("pushed_at"),
                                             "official_status": "unverified", "discovered_by": [],
                                             "history_matches": find_matches(history, [repo["html_url"], repo.get("homepage")])}
                    repositories[key]["discovered_by"].append({"keywords": query["keywords"], "date_filter": query["date_filter"]})
                if status["received"] >= total:
                    status["complete"] = not status["incomplete_results"]
                    break
                if not batch:
                    raise ValueError("Empty search page before advertised total")
            if not status["complete"]:
                status["coverage_limit"] = "Split query by date/keywords or extend pages; GitHub search caps at 1,000 results."
        except (OSError, ValueError, KeyError) as error:
            status["error"] = str(error)

    for number, name in enumerate(dict.fromkeys(args.repo)):
        status = {"repo": name, "complete": False, "pages": []}
        result.setdefault("repo_checks", []).append(status)
        try:
            data = get(f"repos/{name}", f"repo-{number + 1}.json")
            key = data["full_name"].lower()
            repo = repositories.setdefault(key, {"full_name": data["full_name"], "url": data["html_url"],
                                                "official_status": "unverified"})
            repo.update({"created_at": data.get("created_at"), "pushed_at": data.get("pushed_at"),
                         "homepage": data.get("homepage"), "default_branch": data.get("default_branch"),
                         "history_matches": find_matches(history, [data["html_url"], data.get("homepage")]),
                         "release_events": []})
            # README absence is separate from release-query coverage.
            try:
                get(f"repos/{name}/readme", f"readme-{number + 1}.json")
                repo["readme_snapshot"] = f"readme-{number + 1}.json"
            except (OSError, ValueError) as error:
                repo["readme_error"] = str(error)
            for page in range(1, args.max_pages + 1):
                filename = f"releases-{number + 1}-{page}.json"
                batch = get(f"repos/{name}/releases?per_page=100&page={page}", filename)
                if not isinstance(batch, list):
                    raise ValueError("Expected a release list")
                status["pages"].append(filename)
                repo["release_events"].extend(event for release in batch
                                              if (event := release_evidence(release, args.since, args.until)))
                if len(batch) < 100:
                    status["complete"] = True
                    break
            if not status["complete"]:
                status["coverage_limit"] = "Release pagination truncated; extend --max-pages."
        except (OSError, ValueError, KeyError) as error:
            status["error"] = str(error)
    result["repositories"] = list(repositories.values())
    result["complete"] = all(s["complete"] for s in result["queries"] + result.get("repo_checks", []))
    result["finished_at"] = datetime.now(LOCAL_TZ).isoformat()
    index = run / "index.json"
    index.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"index": str(index), "repositories": len(repositories), "complete": result["complete"]}))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
