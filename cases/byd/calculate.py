"""BYD-specific calculations, deliberately outside the reusable skill."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")

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

def calculate(output_dir=None):
    output_dir = Path(output_dir) if output_dir else HERE / "outputs"
    with (HERE / "financials.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    financials = compute_financials(rows, {r["source_id"] for r in rows})
    settings = read_json(HERE / "scenario.json")
    def scenario(q,m,k=None):
        return station_economics(settings["stations"],q,m,
            settings["capital_at_risk_rmb_per_site"] if k is None else k,
            settings["fixed_cash_cost_rmb_per_site_year"],settings["hurdle_rate"],settings["life_years"])
    scenarios = [{"name":x["name"], **scenario(x["kwh_per_site_day"],x["retained_contribution_rmb_per_kwh"])} for x in settings["illustrations"]]
    grid = [scenario(q,m,k) for k in settings["grid_capital_at_risk_rmb_per_site"]
            for q in settings["grid_kwh_per_site_day"] for m in settings["grid_retained_contribution_rmb_per_kwh"]]
    records = []
    by_period = {r["period"]:r for r in financials["rows"]}
    for row in financials["rows"]:
        records.append({"id":"F_"+row["period"],"basis":"source_calculation",
            "source_ids":[row["source_id"]],"text":"Group financial inputs and OCF minus long-term-asset cash purchases; not charging capex or FCFE.",
            "value":row,"unit":"RMB billion","method":"CSV transcription and arithmetic; missing cells stay null"})
    for i,comparison in enumerate(financials["comparisons"]):
        refs = sorted({by_period[comparison["old"]]["source_id"],by_period[comparison["new"]]["source_id"]})
        records.append({"id":"G_"+str(i),"basis":"source_calculation","source_ids":refs,
                        "text":"Matched-period descriptive growth, not a causal effect.","value":comparison,"unit":"percent"})
    for result in scenarios:
        records.append({"id":"SC_"+result["name"],"basis":"illustrative","source_ids":[],
            "text":"Hypothetical mature network, not an observed deployment or forecast.",
            "value":result,"assumptions":settings})
    hashes = {n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['financials.csv','scenario.json','calculate.py']}
    for item in records:
        item["input_sha256"] = hashes
    output_dir.mkdir(parents=True,exist_ok=True)
    result = {"execution":"BYD_specific_deterministic_calculation_no_model", "financials":financials,
              "scenarios":scenarios,"grid":grid,"input_sha256":hashes}
    write_json(output_dir/"calculation_results.json",result)
    write_json(output_dir/"calculations.json",records)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(grid[0]),lineterminator="\n")
    writer.writeheader(); writer.writerows(grid)
    (output_dir/"scenario_grid.csv").write_text(output.getvalue(),encoding="utf-8",newline="\n")
    return result

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=HERE/'outputs')
    args=parser.parse_args()
    result=calculate(args.out)
    print(json.dumps({"scenario_grid_rows":len(result["grid"]),"model_called":False}))
