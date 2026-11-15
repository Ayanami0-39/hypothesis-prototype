# Execution scope

The reusable artifact is `skills/investment-hypothesis-verification/`. It contains a research workflow for the host agent and a Python standard-library helper. The root `prototype.py` delegates to that helper. BYD-specific data, formulas, review and report live under `cases/byd/`.

## What actually runs

- Local parsing, explicit source-date eligibility, source-lineage filtering, dependency validation and downstream invalidation.
- Validation of a supplied review's structure and eligible citation IDs; no semantic entailment certification.
- Input SHA-256 fingerprints and machine-readable evidence, diagnostic and feedback outputs.
- Separately invoked BYD financial arithmetic, capital-recovery calculations and a 48-row illustrative sensitivity grid.

The helper makes no model or network calls. A supplied review remains attributed to its declared authoring mode. The skill instructs the host agent to perform research and interpretation; it is not evidence of a tested autonomous research system. Source publication dates and families are declared records, not independently authenticated by the helper.

## Verification protocol

`python -m unittest discover -s tests -v` exercises a synthetic retail hypothesis with arbitrary proposition IDs, date/lineage filtering, invalid and incomplete reviews, cycle rejection, selective invalidation, masked semantic labels and a standalone copied skill. These are software diagnostics, not empirical investment-validation performance. Separate BYD regressions check preservation of previous arithmetic and missing-value behavior.

## Interpretation limits

- Source eligibility is necessary but insufficient for historical availability: vintage, revisions, observation dates and later interpretation still require audit.
- Distinct source families or pathways do not prove statistical independence. No p-values or e-values are aggregated.
- Dependency edges are analyst-declared, not learned causal edges. Missing edges prevent complete invalidation propagation.
- Schema-valid reviews may still be economically wrong. Executable feedback targets format and citation eligibility only; semantic candidate labels have mask 0 and no calibrated weight.
- An illustrative calculation without source references is permitted only with explicit assumptions. It does not become empirical evidence by entering the packet.
- The BYD case is a preserved dated case study. Refactoring the repository does not refresh its underlying public disclosures or establish future excess returns.
