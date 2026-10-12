# AGENTS.md

Python pipeline that forecasts next-day air raid alert activity for 23 units (Ukrainian oblast capitals).
You implement one task per session. The owner reviews, decides and commits.

## Read first, in this order

1. `docs/SPEC.md` — what the code must do. Never edit it.
2. `docs/DECISIONS.md` — settled choices; they override SPEC defaults.
3. `docs/PLAN.md` — tasks, scope, "Done when".
4. `docs/HANDOFF.md` — current state and next step.

## Rules

- Work only on the task ID you were given. Nothing from later tasks.
- Go prompt: restate the task in at most 3 lines, then implement. Start prompt: plan in at most 10 lines, then wait.
- Never commit, push, reset, or change git config. No global installs.
- Ask before network access, except the data download in `alerts/data.py`.
- Never edit `docs/SPEC.md` or tests written by an earlier task.
- If SPEC and DECISIONS leave a definition open, implement the most literal reading and list it under
  "Proposed decisions". Never decide a label, feature or evaluation definition silently.
- Problems outside the task go under "Open issues". Do not fix them.
- Two failed fix attempts on the same check: stop and report.
- Report only checks you ran in this session.

## Commands (PowerShell, venv in `.venv`)

```
python -m pip install -r requirements.txt
python -m pytest -q                          # synthetic data, no network, under 10 s
python run.py                                # audit, panel, backtest, forecast, report
python run.py <stage>                        # audit | panel | backtest | forecast | report
python run.py inspect <unit> <YYYY-MM-DD>    # raw records, episodes, labels for one unit-day
python run.py --raw-path <file>              # local source file instead of download
```

`run.py` prints a short summary per stage and exits non-zero on any failed assertion.

## Layout

```
run.py  requirements.txt  README.md
alerts/   config.py  data.py  episodes.py  labels.py  features.py  models.py  backtest.py  report.py
tests/    test_labels.py  test_leakage.py
notebooks/  01_eda.ipynb
data/raw/ (gitignored)  data/processed/
outputs/  outputs/figures/
docs/     SPEC.md  PLAN.md  DECISIONS.md  HANDOFF.md  prompts/
```

## Conventions

- Python 3.11+, pandas, NumPy, matplotlib, scikit-learn, pytest. Nothing else without asking.
- No frameworks: no MLflow, DVC, Hydra, Prefect, databases, web apps.
- Plain functions, DataFrame in and DataFrame out. File and network I/O only in `data.py`, `report.py`, `run.py`.
- Constants in `config.py`, never inline. Seed 42. Type hints and a one-line docstring on public functions.
- Charts: matplotlib PNG in `outputs/figures/`, dates on time axes, units on axis labels.
- Notebooks import from `alerts/`; no reported result may depend on notebook-only logic. First cell:

```
%load_ext autoreload
%autoreload 2
import sys; sys.path.insert(0, "..")
```

## Report (end of every implementation)

```
Task: T0X — <title>
Changed: <files, one line each>
pytest: <last line, verbatim>
run.py: <last 10 lines, verbatim>
Done-when evidence: <the numbers or facts the PLAN line asks for>
Proposed decisions: <each with a one-line reason, or "none">
Open issues: <or "none">
```

## Close (on the Close prompt)

- `docs/PLAN.md`: change only this task's status. `Done` only if the owner wrote "Approved".
- `docs/HANDOFF.md`: overwrite, keeping its headings.
- `docs/DECISIONS.md`: append only new choices made in this task, as
  `D-XX ... — Proposed`. Never restate, renumber or contradict an existing entry.
- Show the diff of `docs/` and stop.
