# Datumwell Research Skills

Two portable Agent skills behind [Datumwell Community](https://www.datumwell.io/community/?type=papers): discover interesting topics in the latest frontier AI papers, then read the full-text evidence.

| Skill | Purpose | Entry point |
| --- | --- | --- |
| Paper Search | Discover recent papers across models, reasoning, multimodal AI, systems, safety, data, benchmarks and application research; verify contributions, dates and evidence without repeats. | [SKILL.md](paper-search/SKILL.md) |
| Paper Reader | Read the paper body, methods, evaluation tables and limitations before extracting source-grounded key points. | [SKILL.md](paper-reader/SKILL.md) |

## Download and install

Get individual ZIP files or the combined bundle from [GitHub Releases](https://github.com/allen-yi-95/datumwell-skills/releases/latest) or [Datumwell](https://www.datumwell.io/community/?type=papers#research-skills). Verify downloads using SHA256SUMS.

For Codex, unzip and place the `paper-search` and/or `paper-reader` folders directly in `~/.codex/skills/` (or `$CODEX_HOME/skills/`). Each folder must contain its own SKILL.md. Other compatible Agents use their documented skills directory. Review modified local installations before replacing them. Paper Search replaces Benchmark Searcher; remove the old installed skill after migrating any local customizations to avoid duplicate discovery entries.

Paper Search helpers require Python 3.10+, curl and IANA timezone data. GitHub discovery uses an existing authenticated gh CLI or `--transport curl` for public REST. Paper Reader uses the Agent's browsing/PDF tools. Neither download includes a model client, API key or runtime service.

```text
Use $paper-search to find interesting new frontier AI papers, prioritizing the latest 24–48 hours within the last seven calendar days.
Use $paper-reader to explain this paper's full-text methods, results and limitations: <paper URL>
```

Inspect query construction offline:

```sh
python3 paper-search/scripts/fetch_arxiv.py --until YYYY-MM-DD --dry-run
python3 paper-search/scripts/fetch_github.py --until YYYY-MM-DD --query 'agent memory' --query 'test time scaling' --dry-run
python3 -m unittest discover -s paper-search/scripts -p 'test_*.py'
```

Replace the date with the intended check date. Dry runs do not fetch or verify sources.

## Scope and evidence

- Broad frontier AI research: models/reasoning, multimodal AI, systems, safety, data/evaluation, robotics, agents, long-horizon tasks, continual learning, personalization and 3D/CAD. A new benchmark is not required.
- Prioritize substantive contributions and evidence, not stars or a quota for every field. Keep release dates distinct from revisions and repository activity.
- Read full texts; retain methods, exact metrics, conditions, source sections/tables and limitations. Do not repeat abstracts as reviews.
- Private evidence belongs in `artifacts/paper-search/fetches/` in the active workspace. Preserve the existing `artifacts/benchmark-searcher/history.jsonl` ledger for deduplication across the rename; its legacy path is intentional. No personal history or downloaded papers ship in the packages.
- Scheduling and publishing are configured separately. Installing these skills does not create a daily job or publish content. Datumwell's existing daily job runs at 08:00 Asia/Shanghai.
- The optional renderer supports legacy nine-column reports only when explicitly requested; normal findings appear in chat.

## 中文说明

Paper Search 从每日最新的前沿 AI 论文中寻找值得关注的话题，范围包含模型、推理、多模态、系统、安全、数据与 benchmark，以及机器人、Agents、长时任务、持续学习、个性化和 3D/CAD。Paper Reader 负责阅读全文，提取带来源的贡献、方法、结果与局限。

Paper Search 已替代 Benchmark Searcher；旧检索历史保留原路径，避免改名后重复推荐。下载不包含私人数据、论文全文或密钥，也不会自动创建定时任务。版本见 release.json，反馈可提交到 [GitHub Issues](https://github.com/allen-yi-95/datumwell-skills/issues)。
