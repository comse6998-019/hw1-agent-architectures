# hw1-agent-architectures

COMS E6998-019 HW1: build an agent that scans a pinned Python repository with
Bandit and labels each alert. The assignment is in
[briefs/hw1.pdf](briefs/hw1.pdf) (source: `briefs/hw1.tex`).

There is no starter code. You design and write every part of the agent.

| File | What it is |
|---|---|
| `briefs/hw1.pdf` | The assignment brief |
| `briefs/scan/*.toml` | The required `[scan]` block for each target |
| `briefs/report.example.json` | An example `report.json` (format only; its labels are not answers) |
| `config.example.toml` | The config your agent must read |
| `report.schema.json` | JSON Schema your `report.json` must validate against |
| `README.template.md` | Copy to `README.md` in your submission and fill in; it is graded |

Clone targets into `targets/` and write runs to `runs/`. Both are git-ignored.
