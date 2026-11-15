"""Tiny offline evidence harness. Python 3.10+, standard library only.

No hidden LLM call, autonomous verdict, training, or financial recommendation.
Export a prompt, use any model/analyst, then import its JSON for structural checks.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def eligible(source, cutoff):
    """A missing date is not decision-time eligible. Invalid dates fail loudly."""
    value = source.get("published_at")
    return bool(value) and date.fromisoformat(value) <= date.fromisoformat(cutoff)


def percent_change(new, old):
    if old == 0:
        raise ValueError("Cannot compute a growth rate with zero base")
    return 100 * (new / old - 1)


def capital_recovery_factor(rate, years):
    if rate < 0 or years <= 0:
        raise ValueError("Require nonnegative rate and positive life")
    return 1 / years if rate == 0 else rate / (1 - (1 + rate) ** -years)


def station_economics(stations, daily_kwh, margin, capital, fixed, rate, years):
    """Annual levelized, pre-tax BYD-attributable economics, constant mature use.

    Margin is retained contribution AFTER electricity, variable costs and partner
    share, BEFORE annual fixed cost and capital recovery. It is NOT the user tariff.
    Capital recovery includes principal recovery and required return: do not subtract
    depreciation again. This is not accounting net profit or a cash-flow forecast.
    """
    values = [stations, daily_kwh, margin, capital, fixed, rate, years]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("All scenario inputs must be finite")
    if min(stations, daily_kwh, margin, capital, fixed, rate) < 0 or years <= 0:
        raise ValueError("Invalid negative input or nonpositive life")
    recovery = capital * capital_recovery_factor(rate, years)
    contribution = 365 * daily_kwh * margin
    operating = contribution - fixed
    annual_surplus = operating - recovery
    break_even = (fixed + recovery) / (365 * margin) if margin > 0 else None
    return {
        "stations_assumed": stations,
        "daily_kwh_assumed": daily_kwh,
        "retained_margin_rmb_per_kwh_assumed": margin,
        "capital_at_risk_rmb_per_site_assumed": capital,
        "annual_capital_recovery_rmb_per_site": recovery,
        "annual_operating_cash_before_capital_rmb_per_site": operating,
        "annual_levelized_surplus_rmb_per_site": annual_surplus,
        "annual_network_levelized_surplus_rmb_bn": stations * annual_surplus / 1e9,
        "break_even_kwh_per_site_day": break_even,
        "interpretation": "illustrative_constant_mature_use_not_forecast_not_net_profit"
    }


def validate_review(review, proposition_ids, source_ids):
    """Structural validation only: valid citations do not prove entailment."""
    if not isinstance(review, dict) or not review.get("authoring_mode"):
        raise ValueError("Review needs an authoring_mode")
    items = review.get("assessments", [])
    ids = [a.get("proposition_id") for a in items]
    if len(ids) != len(set(ids)) or set(ids) != set(proposition_ids):
        raise ValueError("Need exactly one assessment per proposition")
    for item in items:
        if item.get("status") not in {"supported", "partial", "unresolved", "contradicted"}:
            raise ValueError("Invalid assessment status")
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError("Missing assessment rationale")
        if not isinstance(item.get("missing_evidence"), list):
            raise ValueError("Missing missing_evidence list")
    for item in items + review.get("conflicts", []):
        refs = item.get("citation_ids")
        if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
            raise ValueError("citation_ids must be a list of IDs")
        if set(refs) - set(source_ids):
            raise ValueError("Unknown or date-ineligible citation")
    return True


def compute_financials(rows, source_ids):
    kept = []
    for row in rows:
        if row["source_id"] not in source_ids:
            continue
        item = {k: (float(v) if v else None) for k, v in row.items()
                if k not in {"period", "source_id"}}
        item.update(period=row["period"], source_id=row["source_id"])
        ocf, capex = item["operating_cash_flow_rmb_bn"], item["long_term_asset_cash_purchases_rmb_bn"]
        item["ocf_less_asset_cash_purchases_rmb_bn"] = (
            ocf - capex if ocf is not None and capex is not None else None)
        kept.append(item)
    by_period = {r["period"]: r for r in kept}
    comparisons = []
    for old, new in [("FY2024", "FY2025"), ("9M2025", "9M2026"), ("Q3_2025", "Q3_2026")]:
        if old not in by_period or new not in by_period:
            continue
        for field in ["revenue_rmb_bn", "attributable_profit_rmb_bn",
                      "long_term_asset_cash_purchases_rmb_bn"]:
            a, b = by_period[old][field], by_period[new][field]
            if a is not None and b is not None:
                comparisons.append({"old": old, "new": new, "metric": field,
                                    "change_pct": percent_change(b, a)})
    return {"rows": kept, "comparisons": comparisons,
            "warning": "Group-level descriptive cash proxy; not charging capex, not FCFE, and not causal attribution. Missing cells remain null."}


def run(case_dir, output_dir, cutoff=None, review_path=None, drop_sources=()):
    case_dir, output_dir = Path(case_dir), Path(output_dir)
    case = read_json(case_dir / "case.json")
    cutoff = cutoff or case["as_of"]
    date.fromisoformat(cutoff)
    sources = read_json(case_dir / "sources.json")
    if len({s["id"] for s in sources}) != len(sources):
        raise ValueError("Duplicate source IDs")
    if set(drop_sources) - {s["id"] for s in sources}:
        raise ValueError("Unknown source requested for removal")
    accepted = [s for s in sources if eligible(s, cutoff) and s["id"] not in drop_sources]
    accepted_ids = {s["id"] for s in accepted}
    with (case_dir / "financials.csv").open(encoding="utf-8", newline="") as f:
        financials = compute_financials(list(csv.DictReader(f)), accepted_ids)
    paths = [{**p, "eligible_source_ids": [s for s in p["source_ids"] if s in accepted_ids],
              "source_families": sorted({s["family"] for s in accepted if s["id"] in p["source_ids"]})}
             for p in case["paths"]]
    # An announced future target is eligible information, but stays a target.
    observations = [o for o in case["network_observations"] if o["source_id"] in accepted_ids]
    assumptions = case["scenario_assumptions"]
    def scenario(q, m, capital=None):
        return station_economics(assumptions["stations"], q, m,
            assumptions["capital_at_risk_rmb_per_site"] if capital is None else capital,
            assumptions["fixed_cash_cost_rmb_per_site_year"],
            assumptions["hurdle_rate"], assumptions["life_years"])
    scenarios = [{"name": x["name"], **scenario(x["kwh_per_site_day"], x["retained_contribution_rmb_per_kwh"])}
                 for x in assumptions["illustrations"]]
    grid = [scenario(q, m, k) for k in assumptions["grid_capital_at_risk_rmb_per_site"]
            for q in assumptions["grid_kwh_per_site_day"]
            for m in assumptions["grid_retained_contribution_rmb_per_kwh"]]
    review = read_json(review_path) if review_path else None
    if review:
        validate_review(review, [p["id"] for p in case["propositions"]], accepted_ids)
    input_paths = [case_dir / n for n in ["case.json", "sources.json", "financials.csv"]]
    input_paths += [ROOT / "prototype.py", ROOT / "prompts/research.md"]
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}
    if review_path:
        hashes["review_input"] = hashlib.sha256(Path(review_path).read_bytes()).hexdigest()
    packet = {"case_id": case["id"], "as_of": cutoff, "hypothesis": case["hypothesis"],
              "horizon": case["horizon"], "interpretation": case["interpretation"],
              "propositions": case["propositions"], "sources": accepted, "paths": paths,
              "financials": financials, "network_observations": observations,
              "scenario_assumptions": assumptions, "scenario_results": scenarios,
              "missing_data": case["missing_data"],
              "provenance": "Manually transcribed public sources; analyst-specified propositions and scenarios. Not raw retrieval or independent measurement."}
    results = {"case_id": case["id"], "as_of": cutoff,
               "execution": "offline_calculation_and_review_validation; no model was called",
               "input_sha256": hashes,
               "source_gate": {"accepted": sorted(accepted_ids),
                 "excluded": sorted({s["id"] for s in sources} - accepted_ids),
                 "families": sorted({s["family"] for s in accepted})},
               "financials": financials, "scenarios": scenarios, "grid": grid,
               "utilization_estimate": None,
               "utilization_reason": "Cumulative energy and end-date station count do not supply operating station-days or station cohorts.",
               "review": review, "thesis_truth_label": None}
    feedback = {"case_id": case["id"], "thesis_truth_label": None,
        "items": [{"channel": "executable", "target": "review_schema_and_eligible_citation_ids",
                   "label": "pass" if review else None, "mask": int(review is not None),
                   "scope": "Structural correctness only; does not certify factual extraction or entailment"}],
        "semantic_items": [{"target": a["proposition_id"], "candidate_label": a["status"],
                            "label_source": review["authoring_mode"], "mask": 0,
                            "weight": None, "reason": "Requires independent adjudication"}
                           for a in (review or {}).get("assessments", [])]}
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in [("evidence_packet.json", packet), ("results.json", results), ("feedback.json", feedback)]:
        (output_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    prompt = (ROOT / "prompts/research.md").read_text(encoding="utf-8")
    (output_dir / "review_prompt.md").write_text(prompt + "\nEvidence packet:\n```json\n" +
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(grid[0]))
    writer.writeheader()
    writer.writerows(grid)
    (output_dir / "scenario_grid.csv").write_text(out.getvalue(), encoding="utf-8")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=ROOT / "cases/byd")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/byd")
    parser.add_argument("--as-of", help="Public release cutoff, YYYY-MM-DD")
    parser.add_argument("--review", type=Path, help="External model/analyst JSON; never auto-scored as truth")
    parser.add_argument("--drop-source", action="append", default=[], help="Source removal diagnostic")
    args = parser.parse_args()
    result = run(args.case, args.out, args.as_of, args.review, args.drop_source)
    print(json.dumps({"case": result["case_id"], "as_of": result["as_of"],
        "eligible_sources": len(result["source_gate"]["accepted"]),
        "scenario_grid_rows": len(result["grid"]), "model_called": False,
        "review_imported": result["review"] is not None}, indent=2))
