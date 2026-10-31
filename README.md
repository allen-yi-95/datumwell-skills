# Datumwell Research Skills

Two portable Agent skills behind [Datumwell Community](https://www.datumwell.io/community/?type=papers): discover interesting topics in the latest frontier AI papers, then read the full-text evidence.

| Skill | Purpose | Entry point |
| --- | --- | --- |
| Paper Search | Discover recent papers across models, reasoning, multimodal AI, systems, safety, data, benchmarks and application research; verify contributions, dates and evidence without repeats. | [SKILL.md](paper-search/SKILL.md) |
| Paper Reader | Read the paper body, methods, evaluation tables and limitations before extracting source-grounded key points. | [SKILL.md](paper-reader/SKILL.md) |

## Download and install

Get individual ZIP files or the combined bundle from [GitHub Releases](https://github.com/allen-yi-95/datumwell-skills/releases/latest) or [Datumwell](https://www.datumwell.io/community/?type=papers#research-skills). Verify downloads using SHA256SUMS.

For Codex, unzip and place the `paper-search` and/or `paper-reader` folders directly in `~/.codex/skills/` (or `$CODEX_HOME/skills/`). Each folder must contain its own SKILL.md. Other compatible Agents use their documented skills directory.

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

## Customize your research

Edit the skill instructions and helper scripts to fit your own interests:

- **For one search:** tell your Agent which topics, date window, language and level of detail you want. For example: “Focus on robotics and VLA papers from the last three days; explain each in Chinese with three key points.”
- **For ongoing preferences:** edit `paper-search/SKILL.md` and `paper-reader/SKILL.md` to set research interests, selection/ranking rules, reading depth and output format.
- **For new search routes:** update the categories and keywords in `paper-search/scripts/fetch_arxiv.py`; choose corresponding GitHub queries. Changing the written scope alone does not add keywords to the fetcher.
- **For recurring discovery:** configure the schedule in your own Agent environment. Keep your customized files when installing later updates.

## Scope and evidence

- Broad frontier AI research: models/reasoning, multimodal AI, systems, safety, data/evaluation, robotics, agents, long-horizon tasks, continual learning, personalization and 3D/CAD. A new benchmark is not required.
- Prioritize substantive contributions and evidence, not stars or a quota for every field. Keep release dates distinct from revisions and repository activity.
- Read full texts; retain methods, exact metrics, conditions, source sections/tables and limitations. Do not repeat abstracts as reviews.
- Research evidence and search history stay in your own workspace, outside the installed skill.
- Use the skills on demand or connect them to your Agent’s scheduled tasks for ongoing research discovery.
- The optional renderer supports legacy nine-column reports only when explicitly requested; normal findings appear in chat.

## 中文说明

Paper Search 从每日最新的前沿 AI 论文中寻找值得关注的话题，范围包含模型、推理、多模态、系统、安全、数据与 benchmark，以及机器人、Agents、长时任务、持续学习、个性化和 3D/CAD。Paper Reader 负责阅读全文，提取带来源的贡献、方法、结果与局限。

下载后可查看和修改源码，按你的研究兴趣定制关注领域、筛选规则、阅读深度、语言与输出格式。单次搜索时直接告诉 Agent 你的偏好；长期使用可编辑对应的 SKILL.md，新增自动检索方向时同步调整辅助脚本的关键词与分类。可单次调用，也可配合 Agent 的定时任务持续追踪。反馈可提交到 [GitHub Issues](https://github.com/allen-yi-95/datumwell-skills/issues)。
