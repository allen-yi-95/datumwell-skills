"""Read-only identity matching for legacy and multi-source benchmark ledgers."""

import argparse
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def identity(value):
    value = value.strip()
    if value.lower().startswith("repo:"):
        return "repo:" + value[5:].strip("/").removesuffix(".git").lower()
    if value.lower().startswith("arxiv:"):
        return "arxiv:" + re.sub(r"v\d+$", "", value[6:])
    if value.lower().startswith("doi:"):
        return "doi:" + value[4:].lower()
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if host in {"arxiv.org", "export.arxiv.org", "www.arxiv.org"}:
        match = re.match(r"/(?:abs|pdf|html)/(.+)", parsed.path)
        if match:
            return identity("arxiv:" + match[1].removesuffix(".pdf"))
    if host in {"github.com", "www.github.com"}:
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2:
            return identity("repo:" + "/".join(parts[:2]))
    if host in {"doi.org", "dx.doi.org"}:
        return identity("doi:" + parsed.path.lstrip("/"))
    if parsed.scheme not in {"https", "http"} or not host:
        return value
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path.rstrip("/"),
                       urlencode(sorted(query)), ""))


def record_keys(record):
    return {identity(v) for field in ("identifiers", "canonical_urls")
            for v in record.get(field, []) if v}


def load_records(path):
    if not path.exists():
        return [], f"History ledger missing: {path}; cross-run deduplication needs reconstruction."
    records = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict) or not record.get("name"):
            raise ValueError(f"Invalid history record at {path}:{number}")
        records.append(record)
    return records, None


def find_matches(records, values):
    keys = {identity(v) for v in values if v}
    return [{"name": r["name"], "family": r.get("family", r["name"]), "report": r.get("report")}
            for r in records if keys & record_keys(r)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--identity", action="append", required=True,
                        help="Repeat for paper IDs, repository IDs and official URLs")
    args = parser.parse_args()
    records, warning = load_records(args.history)
    print(json.dumps({"matches": find_matches(records, args.identity), "warning": warning},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
