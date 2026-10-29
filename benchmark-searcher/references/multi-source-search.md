# Multi-source benchmark discovery

## GitHub and official project sites

Discover candidates broadly, then verify official ownership and release evidence. GitHub has no search qualifier that establishes a repository as the introducing team's official benchmark. Stars, recent activity, a matching name or an organization account alone do not establish this.

### GitHub searches

Use repository name, description **and README** (`in:name,description,readme`). Search both `created` and `pushed`: the first finds newly created repos; the second catches pre-existing repos with newly published content. Neither timestamp is the benchmark's release date, and an old private repo becoming public may escape both routes. Supplement with official website announcements and known authors/organizations.

Example, replacing dates and selecting terms for the requested domains:

```bash
python3 <skill-dir>/scripts/fetch_github.py --storage-root <storage-root> --until YYYY-MM-DD \
  --query 'robot benchmark' --query 'embodied exam' --query 'agent evaluation' \
  --query '"long-horizon"' --query '"continual learning" benchmark' --query 'personalization benchmark'
```

Rotate `benchmark`, `bench`, `evaluation`, `eval`, `exam`, `testbed`, `suite`, and terms from the skill's domain table. Do not require one literal evaluation term in every query; broader domain-only or author/organization searches can discover differently named suites. Treat mentions in README related-work lists as leads, not evidence that the repository introduces that suite. Do not impose a minimum star count, coding language or license merely to shrink results.

For the independent `3d-cad` direction, cover both graphics/content creation (Blender, 3D asset/scene generation and editing) and engineering design (CAD, FreeCAD, OpenSCAD, CADQuery, parametric modeling, assemblies and functional mechanisms). Do not require `agent` or `robot` in these queries. For example:

```bash
python3 <skill-dir>/scripts/fetch_github.py --storage-root <storage-root> --until YYYY-MM-DD \
  --query 'Blender benchmark' --query 'CAD evaluation' --query '"3D creation"'
```

Check native project and geometry artifacts as well as rendered views; image similarity, solid validity, geometric accuracy and simulated function establish different capabilities.

The helper uses `gh api` with the existing authentication; `--transport curl` uses the public REST API through curl if gh is unavailable or unsuitable. It does not log in, modify credentials or write to GitHub. Connector/browser equivalents are acceptable when CLI access fails; save their queries and coverage too.

Results are paginated, with `--max-pages` defaulting to 3. Each search has GitHub's 1,000-result cap. Inspect `complete`, `incomplete_results`, errors and total counts; split overloaded queries into smaller dates/keywords and fetch remaining pages. `complete: true` only means those query pages were obtained. Do not treat an API cap, rate limit or missing authentication as no candidates. Use GitHub's rate-limit guidance and response headers; do not repeatedly retry an unchanged failure.

For a selected candidate, including an old or history-matched repo whose evidence needs inspection:

```bash
python3 <skill-dir>/scripts/fetch_github.py --storage-root <storage-root> --until YYYY-MM-DD \
  --repo OWNER/REPO
```

Read the metadata, decoded README (`content` is base64 when `encoding` is `base64`), all retrieved Releases and their linked documentation. Check `readme_error` separately from release-query completeness. Keep release `published_at`, tag and `prerelease`; exclude drafts. Fetch all relevant pages rather than just `/releases/latest`, because “latest” is not a complete release history and excludes some release types. An empty Releases list is not evidence of no public benchmark: inspect README News, dated official announcements and relevant code/data history. Use commit permalinks for file/commit evidence; a Git author/committer timestamp alone does not prove when code became public.

### Official website discovery and ownership

- Run fresh web searches combining requested domains with evaluation synonyms and release/launch terms. Use date filters as discovery aids, then read the actual dated official source. Follow links from arXiv, author/lab pages and repositories to find additional projects.
- Inspect user-provided project sites directly even when unindexed or marked `noindex`. If static HTML is a shell, render with a browser or inspect its linked JavaScript/JSON for visible protocol/results and outbound links. Do not stop at an empty HTML extract.
- Prefer a paper or author/lab page linking the repo, a project site linking the repo and the repo linking the project/paper, and author/team identities consistent across them. Save the supporting URLs under `official_evidence`. Weak evidence remains `official_status: unverified`; do not present the repo as confirmed official.
- A secondary article, social mention or curated list may point to a project. Confirm facts and dates on the introducing team's official site, repository or paper. Official team launch posts are primary announcements; reposts and search-engine timestamps are not.
- Read task definitions, data/environment construction, evaluation protocol, metrics and scoring artifacts. A landing page claiming “a benchmark” without accessible definitions is a lead, not a fully verified result.

Save selected HTML/JSON/text snapshots, URLs, fetch timestamps and any failed checks under the run's `fetches/` directory. GitHub and site sources supplement arXiv; they are independent discovery channels, not only fallbacks when arXiv returns too few papers.

## Release dates and history

Record separate source events with `source`, `date`, `url`, `verified`, and `event`:

| Source | Date evidence | Interpretation |
| --- | --- | --- |
| `arxiv_v1` | Atom `published` and v1 submission history | First arXiv submission of this paper; not necessarily first public benchmark release. |
| `project_announcement` | Dated official announcement explicitly introducing the benchmark | Official project launch date; distinguish initial launch from later updates. |
| `github_release` | Release `published_at` | Date this release was published; retain tag, `prerelease` and original timestamp. Inspect whether it introduces the suite or updates an old one. |
| `github_code_publication` | Explicit dated code/data launch notice with repository/commit evidence | Code/data availability event; not automatically the original benchmark introduction. |

`created_at`, `pushed_at`, Git commit dates, website build/last-modified times, crawl/index dates and `first_seen_at` are discovery/provenance fields. Do not substitute them for a verified release. A bare tag is not a GitHub Release. Preserve conflicting source dates and resolve the event meanings before selecting a date; do not choose whichever makes a candidate look fresh.

Use the user's timezone, default Asia/Shanghai, for window comparisons when timestamps exist; retain the original timestamp. For date-only announcements retain that date, mark `precision: day`, and keep its timezone unknown if unstated rather than inventing one. The GitHub helper searches with a one-day buffer for discovery and computes release-event window membership in Asia/Shanghai; neither `in_window: true` nor its collected release date verifies benchmark introduction.

A benchmark's `first_release` is the earliest **verified public introduction of that same benchmark known from checked evidence**, not proof of absolute first publication. Set `first_release_basis` to the supporting event/source. If an official website launched an old suite before this window, a new arXiv paper or code release does not make the suite a new benchmark. Do not exclude a newly introduced suite merely because its repository was created earlier. Major successors need task/data/protocol evidence and a link to the predecessor. Undated leads may be noted separately as “发布日期未核实”; do not count them toward fresh results or silently use the discovery date.

### Extended ledger (new entries)

```json
{
  "schema_version": 2,
  "name": "Official benchmark name",
  "aliases": [],
  "family": "Benchmark family",
  "identifiers": ["arxiv:2610.12345", "repo:team/benchmark"],
  "canonical_urls": ["https://official-project.example/", "https://github.com/team/benchmark", "https://arxiv.org/abs/2610.12345"],
  "first_release": "2026-10-14",
  "first_release_basis": "project_announcement",
  "release_dates": [
    {"source": "project_announcement", "event": "benchmark_introduction", "date": "2026-10-14", "precision": "day", "url": "https://official-project.example/news/launch", "verified": true},
    {"source": "arxiv_v1", "event": "paper_submission", "date": "2026-10-16", "timestamp": "2026-10-16T05:00:00Z", "url": "https://arxiv.org/abs/2610.12345v1", "verified": true},
    {"source": "github_release", "event": "code_release", "date": "2026-10-18", "timestamp": "2026-10-18T09:00:00Z", "tag": "v1.0", "prerelease": false, "url": "https://github.com/team/benchmark/releases/tag/v1.0", "verified": true}
  ],
  "official_evidence": ["https://official-project.example/", "https://github.com/team/benchmark/blob/COMMIT/README.md"],
  "reported_at": "2026-10-20",
  "domains": ["agents"],
  "delivery": "chat",
  "report": null
}
```

This is an illustrative schema, not real benchmark data. For direct chat delivery use `delivery: "chat"` and `report: null`; a report path is needed only when the user explicitly asks for a saved report. Preserve legacy report paths. Omit unknown IDs/events; never add fabricated dates to fill fields. The helper's unverified release events require manual event classification before adding verified evidence to the ledger.

Preserve all existing ledger entries unchanged, including older `first_release` values that used the arXiv-v1 convention. Absence of `schema_version`, `release_dates` or `official_evidence` does not remove an older benchmark from exclusions. Use old records for identity deduplication without treating their dates as newly verified multi-source dates. If old identity metadata is incomplete, inspect the linked prior report before declaring a candidate new.

The read-only `benchmark_history.py` helper matches versionless arXiv IDs, DOI, normalized official URLs and case-insensitive GitHub owner/repo identities, including release/blob URLs. It strips tracking query parameters/fragments, but preserves meaningful site query parameters. Neither names/acronyms nor similar site domains alone prove family identity: resolve aliases, moved repositories and renamed projects manually. Multiple distinct suites within one paper/repository stay separate after task/protocol verification; helper matches are review flags, not automatic exclusions. Merge a newly found paper/site/repo into a reported family's identity assessment rather than reporting it again merely because it uses a different source.

### Result presentation

Keep the skill's concise area-grouped list and three sub-bullets. Label dates in the introduction, for example:

- `官网首发 10 月 14 日；arXiv v1 10 月 16 日；代码发布 10 月 18 日`.
- `GitHub Release 10 月 18 日（预发布）；未找到 arXiv 论文` when that release verifiably introduces the benchmark.

For scores, cite the actual paper version, pinned repository file/tag, or official leaderboard snapshot with check timestamp. Clearly separate paper results from later official scores and preserve protocol differences. State `官方来源未报告模型成绩` when applicable. Do not infer publication or task success from site build dates, badges, plots or repository popularity.

## Official API references

- [Repository search qualifiers](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)
- [GitHub REST search limits and incomplete results](https://docs.github.com/en/rest/search/search)
- [GitHub Releases API](https://docs.github.com/en/rest/releases/releases#list-releases)
- [GitHub CLI API requests](https://cli.github.com/manual/gh_api)
