---
name: benchmark-searcher
description: "Find newly released AI benchmarks across arXiv, official project websites and GitHub in robotics, agents, long-horizon tasks, continual learning, personalization, and 3D/Blender/CAD. Use for benchmark discovery, roundups or more results without repeats; distinguish source-specific release dates and cite model scores."
---

# Benchmark Searcher

Find recent, distinct evaluation benchmarks and explain what each measures, why it was needed, and how mainstream models perform. Search arXiv, official project websites, and GitHub releases with fresh requests on every discovery run. General web search, news and curated lists may locate candidates, but verify identity, dates, methods and scores against these primary sources. Honor explicit user source restrictions. A benchmark without an arXiv paper can qualify when official sources define its tasks, evaluation protocol and metrics. Match the user's language; retain official benchmark and model names.

## Scope and freshness

Honor any requested dates, domains, exclusions, and result count. Otherwise:

- Search the latest **7 calendar days including the user's current date**, aiming for 5–10 verified benchmarks across the six areas below. For example, on 2026-10-19 use 2026-10-13 through 2026-10-19 in Asia/Shanghai. Include at least one from each area when qualifying candidates exist; one benchmark may cover several areas but appears only once.
- Deduplicate against the persistent ledger and prior reports. If too few qualify, return fewer results and explain coverage gaps; do not automatically broaden the date window or pad with familiar benchmarks. Expand only when the user requests a wider period.
- Distinguish **newly released** from **new to the user**. Keep arXiv v1, official project announcement, GitHub Release, and code-publication dates separately, with evidence and event labels. Select new benchmarks by their earliest verified public introduction, not whichever later source falls in the window. A later paper, code release, revision, ordinary commit, or score update does not reset benchmark age. Follow the [date and history rules](references/multi-source-search.md#release-dates-and-history).

| Area | Relevant evaluation targets and search terms |
| --- | --- |
| Robotics | Embodied AI, manipulation, navigation, locomotion, VLA, sim-to-real, real-world robot evaluation |
| Agents | Tool use, web/browser and computer use, coding, research, multi-agent coordination, enterprise workflows |
| Long-horizon tasks | Multi-step planning and execution, extended rollouts, persistent state, delayed rewards, long-running interaction; long-context QA alone is insufficient |
| Continual learning | Sequential tasks, online adaptation, evolving environments, forgetting, retention, forward/backward transfer; static multitask evaluation alone is insufficient |
| Personalization | User preferences, profiles, personal memory, user-specific adaptation, recommendation, preference evolution and personalized assistants |
| 3D / Blender / CAD | 3D creation, modeling/modelling, asset generation and editing, scene composition, procedural geometry, Blender, FreeCAD, OpenSCAD, CADQuery, parametric/solid modeling, B-rep, assembly and functional mechanism design, geometry constraints and simulation-based verification |

Interpret these as research/application areas. Mention the industry or deployment setting when it explains the benchmark's relevance. A training dataset or model paper qualifies only if it introduces a defined evaluation task, protocol, and metrics.

Search 3D/Blender/CAD independently, without requiring robotics or agent keywords. Include native editable projects, geometric reconstruction/editing, parametric solids, assemblies and functional simulation when they define an AI evaluation protocol. Pure 3D perception or renderer/hardware speed tests are outside this direction unless they also evaluate creation or design. A CAD agent/harness paper that only reuses existing suites is a related method, not a new benchmark. Keep visual quality, geometric validity/accuracy, editability, constraint satisfaction and physical function separate when reporting scores.

## Fresh discovery across three channels

On each default discovery run, fetch arXiv metadata, search GitHub through both new-repository and recent-push routes, and search for dated official project announcements. Do all applicable channels before selecting a quota; arXiv yield alone is not a reason to skip GitHub or official sites. Do not silently widen the release window. Read [multi-source search](references/multi-source-search.md) for GitHub queries, official identity checks, website discovery, date evidence and the extended ledger schema.

- **arXiv:** use the helper below and verify selected full texts with curl.
- **GitHub:** use `scripts/fetch_github.py` with repeated `--query` keywords; it searches both `created` and `pushed`. Rotate domain terms with `benchmark`, `evaluation`, `exam`, `testbed` and `suite`; include broader domain queries where feasible. For 3D/CAD, separately query Blender, CAD/computer-aided design and 3D creation/modeling terms rather than relying on agent queries. Use `--repo owner/name` for selected repositories' metadata, README and paginated Releases. The helper saves raw responses and exact history matches, but leaves official status and benchmark introduction unverified. `--dry-run` is not a live search. For resolved identities from any source, `scripts/benchmark_history.py --history <ledger> --identity <URL-or-ID>` supports repeated identities and legacy entries.
- **Official sites:** use live web discovery for the requested areas and dates, follow paper/repository links in both directions, and inspect user-provided sites directly. Read dated News/Announcements or official launch posts; do not require an arXiv entry or GitHub Release. Save evidence URLs, timestamps and relevant snapshots under the run's fetch directory. A search-engine date alone is not release evidence.

Both helpers write below `<storage-root>/artifacts/benchmark-searcher/fetches/` and never append history. Resolve storage as described below. API errors, result caps, missing authorization, search-index gaps and inaccessible sites are coverage limitations, not zero matches. Continue the available channels and disclose material gaps. Search-result completeness flags describe those queries, not exhaustive coverage of all benchmarks.

### arXiv metadata and full text

Use **curl** for arXiv requests, including API metadata, abstract pages, HTML full texts, and PDFs. The bundled Python script invokes curl for HTTP transport and uses the standard library for query construction, parsing, and storage. Run it on each discovery run before selecting papers (unless the user excludes arXiv). Pass the user's current date explicitly so a different execution-host date cannot shift the release window:

```bash
python3 <skill-dir>/scripts/fetch_arxiv.py --storage-root <storage-root> --until YYYY-MM-DD
```

The script queries the official arXiv Atom API with category, title/abstract keywords, and first-submission date filters, sorted by submitted date. It makes fresh requests instead of reusing a previous run. Default mappings are:

| Area | arXiv categories |
| --- | --- |
| Robotics | cs.RO, cs.AI, cs.CV, cs.LG |
| Agents | cs.AI, cs.CL, cs.MA, cs.SE, cs.HC |
| Long-horizon tasks | cs.AI, cs.RO, cs.CL, cs.LG, cs.SE |
| Continual learning | cs.LG, cs.AI, cs.RO, cs.CL, cs.CV |
| Personalization | cs.CL, cs.AI, cs.IR, cs.HC, cs.LG |
| 3D / Blender / CAD | cs.GR, cs.CV, cs.AI, cs.HC, cs.LG, cs.SE, cs.RO, cs.CL |

Use `--areas robotics agents long-horizon continual-learning personalization 3d-cad` to select requested areas (`3d-cad` is the independent 3D/Blender/CAD direction), `--since YYYY-MM-DD` for a custom start date, and `--max-pages N` to expand pagination when needed. `--dry-run` only prints queries and does not count as a live fetch. Requests are serial and spaced by at least three seconds, following [arXiv API limits](https://info.arxiv.org/help/api/tou.html).

Read the returned `index.json` and abstracts. The script also rechecks category and title/abstract keyword matches locally and records discarded API hits as `filtered_out`. Each run saves raw Atom responses, query URLs, fetch timestamps, coverage/truncation/errors, paper metadata, arXiv full-text links, and history matches under `artifacts/benchmark-searcher/fetches/`. These are candidates, not automatically accepted benchmarks. `matched_areas` are query matches, not final domain judgments. `new_candidate_ids` is only an ID-based shortlist; check aliases/families manually, and inspect history-matched papers only for genuinely distinct suites or user-requested updates. The fetcher never appends candidates to the reported-history ledger.

The script's default limit is three pages of 100 papers per area; this is a local configurable cap, not an arXiv retrieval limit. If `complete` is false, inspect whether this is pagination truncation or an error; extend relevant queries or disclose the coverage limit. Never interpret failed requests as zero papers. If the API fails, try arXiv's own search/category pages using curl. If live arXiv access still fails, report that channel's limitation and continue official sites and GitHub; never present cached results as newly fetched.

Fetch metadata first, then download selected papers' arXiv HTML or PDF with curl and read the relevant methods and result tables locally. Download only selected full texts, not every search result. Follow-up queries may refine keywords/categories when a requested area lacks candidates, within the arXiv channel. See the [API manual](https://info.arxiv.org/help/api/user-manual.html) for query semantics.

## Persistent non-repetition

Keep runtime data outside the skill folder. Use the active workspace as the storage root unless the user supplies a shared history location. Pass `--storage-root` explicitly when running from a different directory.

Deliver findings directly in chat. Keep the persistent ledger at `<storage-root>/artifacts/benchmark-searcher/history.jsonl` and reuse it across runs and sessions; source-fetch evidence may remain under `fetches/`. Do not create a report file unless the user explicitly requests one. Preserve existing reports as legacy evidence. If history cannot be accessed, disclose that cross-run deduplication is unverified; do not silently claim no repeats.

Before researching, read the ledger and relevant prior benchmark-search reports. On the first run, check available prior conversation results and search existing notes/reports for benchmark roundups to bootstrap the exclusion set. Do not classify a name as previously reported merely because it appears in a paper's related work. State when prior coverage cannot be reconstructed completely.

Deduplicate both within the current batch and against past reports using benchmark identity: official name and aliases, versionless arXiv ID or DOI, canonical project URL, and repository owner/name. Strip URL tracking parameters and fragments, normalize trailing slashes, and treat arXiv abstract/PDF links and revision suffixes as the same paper. Use names as supporting evidence; acronyms alone can collide. Multiple benchmarks in one paper remain separate when they define distinct evaluation suites.

Deduplicate across sources as well as runs: a website, repository, release and paper describing the same suite are one benchmark. Default to excluding the whole previously reported benchmark family, including renamed projects, translations, new paper revisions, score updates, and minor dataset versions. Shared infrastructure alone (for example, two distinct suites built on LIBERO) does not establish the same family; compare task and protocol identity before excluding. A major successor may qualify only if it materially changes the tasks, data, or evaluation protocol; explain the difference and link its predecessor. Repeat or refresh an old benchmark only when the user asks for updates or explicitly allows repeats.

When the verified findings are ready for delivery in chat, append one JSON object per included benchmark, preserving existing ledger bytes and existing entries. Store only items being delivered; rejected candidates do not become exclusions. Keep `name`, `aliases`, `family`, `identifiers` (arXiv, DOI and `repo:owner/name` when known), canonical official URLs, domains and reported date. For chat delivery use `delivery: "chat"` and `report: null`; do not create a report merely to fill a path. New entries use `schema_version: 2`, a sourced `release_dates` event list, `first_release` plus `first_release_basis`, and `official_evidence`; see the [schema and compatibility rules](references/multi-source-search.md#release-dates-and-history).

Older entries retain their original `first_release` convention; missing new fields do not disable their identity exclusions. Never rewrite old dates as multi-source first releases. A new entry's `first_release` is the earliest verified public benchmark introduction known from checked evidence (not proof of absolute first release); use `null` if unverified. Undated candidates do not enter the fresh-results list; an optional undated leads section must be clearly separate. Repeated runs on the same day still deduplicate against the latest ledger. If the user explicitly requests a saved report and one already exists for that date, add a numeric filename suffix. If a ledger update fails, still deliver the findings in chat and disclose the failure so deduplication can be recovered next time.

## Research and verify

1. Search all applicable channels, read candidate metadata and abstracts/READMEs, and distinguish defined new evaluation suites from papers or repositories that only reuse existing benchmarks.
2. Resolve the official name, aliases, authors and affiliated organizations using paper, project and repository links. A third-party reimplementation, mirror or resource roundup is not the introducing team's release. Inspect official sites directly even when they are absent from search indexes.
3. Verify each source's date and what it announces. A repository created recently or pushed recently is only a candidate. No GitHub Release does not disqualify a benchmark; inspect dated official announcements and relevant code/data publication history. Keep undated and conflicting evidence explicit.
4. Read selected papers' methods and result tables, or equivalent official protocol documentation, versioned README/result files and official leaderboard data. Record paper version, repository commit/tag, or website check timestamp. No-paper projects still need inspectable task/protocol/metric definitions; do not invent missing scores.
5. Deduplicate the resolved benchmark identities against each other, the ledger and prior reports before ranking. Rank by verified freshness, domain fit, evaluation usefulness and source completeness, without requiring stars or filling a quota at the expense of verification.

If a primary source is unavailable, use the other verified primary sources and label the gap. Cached recollections and search snippets are not freshly verified findings.

## Mainstream-model results

For every benchmark, look for scores of representative widely used frontier models, strong open-weight models, and relevant specialist systems actually evaluated in the paper, appendices, or official published results. In robotics, the relevant systems may be VLAs or robot policies rather than chat models. Identify exact model versions, and select 2–4 representative comparable systems when available; fewer is acceptable when reporting is limited. Keep the presentation compact rather than listing every evaluated model. Do not assume a model is still current without checking.

For each reported score, verify the metric name, numeric value, scale/unit and direction, split or task subset, evaluation setup, source, and source's result date or version when available. In the concise output, state shared conditions once and retain differences that materially affect interpretation. State the check date and the paper version, repository commit/tag or official leaderboard snapshot used. Official project leaderboards are allowed, but keep their current results separate from paper tables; third-party scores require primary confirmation. Preserve distinctions such as success rate vs. pass@k, macro vs. micro averages, and percent vs. fraction. Do not manufacture an overall score by averaging unrelated metrics.

Agent harness, tools, retries, rollout budget, training/fine-tuning, and simulated vs. real-world conditions can change results. Label materially different protocols explicitly within the model-scores bullet; do not imply a fair ranking across them. Label scores as paper-reported or officially published, preserving whether the source attributes them to its own runs, a provider, or a reproduced result. Do not describe paper scores as current live leaderboard standings or mix protocols across source versions.

Never infer a missing score from a graph, another benchmark, model reputation, or an unrun evaluation. For every included benchmark, include a model-scores bullet even if it only says **官方来源未报告模型成绩** and identifies the paper/appendix version or official documentation/results snapshot checked. For a specific unevaluated model use **Not reported**, never zero. If only specialist or older models have scores, give those scores and explicitly state the lack of mainstream-model results.

## Deliverable

Present the full findings directly in chat as concise Markdown lists grouped by research/application area, using the structure below. This also applies to scheduled runs: return the benchmark details, not just an overview, count or report link. Do not save Markdown, HTML, PDF or other report files, run a report renderer, open a preview, or use a comparison table unless the user explicitly requests that deliverable. Maintain the deduplication ledger separately. For scheduled runs, remain quiet when no qualifying new benchmarks are found, as directed by the automation.

Start with one short sentence giving the check date, release window, and result count. Mention incomplete history access or an expanded date window only when relevant; keep routine ledger details out of the main reading flow.

Use area headings in the user's language, such as 机器人、Agents、长时任务、持续学习、个性化、3D／Blender／CAD. Include only areas with qualifying results. Put each benchmark under its primary area once; mention overlapping areas briefly in its introduction rather than duplicating it. Use `3d-cad` in ledger domains for this direction.

Use this structure for every benchmark:

```markdown
## {领域}

- **{Official benchmark name}**：{arXiv／官方项目／官方仓库链接}，{一句基本介绍；明确日期类型，如“官网首发 YYYY-MM-DD；arXiv v1 YYYY-MM-DD”或“GitHub Release YYYY-MM-DD；未找到论文”，作者／机构简注}。
  - **背景／痛点**：{已有评测缺什么，它要解决什么问题；1–2 句}。
  - **方法**：{怎么构造任务、数据或环境，怎么评测；保留最有用的规模与关键协议，1–2 句}。
  - **主流模型和分数**：{共享指标、单位／方向与必要设置}；{模型版本 A} {分数}，{模型版本 B} {分数}，{模型版本 C} {分数}。[成绩来源／表号／版本或快照](https://official-source.example/results)
```

Keep the introductory line and three sub-bullets short. Use labeled source links next to claims and scores; one source link may support several scores when they share a table and protocol. Link the strongest verified primary sources: arXiv full text, official launch page, official repository permalink or official results. Add only links that support the introduction, release date, protocol or scores. Label missing papers and source-specific dates instead of forcing an arXiv link. Include a material caveat briefly in the relevant introduction, methods, or scores bullet instead of adding a standard limitations section to every item. Do not drop a condition that would make the displayed score misleading merely to shorten the answer.

End with a short coverage or freshness note only when there are uncovered areas, older-window additions, or other material gaps, including a channel that could not be searched. Do not claim an exhaustive search of all benchmarks.
