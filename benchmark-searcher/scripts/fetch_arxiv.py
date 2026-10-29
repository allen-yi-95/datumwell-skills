#!/usr/bin/env python3
"""Fetch fresh arXiv benchmark candidates using curl; no model scoring.

Every invocation makes live API requests (except --dry-run). Raw Atom pages and
an index go under artifacts/benchmark-searcher/fetches/. Never writes the ledger.
API reference: https://info.arxiv.org/help/api/user-manual.html
Rate limits: https://info.arxiv.org/help/api/tou.html
"""

import argparse
from datetime import date, datetime, time as day_time, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from benchmark_history import load_records


AREAS = {
    "robotics": {
        "categories": ["cs.RO", "cs.AI", "cs.CV", "cs.LG"],
        "terms": ["robot", "robotics", "embodied", "manipulation", "navigation", "VLA"],
    },
    "agents": {
        "categories": ["cs.AI", "cs.CL", "cs.MA", "cs.SE", "cs.HC"],
        "terms": ["agent", "agents", "tool use", "computer use", "browser", "agentic"],
    },
    "long-horizon": {
        "categories": ["cs.AI", "cs.RO", "cs.CL", "cs.LG", "cs.SE"],
        "terms": ["long-horizon", "long horizon", "long-running", "multi-step", "persistent", "workflow"],
    },
    "continual-learning": {
        "categories": ["cs.LG", "cs.AI", "cs.RO", "cs.CL", "cs.CV"],
        "terms": ["continual learning", "lifelong learning", "online adaptation", "forgetting", "sequential learning", "continual"],
    },
    "personalization": {
        "categories": ["cs.CL", "cs.AI", "cs.IR", "cs.HC", "cs.LG"],
        "terms": ["personalization", "personalisation", "personalized", "personalised", "user preference", "personal memory", "user profile"],
    },
    "3d-cad": {
        "categories": ["cs.GR", "cs.CV", "cs.AI", "cs.HC", "cs.LG", "cs.SE", "cs.RO", "cs.CL"],
        "terms": ["Blender", "CAD", "computer-aided design", "FreeCAD", "OpenSCAD", "CADQuery",
                  "Fusion 360", "3D creation", "3D modeling", "3D modelling", "3D generation",
                  "3D editing", "3D design", "3D asset", "scene creation", "scene editing",
                  "parametric modeling", "parametric modelling", "solid modeling", "solid modelling",
                  "procedural modeling", "procedural modelling", "mesh generation", "text-to-mesh",
                  "text-to-CAD", "image-to-CAD", "B-rep", "assembly design", "mechanism design"],
    },
}
NS = {"a": "http://www.w3.org/2005/Atom", "o": "http://a9.com/-/spec/opensearch/1.1/",
      "x": "http://arxiv.org/schemas/atom"}
LOCAL_TZ = ZoneInfo("Asia/Shanghai")
API = "https://export.arxiv.org/api/query"


def normalize_id(value):
    value = value.strip().removeprefix("arxiv:")
    value = re.sub(r"^https?://(?:export\.)?arxiv\.org/(?:abs|pdf|html)/", "", value)
    return re.sub(r"v\d+$", "", value.split("?")[0].split("#")[0].removesuffix(".pdf"))


def text_terms(terms):
    return "(" + " OR ".join(f'{field}:"{term}"' for term in terms for field in ("ti", "abs")) + ")"


def matches_area(paper, area):
    """Recheck API query predicates locally; keyword matches still need review."""
    text = re.sub(r"[-\u2010-\u2015]", " ", paper["title"] + " " + paper["abstract"]).lower()
    def contains(term):
        phrase = re.sub(r"[-\u2010-\u2015]", " ", term).lower()
        return re.search(r"\b" + re.escape(phrase).replace(r"\ ", r"\s+") + r"\b", text) is not None
    return (bool(set(paper["categories"]) & set(AREAS[area]["categories"]))
            and any(contains(t) for t in ["benchmark", "benchmarks", "evaluation", "testbed"])
            and any(contains(t) for t in AREAS[area]["terms"]))


def build_query(area, since, until):
    config = AREAS[area]
    categories = "(" + " OR ".join("cat:" + c for c in config["categories"]) + ")"
    start = datetime.combine(since, day_time.min, LOCAL_TZ).astimezone(timezone.utc)
    end = datetime.combine(until, day_time(23, 59), LOCAL_TZ).astimezone(timezone.utc)
    dates = f"submittedDate:[{start:%Y%m%d%H%M} TO {end:%Y%m%d%H%M}]"
    evaluation = text_terms(["benchmark", "benchmarks", "evaluation", "testbed"])
    return f"{categories} AND {dates} AND {evaluation} AND {text_terms(config['terms'])}"


def parse_feed(payload):
    root = ET.fromstring(payload)
    if root.tag != "{" + NS["a"] + "}feed":
        raise ValueError("Expected an Atom feed, not an HTML/error response")
    total = int(root.findtext("o:totalResults", default="0", namespaces=NS))
    records = []
    for entry in root.findall("a:entry", NS):
        def get(path):
            return " ".join(entry.findtext(path, default="", namespaces=NS).split())
        raw_id = get("a:id")
        if "/api/errors" in raw_id or get("a:title").lower() == "error":
            raise ValueError("arXiv API error: " + get("a:summary"))
        versioned = raw_id.rsplit("/abs/", 1)[-1]
        paper_id = normalize_id(raw_id)
        if not re.fullmatch(r"(?:\d{4}\.\d{4,5}|[a-zA-Z-]+(?:\.[A-Z]{2})?/\d{7})", paper_id):
            raise ValueError(f"Invalid arXiv ID: {raw_id}")
        published, updated = get("a:published"), get("a:updated")
        datetime.fromisoformat(published.replace("Z", "+00:00"))
        records.append({
            "id": paper_id, "versioned_id": versioned, "title": get("a:title"),
            "abstract": get("a:summary"), "published": published, "updated": updated,
            "authors": [{"name": " ".join(author.findtext("a:name", default="", namespaces=NS).split()),
                         "affiliations": [" ".join((n.text or "").split()) for n in author.findall("x:affiliation", NS)]}
                        for author in entry.findall("a:author", NS)],
            "categories": [n.attrib["term"] for n in entry.findall("a:category", NS)],
            "url": f"https://arxiv.org/abs/{paper_id}",
            "html_url": f"https://arxiv.org/html/{versioned}",
            "pdf_url": f"https://arxiv.org/pdf/{versioned}",
            "release_dates": [{"source": "arxiv_v1", "event": "paper_submission",
                               "date": str(datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(LOCAL_TZ).date()),
                               "timestamp": published, "url": f"https://arxiv.org/abs/{paper_id}v1",
                               "verified": True}],
        })
    return total, records


def load_history(path):
    records, warning = load_records(path)
    identifiers = {}
    for item in records:
        values = [v for v in item.get("identifiers", []) if v.startswith("arxiv:")]
        values += [v for v in item.get("canonical_urls", []) if re.match(r"https?://(?:export\.)?arxiv\.org/", v)]
        for value in set(map(normalize_id, values)):
            identifiers.setdefault(value, []).append({"name": item["name"], "report": item.get("report")})
    return identifiers, warning


class Client:
    def __init__(self, timeout=30):
        self.last_request = None
        self.timeout = timeout

    def get(self, url):
        # Single connection; at least 3 seconds between starts, including retries.
        for attempt in range(2):
            if self.last_request is not None:
                time.sleep(max(0, 3.1 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            # Pass arguments directly, without a shell. Keep headers separate
            # from the raw response bytes so Atom, HTML and PDF all work.
            with tempfile.TemporaryDirectory(prefix="arxiv-curl-") as directory:
                headers_path = Path(directory) / "headers.txt"
                try:
                    response = subprocess.run([
                        "curl", "--disable", "--fail", "--silent", "--show-error",
                        "--location", "--compressed", "--proto", "=https",
                        "--proto-redir", "=https", "--max-time", str(self.timeout),
                        "--user-agent", "benchmark-searcher/1.0 (personal research; curl)",
                        "--header", "Cache-Control: no-cache",
                        "--dump-header", str(headers_path), "--url", url,
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=self.timeout + 5)
                except subprocess.TimeoutExpired as error:
                    if attempt:
                        raise OSError("curl exceeded the request timeout") from error
                    continue
                headers = headers_path.read_text(errors="replace") if headers_path.exists() else ""
            if response.returncode == 0:
                return response.stdout
            message = response.stderr.decode(errors="replace").strip()
            error = OSError(f"curl exited {response.returncode}: {message}")
            if response.returncode == 22:
                # Only the final response determines retry eligibility, not an
                # earlier redirect or proxy's connection response.
                blocks = re.split(r"\r?\n\r?\n", headers.strip())
                final_headers = next((b for b in reversed(blocks) if b.startswith("HTTP/")), "")
                status = re.match(r"HTTP/\S+\s+(\d{3})", final_headers)
                if attempt or not status or int(status[1]) not in (429, 500, 502, 503, 504):
                    raise error
                retry = re.search(r"^Retry-After:\s*(.*?)\s*$", final_headers, re.I | re.M)
                retry_after = retry[1] if retry else ""
                # Do not retry sooner than requested; long/date-form waits stop here.
                if retry_after and (not retry_after.isdigit() or int(retry_after) > 60):
                    raise error
                time.sleep(max(3.1, int(retry_after or "0")))
            elif attempt or response.returncode not in (5, 6, 7, 18, 28, 35, 52, 55, 56):
                raise error


def storage_root():
    return Path.cwd()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--until", type=date.fromisoformat, default=datetime.now(LOCAL_TZ).date())
    parser.add_argument("--since", type=date.fromisoformat, help="Default: 7 calendar days including --until (Asia/Shanghai)")
    parser.add_argument("--areas", nargs="+", choices=list(AREAS), default=list(AREAS))
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=3, help="Per area; truncation is recorded, never hidden")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--storage-root", type=Path, default=storage_root())
    parser.add_argument("--dry-run", action="store_true", help="Print queries only; no fetch or files")
    args = parser.parse_args(argv)
    args.since = args.since or args.until - timedelta(days=6)
    if args.since > args.until or not 1 <= args.page_size <= 2000 or args.max_pages < 1 or args.timeout <= 0:
        parser.error("Invalid date range, page size, page limit, or timeout")
    areas = list(dict.fromkeys(args.areas))
    queries = {area: build_query(area, args.since, args.until) for area in areas}
    if args.dry_run:
        print(json.dumps(queries, indent=2))
        return 0
    report_dir = args.storage_root.resolve() / "artifacts/benchmark-searcher"
    history_path = report_dir / "history.jsonl"
    history, warning = load_history(history_path)
    fetch_dir = report_dir / "fetches"
    fetch_dir.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=datetime.now(LOCAL_TZ).strftime("%Y-%m-%d_%H%M%S-"), dir=fetch_dir))
    result = {"fetched_at": datetime.now(LOCAL_TZ).isoformat(), "source": API, "transport": "curl",
              "since": str(args.since), "until": str(args.until), "history": str(history_path),
              "warnings": [warning] if warning else [], "queries": [], "papers": []}
    papers = {}
    client = Client(args.timeout)
    for area, query in queries.items():
        status = {"area": area, "query": query, "pages": [], "received": 0, "filtered_out": 0, "complete": False}
        result["queries"].append(status)
        try:
            for page in range(args.max_pages):
                params = {"search_query": query, "start": page * args.page_size, "max_results": args.page_size,
                          "sortBy": "submittedDate", "sortOrder": "descending"}
                url = API + "?" + urlencode(params)
                payload = client.get(url)
                raw_path = run_dir / f"{area}-{page + 1}.xml"
                raw_path.write_bytes(payload)
                total, batch = parse_feed(payload)
                status["total_results"] = total
                status["received"] += len(batch)
                status["pages"].append({"url": url, "raw": raw_path.name, "count": len(batch)})
                for paper in batch:
                    # Guard against stale API pages returning papers outside the window.
                    published = datetime.fromisoformat(paper["published"].replace("Z", "+00:00")).astimezone(LOCAL_TZ).date()
                    if not args.since <= published <= args.until:
                        status["filtered_out"] += 1
                        continue
                    if not matches_area(paper, area):
                        status["filtered_out"] += 1
                        continue
                    if paper["id"] not in papers:
                        paper["matched_areas"] = []
                        paper["history_matches"] = history.get(paper["id"], [])
                        papers[paper["id"]] = paper
                    if area not in papers[paper["id"]]["matched_areas"]:
                        papers[paper["id"]]["matched_areas"].append(area)
                if status["received"] >= total:
                    status["complete"] = True
                    break
                if not batch:
                    raise ValueError("Empty API page before advertised total; results incomplete")
            if not status["complete"]:
                status["truncated"] = True
        except (OSError, ValueError, ET.ParseError) as error:
            status["error"] = str(error)
        print(f"{area}: {status['received']} records; complete={status['complete']}" +
              (f"; {status['error']}" if "error" in status else ""), file=sys.stderr, flush=True)
    result["papers"] = sorted(papers.values(), key=lambda p: p["published"], reverse=True)
    result["new_candidate_ids"] = [p["id"] for p in result["papers"] if not p["history_matches"]]
    result["complete"] = all(q["complete"] for q in result["queries"])
    result["finished_at"] = datetime.now(LOCAL_TZ).isoformat()
    index = run_dir / "index.json"
    index.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"index": str(index), "papers": len(papers), "new_candidates": len(result["new_candidate_ids"]),
                      "complete": result["complete"]}, ensure_ascii=False))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
