import copy
import json
import tempfile
import unittest
from pathlib import Path
import prototype as p


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_parent = (p.ROOT / "local_runs").resolve()
        cls.temp_parent.mkdir(exist_ok=True)

    def test_time_gate(self):
        self.assertFalse(p.eligible({"published_at": "2026-10-30"}, "2026-10-29"))
        self.assertTrue(p.eligible({"published_at": "2026-10-30"}, "2026-10-30"))
        self.assertFalse(p.eligible({}, "2026-11-15"))

    def test_zero_discount_recovery(self):
        self.assertEqual(p.capital_recovery_factor(0, 10), 0.1)

    def test_break_even_and_monotonicity(self):
        base = p.station_economics(10, 2000, .3, 1e6, 50000, .08, 10)
        q = base["break_even_kwh_per_site_day"]
        at_break_even = p.station_economics(10, q, .3, 1e6, 50000, .08, 10)
        self.assertAlmostEqual(at_break_even["annual_levelized_surplus_rmb_per_site"], 0, places=7)
        more = p.station_economics(10, q+1, .3, 1e6, 50000, .08, 10)
        self.assertGreater(more["annual_levelized_surplus_rmb_per_site"], 0)

    def test_zero_margin_no_finite_break_even(self):
        self.assertIsNone(p.station_economics(1, 100, 0, 1000, 50, .08, 10)["break_even_kwh_per_site_day"])

    def test_bad_scenarios(self):
        for margin in [-1, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                p.station_economics(1, 100, margin, 1000, 50, .08, 10)

    def test_reference_review_and_fabricated_citation(self):
        review = p.read_json(p.ROOT / "examples/byd_review.json")
        ids = {s["id"] for s in p.read_json(p.ROOT / "cases/byd/sources.json")}
        self.assertTrue(p.validate_review(review, ["P1","P2","P3","P4"], ids))
        review["assessments"][0]["citation_ids"].append("invented")
        with self.assertRaises(ValueError):
            p.validate_review(review, ["P1","P2","P3","P4"], ids)

    def test_missing_and_duplicate_propositions(self):
        review = p.read_json(p.ROOT / "examples/byd_review.json")
        ids = {s["id"] for s in p.read_json(p.ROOT / "cases/byd/sources.json")}
        for items in [review["assessments"][:-1], review["assessments"]+[review["assessments"][0]]]:
            edited = copy.deepcopy(review)
            edited["assessments"] = items
            with self.assertRaises(ValueError):
                p.validate_review(edited, ["P1","P2","P3","P4"], ids)

    def test_cutoff_filters_inputs_and_missing_is_not_zero(self):
        with tempfile.TemporaryDirectory(dir=self.temp_parent) as tmp:
            r = p.run(p.ROOT / "cases/byd", tmp, "2026-04-01")
            self.assertNotIn("q3_2026", r["source_gate"]["accepted"])
            self.assertNotIn("9M2026", [x["period"] for x in r["financials"]["rows"]])
            self.assertIsNone(r["utilization_estimate"])
            packet = json.loads((Path(tmp)/"evidence_packet.json").read_text(encoding="utf-8"))
            target = next(x for x in packet["network_observations"] if x["id"]=="target")
            self.assertEqual(target["status"], "target")

    def test_review_rejected_after_source_removal(self):
        with tempfile.TemporaryDirectory(dir=self.temp_parent) as tmp:
            with self.assertRaises(ValueError):
                p.run(p.ROOT / "cases/byd", tmp, review_path=p.ROOT / "examples/byd_review.json", drop_sources=["catl2026"])

    def test_financial_checks_and_semantic_mask(self):
        with tempfile.TemporaryDirectory(dir=self.temp_parent) as tmp:
            r = p.run(p.ROOT / "cases/byd", tmp, review_path=p.ROOT / "examples/byd_review.json")
            rows = {x["period"]:x for x in r["financials"]["rows"]}
            self.assertAlmostEqual(rows["FY2025"]["ocf_less_asset_cash_purchases_rmb_bn"], -97.672309)
            self.assertAlmostEqual(rows["9M2026"]["ocf_less_asset_cash_purchases_rmb_bn"], -32.909466)
            self.assertIsNone(rows["9M2025"]["revenue_rmb_bn"])
            self.assertEqual(len(r["grid"]), 48)
            f = json.loads((Path(tmp)/"feedback.json").read_text(encoding="utf-8"))
            self.assertTrue(all(x["mask"]==0 for x in f["semantic_items"]))
            self.assertEqual(r["source_gate"]["families"], ["BYD", "CATL"])


if __name__ == "__main__":
    unittest.main()
