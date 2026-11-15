"""Synthetic retail diagnostics; no empirical retail-investment claims."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/investment-hypothesis-verification"


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v = module_at("verify", SKILL / "scripts/verify.py")
byd = module_at("byd_calculation", ROOT / "cases/byd/calculate.py")


class GenericTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "local_runs"
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = self.root / "retail"
        self.case.mkdir()
        self.out = self.root / "out"
        self.data = {
            "schema_version": 2, "id": "synthetic_retail", "as_of": "2025-12-31",
            "hypothesis": "Warehouse automation improves inventory efficiency and cash conversion.",
            "horizon": "2026-2028",
            "propositions": [
                {"id": "stock_efficiency", "claim": "Inventory efficiency improves.", "obligations": ["Control product mix"]},
                {"id": "cash_conversion", "claim": "Cash conversion improves.", "obligations": ["Observe working capital"]}],
            "measurements": [{"id": "turnover_proxy", "construct": "inventory efficiency"}],
            "dependencies": [["stock_record", "turnover_proxy"], ["turnover_proxy", "stock_efficiency"]],
            "paths": [{"id": "inventory", "target": "stock_efficiency", "source_ids": ["old", "future"]},
                      {"id": "cash", "target": "cash_conversion", "source_ids": ["replica"]}]}
        self.sources = [
            {"id": key, "title": "SYNTHETIC fixture " + key, "url": "https://example.invalid/"+key,
             "published_at": published, "family": "same_synthetic_origin", "kind": "synthetic",
             "summary": "Invented software-test record; not empirical evidence."}
            for key, published in [("old", "2025-10-01"), ("future", "2026-01-01"),
                                   ("unknown", None), ("replica", "2025-11-01")]]
        self.obs = [{"id": "stock_record", "basis": "synthetic", "source_ids": ["old"],
                     "text": "Invented inventory observation"},
                    {"id": "later_record", "basis": "synthetic", "source_ids": ["future"],
                     "text": "Invented future observation"}]
        self.review = {"authoring_mode": "synthetic_test_fixture", "assessments": [
            {"proposition_id": p["id"], "status": "partial", "citation_ids": ["old"],
             "reason": "Synthetic structural test only.", "missing_evidence": ["Empirical data"]}
            for p in self.data["propositions"]], "conflicts": [], "next_actions": []}
        self.save()

    def save(self):
        for name, data in [("case.json", self.data), ("sources.json", self.sources),
                           ("observations.json", self.obs), ("review.json", self.review)]:
            v.write_json(self.case / name, data)

    def test_generic_case_needs_no_industry_fields(self):
        result = v.run(self.case, self.out)
        packet = v.read_json(self.out / "evidence_packet.json")
        self.assertEqual([p["id"] for p in packet["propositions"]], ["stock_efficiency", "cash_conversion"])
        self.assertEqual(packet["calculations"], [])
        self.assertIsNone(result["thesis_truth_label"])
        self.assertEqual(len(result["source_gate"]["families"]), 1)
        self.assertEqual(packet["paths"][0]["eligible_source_ids"], ["old"])

    def test_date_unknown_and_future_gate(self):
        result = v.run(self.case, self.out)
        reasons = {x["id"]: x["reason"] for x in result["source_gate"]["excluded"]}
        self.assertEqual(reasons, {"future": "after_cutoff", "unknown": "missing_release_date"})
        self.assertEqual(result["excluded_observation_ids"], ["later_record"])
        self.assertTrue(v.eligible({"published_at": "2025-12-31"}, "2025-12-31"))

    def test_calculation_requires_all_inputs_eligible(self):
        path = self.root / "calculations.json"
        v.write_json(path, [{"id": "change", "basis": "source_calculation", "source_ids": ["old", "future"],
                             "text": "Synthetic test of source-lineage gate", "value": 10}])
        result = v.run(self.case, self.out, calculations_path=path)
        self.assertEqual(result["excluded_calculation_ids"], ["change"])
        self.assertEqual(v.read_json(self.out / "evidence_packet.json")["calculations"], [])

    def test_source_derived_record_cannot_omit_lineage(self):
        with self.assertRaisesRegex(ValueError, "lineage"):
            v.validate_records([{"id": "x", "text": "x", "basis": "source_calculation", "source_ids": []}], {}, True)

    def test_illustration_requires_assumptions(self):
        record = {"id": "x", "text": "x", "basis": "illustrative", "source_ids": []}
        with self.assertRaisesRegex(ValueError, "assumptions"):
            v.validate_records([record], {}, True)
        record["assumptions"] = {"hypothetical_growth": 0.1}
        v.validate_records([record], {}, True)

    def test_local_invalidation_preserves_unrelated_claim(self):
        result = v.run(self.case, self.out, invalidate=["turnover_proxy"], review_path=self.case / "review.json")
        self.assertIn("stock_efficiency", result["stale_nodes"])
        self.assertNotIn("cash_conversion", result["stale_nodes"])
        feedback = v.read_json(self.out / "feedback.json")
        items = {i["target"]: i for i in feedback["semantic_items"]}
        self.assertTrue(items["stock_efficiency"]["requires_reassessment"])
        self.assertFalse(items["cash_conversion"]["requires_reassessment"])
        self.assertTrue(all(i["mask"] == 0 for i in items.values()))

    def test_source_removal_propagates_through_observation(self):
        result = v.run(self.case, self.out, drop_sources=["old"])
        self.assertTrue({"stock_record", "turnover_proxy", "stock_efficiency"} <= set(result["stale_nodes"]))
        self.assertNotIn("cash_conversion", result["stale_nodes"])

    def test_old_review_cannot_use_removed_or_future_source(self):
        with self.assertRaises(ValueError):
            v.run(self.case, self.out, review_path=self.case / "review.json", drop_sources=["old"])
        self.review["assessments"][0]["citation_ids"] = ["future"]
        self.save()
        with self.assertRaises(ValueError):
            v.run(self.case, self.out, review_path=self.case / "review.json")

    def test_review_must_cover_arbitrary_ids_exactly_once(self):
        for items in [self.review["assessments"][:1], self.review["assessments"] * 2]:
            bad = copy.deepcopy(self.review)
            bad["assessments"] = items
            with self.assertRaises(ValueError):
                v.validate_review(bad, ["stock_efficiency", "cash_conversion"], ["old"])
        self.assertTrue(v.validate_review(self.review, ["stock_efficiency", "cash_conversion"], ["old"]))

    def test_schema_pass_is_not_semantic_truth(self):
        self.review["assessments"][0]["status"] = "supported"
        self.save()
        result = v.run(self.case, self.out, review_path=self.case / "review.json")
        feedback = v.read_json(self.out / "feedback.json")
        self.assertEqual(feedback["items"][0]["mask"], 1)
        self.assertTrue(all(i["mask"] == 0 and i["weight"] is None for i in feedback["semantic_items"]))
        self.assertIsNone(result["thesis_truth_label"])

    def test_cycle_and_unknown_node_rejected(self):
        for edges in [[["a", "b"], ["b", "a"]], [["a", "unknown"]]]:
            with self.assertRaises(ValueError):
                v.validate_graph(edges, {"a", "b"})

    def test_duplicate_ids_and_unknown_citations_rejected(self):
        self.sources.append(copy.deepcopy(self.sources[0]))
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate ID"):
            v.run(self.case, self.out)
        self.sources.pop()
        self.obs[0]["source_ids"] = ["invented"]
        self.save()
        with self.assertRaisesRegex(ValueError, "Unknown"):
            v.run(self.case, self.out)

    def test_empty_case_initialization_and_no_overwrite(self):
        new = self.root / "new"
        v.init_case(new, "NEW", "A test claim", "2025-12-31", "2026")
        result = v.run(new, self.out)
        self.assertEqual(result["source_gate"]["accepted"], [])
        self.assertIsNone(v.read_json(self.out / "feedback.json")["items"][0]["label"])
        with self.assertRaises(ValueError):
            v.init_case(new, "NEW", "Another claim", "2025-12-31", "2026")

    def test_nonfinite_json_rejected(self):
        path = self.root / "bad.json"
        for value in ["NaN", "Infinity", "-Infinity"]:
            path.write_text('{"value": '+value+'}', encoding="utf-8")
            with self.assertRaises(ValueError):
                v.read_json(path)

    def test_copied_skill_runs_without_repository_or_byd(self):
        destination = self.root / "standalone"
        shutil.copytree(SKILL, destination, ignore=shutil.ignore_patterns("__pycache__"))
        command = [sys.executable, str(destination / "scripts/verify.py")]
        case = self.root / "standalone-case"
        init = subprocess.run(command + ["init", str(case), "--id", "SAAS_RETENTION", "--as-of", "2025-12-31",
            "--horizon", "2026-2028", "--hypothesis", "Retention improves unit economics"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(init.returncode, 0, init.stderr)
        run = subprocess.run(command + ["run", "--case", str(case), "--out", str(self.out)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["case"], "SAAS_RETENTION")


class BYDRegressionTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "local_runs"
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)

    def test_original_arithmetic_and_generic_review(self):
        result = byd.calculate(self.out)
        rows = {x["period"]: x for x in result["financials"]["rows"]}
        self.assertAlmostEqual(rows["FY2025"]["ocf_less_asset_cash_purchases_rmb_bn"], -97.672309)
        self.assertAlmostEqual(rows["9M2026"]["ocf_less_asset_cash_purchases_rmb_bn"], -32.909466)
        self.assertIsNone(rows["9M2025"]["revenue_rmb_bn"])
        self.assertEqual(len(result["grid"]), 48)
        expected = [-2.885589773941507, 1.494410226058493, 12.444410226058494]
        for row, value in zip(result["scenarios"], expected):
            self.assertAlmostEqual(row["annual_network_levelized_surplus_rmb_bn"], value)
        self.assertAlmostEqual(result["scenarios"][1]["break_even_kwh_per_site_day"], 1817.6209013431537)
        r = v.run(ROOT / "cases/byd", self.out / "verification",
                  calculations_path=self.out / "calculations.json", review_path=ROOT / "cases/byd/review.example.json")
        self.assertEqual(r["source_gate"]["families"], ["BYD", "CATL"])

    def test_historical_gate_keeps_target_distinct(self):
        byd.calculate(self.out)
        v.run(ROOT / "cases/byd", self.out / "verification", cutoff="2026-04-01", calculations_path=self.out / "calculations.json")
        packet = v.read_json(self.out / "verification/evidence_packet.json")
        self.assertNotIn("F_9M2026", [x["id"] for x in packet["calculations"]])
        target = next(x for x in packet["observations"] if x["id"] == "target")
        self.assertEqual(target["basis"], "target")

    def test_economic_boundaries_and_break_even(self):
        self.assertEqual(byd.capital_recovery_factor(0, 10), .1)
        self.assertIsNone(byd.station_economics(1, 100, 0, 1000, 50, .08, 10)["break_even_kwh_per_site_day"])
        base = byd.station_economics(10, 2000, .3, 1e6, 50000, .08, 10)
        q = base["break_even_kwh_per_site_day"]
        self.assertAlmostEqual(byd.station_economics(10, q, .3, 1e6, 50000, .08, 10)["annual_levelized_surplus_rmb_per_site"], 0, places=7)
        for invalid in [-1, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                byd.station_economics(1, 100, invalid, 1000, 50, .08, 10)


if __name__ == "__main__":
    unittest.main()
