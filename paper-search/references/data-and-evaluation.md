# Data and evaluation within broader paper discovery

Search these contributions independently of the six application domains and without requiring robot/agent keywords. Favor work with a concrete new resource, method or evaluation finding supported by primary evidence. Keep the skill’s freshness window, source-specific dates, contribution-aware deduplication and chat delivery. These are important research topics, not the entire scope of Paper Search.

## What qualifies

- **Dataset:** a newly released, usable dataset/corpus, with a stated purpose, composition, construction or collection procedure and access information. Training, post-training, RL, preference, multimodal and evaluation data all qualify. A leaderboard is not required.
- **Data method:** a substantive curation, annotation, synthetic-data, selection, filtering, deduplication, quality or contamination method with inspectable experiments. Merely training another model on existing data does not qualify.
- **Benchmark:** a distinct suite with defined tasks, evaluation protocol and metrics, including domains beyond the existing six. Keep task success, partial scores, physical validity and visual quality separate.
- **Evaluation method:** substantive work on judges, rubrics, metrics, robustness, statistical uncertainty, ranking reliability, contamination, reproducibility or evaluation harnesses with inspectable validation. Distinguish a method applied to existing benchmarks from a newly introduced benchmark.

Give each identity one primary type; mention additional contributions in that same entry. Minor versions, score updates, ordinary commits and a later paper do not reset a family’s age. For a new data-method paper evaluated on an old dataset, the new identity is the method, not a new release of that dataset. General model/method/system papers can qualify independently under Paper Search; do not relabel them as data/evaluation papers. Exclude unsupported marketing and resource lists.

## Independent discovery

The arXiv helper defaults include `data`, `benchmark-general` and `evaluation-methods`; all application and general research routes now have no mandatory evaluation-keyword gate. Inspect candidate substance rather than accepting a keyword hit.

Supplement with fresh GitHub created/pushed queries such as `"dataset" "synthetic data"`, `"data curation"`, `"data quality"`, `"data selection"`, `"benchmark contamination"`, `"LLM-as-a-judge"`, `"evaluation reliability"` and `"evaluation suite"`. Rotate terms rather than running every example mechanically. Read official dataset cards, versioned documentation, linked papers and introducing-team announcements, including public Hugging Face pages when relevant. A repository/dataset created timestamp or search-engine date alone does not prove release. Preserve dated launch evidence and source bytes privately.

## Type-specific findings

Use the same concise introduction plus three bullets: background/pain point, method/data, and results/evidence. Include author/team and institution/company (mark unreported), primary links and source-specific release dates.

- **Datasets:** report sample/token/hour/trajectory/user counts with units, modalities, languages/domains, splits, provenance, annotation/synthesis and access/license when stated. Preserve counts at their actual granularity; tokens, documents, tasks and episodes are not interchangeable. Explain usefulness and a concrete limitation.
- **Data methods:** report the intervention, source/target data, data volume and compute budget, comparable baselines and ablations; distinguish data effects from model size or extra training.
- **Benchmarks:** retain sourced model/harness versions, metrics, units, direction, splits, retries and budgets under the existing model-score rules.
- **Evaluation methods:** report judge/calibration versions, validation population, agreement/correlation/error or ranking changes, and uncertainty where available. Agreement with one judge is not automatically human validity.

For dataset/method results, use **结果／证据**: downstream model results where reported, or supported quality/diversity/coverage/annotation-cost measurements. Preserve exact versions and evaluation conditions. If model scores or empirical results are absent, explicitly state **官方来源未报告模型成绩** or **未报告实证结果**, respectively; do not fabricate a leaderboard or imply missing results are zero. Explain when a dataset is available only by application or not yet downloadable. Do not label a method as a new benchmark merely to fit the old output template.

## History and existing website

Use the existing artifacts/benchmark-searcher/history.jsonl ledger for every delivered identity, adding item_type on new entries and preserving old bytes. New fetches live under artifacts/paper-search/fetches/. Do not duplicate a new method as both a paper and a dataset release.

The Datumwell public catalog now accepts data, benchmark-general, evaluation-methods, foundation-models, multimodal, ai-systems and safety alongside the original six application areas. Follow the current catalog.py contract; do not force a cross-domain paper into an unrelated field. Daily runs may add only fully reviewed source-grounded bilingual cards, never alter the schema or publish abstract-only previews. Preserve existing cards and separate chat delivery from any publishing blocker.
