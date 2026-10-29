# Datumwell Research Skills

Two portable Agent skills behind [Datumwell Community](https://www.datumwell.io/community/?type=papers): discover distinct new benchmarks, then read the evidence behind them.

| Skill | Purpose | Entry point |
| --- | --- | --- |
| Benchmark Searcher | Verify new evaluation suites across arXiv, official projects and GitHub; distinguish release dates, deduplicate benchmark families and cite model scores. | [SKILL.md](benchmark-searcher/SKILL.md) |
| Paper Reader | Read the paper body, methods, evaluation tables and limitations before extracting source-grounded key points. | [SKILL.md](paper-reader/SKILL.md) |

## Download and install

Get individual ZIP files or the combined bundle from [GitHub Releases](https://github.com/Jiayi-Liao/datumwell-skills/releases) or the [Datumwell download section](https://www.datumwell.io/community/?type=papers#research-skills). The release includes SHA256SUMS for verifying downloaded files.

For Codex, unzip and copy the `benchmark-searcher` and/or `paper-reader` folders into `~/.codex/skills/` (or `$CODEX_HOME/skills/`). Each folder must contain its own `SKILL.md`; do not add an extra parent folder. Other compatible Agents can use the same skill folders in their documented skills location. Do not overwrite an existing modified installation without reviewing it first.

Benchmark Searcher's helper scripts require Python 3.10+, `curl` and IANA timezone data. For GitHub discovery, use an existing authenticated `gh` CLI, or the public REST API via `--transport curl`. Paper Reader contains instructions rather than a model client: it uses the Agent's available browsing/PDF tools. Neither skill bundles a model, API key or runtime service.

Examples:

```text
Use $benchmark-searcher to find new benchmarks from the latest seven calendar days.
Use $paper-reader to read this paper's full text and explain its methods, results and limitations: <paper URL>
```

Queries can be inspected without network calls:

```sh
python3 benchmark-searcher/scripts/fetch_arxiv.py --until YYYY-MM-DD --dry-run
python3 benchmark-searcher/scripts/fetch_github.py --until YYYY-MM-DD --query 'agent benchmark' --dry-run
```

Replace the date with your intended check date. `--dry-run` checks query construction, not source availability or research correctness.

## Behavior and boundaries

- Six discovery areas: robotics, Agents, long-horizon tasks, continual learning, personalization and 3D / Blender / CAD.
- Runtime evidence and the deduplication ledger belong in your workspace, outside the installed skill. No personal history or previously downloaded papers are included.
- Paper reviews require full text. Scores retain their source version, metric, units, evaluation conditions and limitations.
- Scheduling and publishing are configured separately in your Agent environment; installing these skills does not create a daily job or publish anything.
- Helper scripts use Python's standard library. The optional report renderer supports the legacy nine-column Markdown table format and is only used when a saved report is requested.

Run the offline helper tests with:

```sh
python3 -m unittest discover -s benchmark-searcher/scripts -p 'test_*.py'
```

## 中文说明

这两个 skill 分别负责「搜寻与核实新 benchmark」和「阅读全文、提取关键点」。解压后将对应文件夹放入 Agent 的 skills 目录即可。检索历史和原文证据保存在使用者自己的工作目录；下载包不包含私人数据、模型或密钥，也不会自动创建定时任务。

发布版本可在 `release.json` 中查看。问题与改进建议请通过 [GitHub Issues](https://github.com/Jiayi-Liao/datumwell-skills/issues) 提交。
