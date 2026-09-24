<!--
HW1 README template. Copy this file to README.md and fill in every section.
A grading skill reads README.md, so:
- keep every ## and ### heading exactly as written, in this order;
- add your own headings only as ### inside a section (not inside ## Run);
- put every command in a fenced block tagged sh, one command per line,
  with no $ prompt, no output, no placeholders like <...>, and nothing interactive;
- run every command from the repository root; use repo-relative paths;
- read secrets only from environment variables listed under ## Requirements.
Delete nothing but these comments.
-->

## Team
<!-- Each member's name and UNI. Then the full 40-character commit SHA of the submitted code. -->

## Requirements
<!--
The operating system(s) you tested on. Language and runtime versions.
How Python 3.12 and Bandit 1.9.4 are installed. The model provider and exact model name.
A table with columns Variable, Purpose, listing every environment variable your agent reads.
Never write a value.
-->

## Setup
<!--
One sh block that takes a fresh clone to a ready state: dependencies installed and
Bandit 1.9.4 on the path. The last line prints the Bandit version, for example:
bandit --version
-->

## Fetch targets
<!--
One sh block that clones the three targets into targets/radicale, targets/sglang and
targets/owasp-benchmark-python, checks out the pinned commits from the brief, and
prints git rev-parse HEAD for each.
-->

## Configs
<!--
A table with columns Target, Config file. One row for each target and one row for the
budget-cutoff run. Commit every config file. Each [scan] block must equal the brief's
required block for that target.
-->

## Run
<!--
Four subsections, in this order. Each holds one sh block with one agent command of the form
./their-agent --input targets/radicale --output runs/radicale --config configs/radicale.toml
Output directories: runs/radicale, runs/sglang, runs/owasp-benchmark-python, runs/radicale-cutoff.
Under each block, give the observed wall-clock time and used_tokens.
-->

### Radicale
<!-- Output: runs/radicale -->

### SGLang
<!-- Output: runs/sglang -->

### OWASP BenchmarkPython
<!-- Output: runs/owasp-benchmark-python -->

### Budget cutoff
<!--
Output: runs/radicale-cutoff. The Radicale target with a config whose max_tokens is small
enough that at least one row has status budget_exhausted.
-->

## Outputs
<!--
A table with columns Run, Directory, alert_count, label_1, label_0, null, used_tokens, exhausted.
One row for each run above. Every value must equal the committed report.json in that directory.
-->

## Validate
<!--
One sh block that validates every committed report.json against report.schema.json and exits
non-zero if any fails.
-->

## Trajectory
<!--
One sh block with one command that renders the trajectory of one alert from
runs/radicale/trace.jsonl as a Mermaid sequenceDiagram, using the trace alone.
Then paste the rendered diagram in a fenced block tagged mermaid.
-->

## Rubric map
<!--
A table with columns Item, Where. One row for each item, in this order:
A1 A2 A3 A4 A5 A6 A7 B1 B2 B3 B4 B5 B6 B7 B8 B9 B10 C1 C2 C3.
For B items, Where is path:line or path:start-end in your code.
For A and C items, Where is a section heading in your report.
-->

## Known issues
<!-- Anything that does not work, failed runs, and deviations from the brief. Write None. if there are none. -->
