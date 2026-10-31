---
name: paper-search
description: "Discover recent frontier AI papers and interesting research topics across arXiv, official projects and GitHub. Cover models, reasoning, learning, multimodal AI, systems, safety, data, benchmarks, robotics, agents, memory/personalization and 3D/CAD; verify dates, contributions and evidence, and deduplicate prior research."
---

# Paper Search

Find interesting topics in the newest frontier AI papers, not only new benchmarks. Select substantive advances, surprising findings and useful methods; explain what changed, why it matters and what the evidence supports. Search arXiv, official project websites and GitHub with fresh requests on every discovery run. Data and benchmarks remain important interests alongside model architectures, training/post-training, reasoning, inference, multimodal learning, AI systems, safety, robotics, agents, long-horizon tasks, continual learning, personalization/memory and 3D/Blender/CAD. Do not require a new dataset, benchmark, leaderboard, code release or particular model name to qualify. Match the user's language and retain official paper/model names.

## Scope and freshness

Honor requested interests, dates, exclusions and result counts. Otherwise:

- Run daily using the user's actual date and timezone (default Asia/Shanghai). Search the latest **7 calendar days including that date** to cover publication delays and weekends, prioritizing unseen papers from the latest **24–48 hours**. State the actual release window; never imply all seven-day results were released today.
- Aim for 5–10 well-supported items, with no quota per field. Return fewer when appropriate; do not fill the list with low-value items or silently widen the window.
- Rank by fit to the user's interests, conceptual novelty, strength of evidence and practical/research implications, with freshness as a strong signal. Stars, author fame, marketing claims and leaderboard rank alone do not establish importance.
- Distinguish new research from newly discovered old work. Keep arXiv v1, official announcement, GitHub Release and code/data availability dates separately. Revisions, score updates and ordinary commits do not reset the age of the same contribution. A genuinely new method using an old dataset or shared repository can qualify as a distinct paper.
- Use current conversation/explicit interests to refine the search. In their absence use the scope below; do not invent personal interests or require every area to yield a result.

| Route | Research interests |
| --- | --- |
| `foundation-models` | Architectures, pretraining/post-training, RL, reasoning, planning, test-time compute, efficiency and model behavior |
| `multimodal` | Vision-language, video, audio/speech, world models and cross-modal generation/understanding |
| `ai-systems` | Inference, serving, training systems, kernels, distributed learning and compute/memory trade-offs |
| `safety` | Reliability, robustness, alignment, interpretability, hallucination, privacy and security |
| `data` | Datasets, collection, annotation, curation, synthetic data, quality, selection and contamination |
| `benchmark-general`, `evaluation-methods` | Evaluation suites, judges, metrics, uncertainty, reproducibility and ranking reliability |
| `robotics` | Embodied AI, manipulation, navigation, VLA, sim-to-real and robot learning |
| `agents` | Tool use, browser/computer use, coding, research, multi-agent systems and workflows |
| `long-horizon` | Extended planning/execution, persistent state and delayed rewards |
| `continual-learning` | Adaptation, sequential learning, forgetting and transfer |
| `personalization` | User preferences, personal memory, personalized assistants and recommendation |
| `3d-cad` | 3D generation/editing, Blender, CAD, geometry, assemblies and functional design |

Application routes do **not** require benchmark/evaluation keywords. Model and method papers evaluated on existing suites are explicitly in scope when their contribution is substantive. Search 3D/CAD independently of robot/agent terms. Read [Data and evaluation research](references/data-and-evaluation.md) for additional type-specific evidence rules.

## Fresh discovery across three channels

Perform applicable arXiv, GitHub and official-site searches before selecting findings. A strong arXiv yield does not replace the other channels. Read [multi-source search](references/multi-source-search.md) for official identity, date evidence, pagination and history compatibility.

1. **arXiv:** run the bundled helper on every discovery run unless explicitly excluded. Use **curl** for arXiv API metadata, abstract pages, HTML and PDFs. The Python helper invokes curl and saves original responses; `--dry-run` is not a live search.

   ```bash
   python3 <skill-dir>/scripts/fetch_arxiv.py --storage-root <storage-root> --until YYYY-MM-DD
   ```

   Default routes are all rows above. Use `--areas agents foundation-models data` for a requested subset, `--since YYYY-MM-DD` for explicit windows, and `--max-pages N` for pagination. Queries filter first-submission dates in Asia/Shanghai, not revision dates. Inspect `index.json`, abstracts, locally discarded hits, `complete`, truncation and errors. The default cap is three pages of 100 per route; disclose material coverage gaps. A capped query is not exhaustive coverage. Requests are serial and spaced by at least three seconds following [arXiv API limits](https://info.arxiv.org/help/api/tou.html). If the API fails, try arXiv search/category pages via curl, then disclose continued failure and use the available channels. Never present cached results as live discoveries.

2. **GitHub:** `scripts/fetch_github.py --until YYYY-MM-DD --query 'agent memory' --query 'test time scaling'` searches both new repositories and recent pushes. Rotate broad research/topic queries; do not suffix every query with benchmark/evaluation. For selected candidates, use `--repo owner/name` to retrieve metadata, README and paginated Releases. Repository timestamps and helper release flags are leads, not proof of a new paper. Confirm the introducing authors/team through reciprocal primary links. Code availability is useful but not required for a paper to qualify.
3. **Official sites:** inspect introducing labs' announcements, project pages, model/data cards and release notes; follow paper and repository links in both directions. Search-engine dates, reposts and resource lists only locate leads. Record dated primary evidence and material access gaps.

New source fetches go under `<storage-root>/artifacts/paper-search/fetches/`. Download full texts only for shortlisted papers, not all search hits. Fetchers never append history or accept candidates automatically. `matched_areas` are keyword routes, not final scholarly classification.

## Persistent non-repetition

Keep runtime evidence outside the skill folder. Resolve the real installed directory; under a notes repository's `scripts/workflows/`, use that repository as storage root; otherwise default to the active workspace or an explicitly provided shared root.

Keep the persistent ledger at `<storage-root>/artifacts/benchmark-searcher/history.jsonl` and source fetches under `<storage-root>/artifacts/paper-search/fetches/`. Preserve existing history bytes. Read relevant prior reports and conversation results when reconstructing incomplete history; disclose unavailable history.

Normalize versionless arXiv IDs/DOIs, canonical project URLs and GitHub owner/repo identities. `scripts/benchmark_history.py --history <ledger> --identity <URL-or-ID>` remains a backward-compatible helper name; matches are **review flags**, not automatic whole-repository exclusions. Two papers in a shared model repository can have distinct contributions. For benchmarks/datasets, preserve family deduplication across aliases and minor versions; for new model/method papers, compare the paper and substantive contribution instead of excluding everything sharing its repository or evaluated datasets. Do not count a revised paper, mirror or renamed project twice.

When verified findings are ready to deliver, append one JSON object per delivered identity, preserving all existing ledger bytes. Use `schema_version: 2`, `name`, `aliases`, `family`, `identifiers`, `canonical_urls`, `domains`, `reported_at`, `release_dates`, `first_release`, `first_release_basis`, `official_evidence`, `delivery: "chat"`, `report: null`. Add `item_type`: `paper`, `model`, `method`, `dataset`, `data-method`, `benchmark`, `evaluation-method`, `system`, or `analysis`. Choose one primary type; do not deliver one project repeatedly under different types. Old records without these fields remain valid. Only delivered findings enter history. A failed append must be disclosed without withholding findings.

## Read, select and verify

- Resolve official title/name, authors, institutions/company (mark unreported) and source-specific release dates. Earliest verified introduction applies to that contribution; do not age a new method by the reused benchmark's launch date.
- Read shortlisted full texts: problem, method, evaluation setup, result tables, limitations and relevant appendix. Use **paper-reader** for full-text notes and public website key points. An abstract or project claim alone cannot support a full-text-reviewed card.
- Look for the actual contribution, nearest baselines, ablations, scale and compute, uncertainty and whether evidence supports the conclusion. Treat negative findings, theory and careful analyses as eligible; report their kind of evidence instead of demanding a model leaderboard.
- For quantitative results retain exact model/harness versions, metrics, units/direction, dataset/split, budgets, training vs test-time conditions, and paper version/table or pinned official source. Keep paper-reported and later leaderboard results separate. Do not average unrelated metrics, infer missing values from reputation or present absent scores as zero.
- Benchmarks need inspectable tasks/protocol/metrics. Datasets need composition, provenance, access/license and usefulness. Methods/models/systems need their intervention, comparable baselines, budgets and reported evidence. Theory/analysis need assumptions, claims, proof/measurement design and scope. Code-only research without a paper must be clearly labeled and needs complete primary method/results evidence; it is not a published paper.
- If the selected full text cannot be accessed, omit it from the fully reviewed list and website. You may mention a clearly labeled unreviewed lead separately without inventing findings. Preserve the last valid public feed on research/publishing failures.

## Deliverable

Return concise area/topic-grouped findings directly in chat. Start with the check date, actual release window and result count. For each item:

```markdown
- **{Official paper title or project}** · {type} — {one-sentence contribution; authors/institution; labeled release dates}. [Paper](https://primary.example/paper)
  - **问题／背景**：{what limitation or research question motivated this work}。
  - **方法／贡献**：{specific mechanism, data, experiment or theoretical idea}。
  - **证据／启发**：{reported result with metric/setup and section/table citation; why this topic matters; a concrete boundary}。
```

Use source links next to claims; preserve meaningful conditions rather than forcing shorter copy. For benchmarks include comparable model scores when reported; otherwise say **官方来源未报告模型成绩** and identify sources checked. For other papers use the evidence appropriate to the contribution; say **未报告实证结果** when appropriate rather than inventing a ranking. Clearly distinguish an agent's interpretation from authors' claims. Do not repeat abstracts. Close with a coverage note only for material gaps.

Do not create standalone reports/HTML/PDFs or previews unless requested. Private evidence and the separately authorized Datumwell website build are allowed. For scheduled runs, keep the established schedule and stay quiet when no new qualifying research or actionable failure exists. Installing the skill alone creates no schedule or publication permissions.
