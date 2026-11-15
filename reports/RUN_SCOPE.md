# Execution record

- Research information cutoff and run date: 2026-11-15 (Asia/Singapore).
- Exploratory, retrospective public-source review; no preregistered investment prediction.
- Runtime: Python 3.12; standard library only. Supported Python: 3.10+.
- Command: `python prototype.py --review examples/byd_review.json`.
- Implementation checks: `python -m unittest discover -s tests -v` (10 passed).
- Six public source records; two upstream source families (BYD and CATL).
- 48 illustrative parameter combinations, not independent economic observations.
- No external LLM API called by the executable. The example assessment and report are assistant-authored research artifacts. No blind trial, baseline comparison, model training, or calibrated truth reward.
- The initial test invocation hit an environment temporary-directory permission problem. Tests now use a temporary directory inside the ignored local_runs directory; the complete suite then passed.
- Inputs were already researched before scenario design. Scenario settings are exploratory assumptions, not precommitted estimands or market estimates.
- Publication includes only project files; no credentials, local browser history, private proposal text, or private user files.
- Re-running the default command without --review intentionally yields no semantic assessment. Use the reproduction command above to regenerate the committed demonstration.
