# Case and review format (version 2)

Required inputs: `case.json` and `sources.json`. Optional input: `observations.json`.
No company, fiscal year, financial column or economic formula is hard-coded.
All dates are ISO `YYYY-MM-DD`. Files use UTF-8 and finite JSON numbers (no NaN).

## case.json

```json
{
  "id": "RETAIL_EXAMPLE",
  "as_of": "2026-11-15",
  "hypothesis": "A retailer's inventory changes improve cash generation.",
  "horizon": "next fiscal year",
  "propositions": [
    {"id":"P1", "claim":"Inventory days fall for comparable stores.",
     "obligations":["Check store coverage and seasonality"],
     "claim_type":"descriptive", "population":"comparable stores",
     "period":"next fiscal year", "comparison":"previous fiscal year",
     "criterion":"unresolved until materiality is specified"}
  ],
  "measurements":[{"id":"M1", "construct":"inventory efficiency", "proxy":"inventory days", "limitations":"supply shortages can mimic improvement"}],
  "paths":[{"id":"operations", "target":"inventory efficiency", "source_ids":["S1"], "limitations":"one reporting family"}],
  "dependencies":[["O1","M1"],["M1","P1"]],
  "missing_data":["comparable-store stockout rate"]
}
```

Required case fields: id, as_of, hypothesis, horizon, and a nonempty propositions list.
Each proposition needs a unique id, claim and an obligations list. Other formalization
fields are optional to preserve genuine ambiguity, but the agent should fill material
ones. Optional measurements have unique id and construct. Dependencies link observation,
measurement and proposition IDs and must form a DAG. They are analyst/agent declarations,
not automatically discovered causal relationships. Different numbers of propositions
and paths are allowed; no minimum number of evidence paths is imposed by the parser.

## sources.json

A list of `{id, title, url, published_at, family, kind, summary}`. Use original public
URLs; `kind` should identify audited/unaudited filings, company statements, research,
statistics, etc. `published_at: null` quarantines unknown availability. Add `retrieved_at`
and `locator` for traceability. `family` is upstream provenance, not the website hostname.
For synthetic fixtures, explicitly mark kind as synthetic and use an example.invalid URL.

## observations.json and optional calculations

Both are lists of records:

```json
[{"id":"O1", "basis":"reported", "source_ids":["S1"],
  "text":"Inventory days reported for a specified population.",
  "value":42, "unit":"days", "period":"fiscal year", "population":"specified stores"}]
```

Observations use basis `reported`, `target`, `assumption` or `synthetic`.
Calculations supplied with `--calculations` use `source_calculation`, `illustrative` or
`synthetic`. All need id, basis, text, source_ids; value, unit, method, assumptions and
code/input hashes are optional. Reported/target/source_calculation records need at least
one source ID. Illustrations must identify their assumptions, not pretend to be observed.
Value may be a scalar, object or list. Unknown values are null, never zero by default.
Every listed source must exist, and ALL must be cutoff-eligible for the record to enter
the packet. A previously announced target can concern a future horizon; it remains a
target, not an observed future outcome. Preserve raw observations when invalidating a
measurement link; flag the dependent inference instead of silently deleting history.

## review.json

```json
{
  "authoring_mode":"host_agent_research_draft",
  "assessments":[
    {"proposition_id":"P1", "status":"unresolved", "citation_ids":["S1"],
     "reason":"Reporting population does not yet match the target.",
     "missing_evidence":["comparable-store data"]}
  ],
  "conflicts":[{"description":"...", "explanation":"...", "status":"unresolved", "citation_ids":["S1"]}],
  "next_actions":["Obtain a matched reporting population"]
}
```

Exactly one assessment per declared proposition. Status: supported, partial, unresolved,
contradicted. Decisive/partial assessments require citations. Conflict status:
resolved_scope or unresolved. Citation IDs refer to source IDs, not calculation IDs.
The parser checks completeness, allowed values and eligible citations, NOT whether an
explanation resolves a conflict or a source entails a claim. A supplied review cannot
turn a structurally valid claim into a verified economic fact.

## Outputs

- `evidence_packet.json`: eligible evidence, optional calculations and dependency flags.
- `review_prompt.md`: generic prompt plus packet; no example answer included.
- `results.json`: eligibility audit, source-family counts, stale descendants, optional
  review and input hashes. An imported review remains in its original authoring mode.
- `feedback.json`: executable structure checks separated from semantic candidates;
  semantic masks remain zero and reliability weights null pending independent review.

`--invalidate NODE` marks that node and its descendants for review. Removing an upstream
source also marks excluded observations and their descendants. These are mechanical
consequences of the supplied graph; neither action changes the economic truth label.
No template, historical source replay or synthetic fixture is a prospective prediction.
