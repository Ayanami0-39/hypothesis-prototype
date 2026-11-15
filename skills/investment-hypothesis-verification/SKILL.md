---
name: investment-hypothesis-verification
description: Research and verify discretionary investment hypotheses against public evidence. Use to formalize a thesis, challenge proxy validity, compare evidence paths, diagnose conflicting results, and produce auditable assessments and feedback. Supports company, industry, and macroeconomic cases; not a trading or order-execution skill.
---

# Evidence-Grounded Verification for Investment Hypotheses

Turn a natural-language investment thesis into a scoped assessment that distinguishes
what is supported, contradicted, partly supported, and still unresolved. Use the host
agent's research and execution tools; the bundled Python helper only manages evidence
records, eligibility, dependencies and structured feedback. It does not replace economic
judgment or autonomously discover causal validity.

## Start with the actual question

Preserve the user's hypothesis, entity/market, information cutoff and horizon. Separate
descriptive, predictive, causal and valuation claims. Clarify ambiguity when it changes
the question; otherwise record the interpretation and continue. Do not turn business
success into a stock-return prediction without valuation and timing assumptions.

For a substantive case, create a case directory with the helper below and read
[the record format](references/schema.md). For a short conceptual question, use the
same reasoning without requiring files or a full experiment.

```sh
python <skill-dir>/scripts/verify.py init <case-dir> --id CASE_ID --as-of YYYY-MM-DD --horizon "declared horizon" --hypothesis "original thesis"
```

The initializer creates a starting proposition, not a completed formalization. Replace
it with the material clauses of the hypothesis; use as many propositions as needed.

## Research loop

1. **Formalize.** For each proposition record the target population, period, comparison,
   construct, intended estimand/decision criterion and assumptions. Preserve a pending
   criterion when no justified threshold exists; do not choose it after seeing results.
2. **Find evidence.** Retrieve public filings, official statistics, original studies and
   documented datasets using available host tools. Record source URL, release/revision
   vintage, locator, retrieval date and upstream source family. Identify company claims
   and management explanations as attributed statements. If access fails, record the gap.
3. **Challenge measurements.** State what each proxy measures and what it does not.
   Check entity, geography, cohorts, units, denominator, exposure window and data coverage.
   Correlation is not construct validity; a predictive proxy is not automatically an
   instrument. Read [research checks](references/research-checks.md) for causal or
   measurement-sensitive cases.
4. **Build useful paths.** Test different necessary implications, measurements or designs
   when feasible. Multiple URLs or model votes do not establish independence. Keep
   alternatives that survive validity checks, even when they weaken the thesis.
5. **Diagnose conflict.** Compare estimands and scope before combining results. Maintain
   competing explanations and choose a feasible follow-up that distinguishes them.
   Unresolved conflict stays unresolved; a plausible story alone is not a resolution.
6. **Revise locally.** When a measurement or assumption fails, reconsider dependent
   claims while preserving unrelated valid evidence. The helper can mark descendants
   stale for a supplied graph; the agent must infer and justify the graph and revisions.
7. **Deliver.** Report the original hypothesis, formalized clauses, evidence paths,
   calculations, conflict status, scoped conclusions and next discriminating observations.
   Separate published findings, executed calculations, scenarios and new inferences.

## Use the helper when a reproducible artifact is useful

```sh
python <skill-dir>/scripts/verify.py run --case <case-dir> --out <run-dir>
python <skill-dir>/scripts/verify.py run --case <case-dir> --out <reviewed-run-dir> --review <review.json>
```

The first command exports an evidence packet and a model-independent review prompt.
As the host agent, review the eligible source material, perform relevant calculations,
and write `review.json` following [the schema](references/schema.md); alternatively
give the prompt to another model or analyst. Do not supply an example answer as truth.
Record the actual authoring mode. Importing a review checks structure and references,
not entailment, identification or truth. Keep unadjudicated semantic feedback masked.

Calculations are optional and case-specific. Execute reviewed code explicitly, then
attach its JSON with `--calculations <file>`. Case data is never executable code and the
helper never automatically imports a case script. Calculations must declare source
lineage; source-derived records are excluded if any required source is ineligible.

For controlled diagnostics, use `--drop-source ID`, `--invalidate NODE_ID` or an earlier
`--as-of`. These are evidence-state perturbations, not economic interventions. An earlier
cutoff does not remove hindsight from how the case or its proxies were constructed.

## Evidence and feedback boundaries

- A claim can be supported within a limited population without the full thesis being true.
- Unknown and unsupported are distinct from contradicted. Avoid blanket abstention when
  narrower conclusions are justified.
- Use causal or statistical tests only with a defined target and credible assumptions;
  do not manufacture p-values, e-values or truth probabilities from textual judgments.
- Reward verified evidence operations separately from investment outcomes. Future results
  remain pending; reference preferences need independent adjudication before training.
- Use source-count and citation checks as diagnostics, not rewards for longer answers.
- A request to research does not by itself authorize publishing, trading, messaging,
  or installing this skill globally. Follow the user's actual scope.

The skill is company-independent and self-contained. Domain examples and economic
models belong in external case directories, not in this workflow or its defaults.
