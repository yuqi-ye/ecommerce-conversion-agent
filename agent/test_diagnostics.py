import csv
from pathlib import Path
import unittest
from analysis_tools import summarize_rows
from diagnostics import summarize_breakdown

ROOT = Path(__file__).resolve().parents[1]

class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.comparison=summarize_rows("2020-12-21",[
            ("2020-12-14",24173,338),("2020-12-21",16984,124)])
        with (ROOT/"data/processed/source_device_comparisonL.csv").open(encoding="utf-8-sig",newline="") as f:
            self.rows=[tuple(r[:4])+tuple(map(int,r[4:])) for r in csv.reader(f)]
    def test_verified_case(self):
        result=summarize_breakdown("2020-12-21",self.rows,self.comparison)
        self.assertEqual(result["group_count"],47)
        self.assertAlmostEqual(result["source"]["mix_change_pp"],0.0003202458404091542)
        self.assertAlmostEqual(result["source"]["within_change_pp"],-0.6684755798231802)
        top=result["source"]["groups"][0]
        self.assertEqual((top["source"],top["medium"],top["buyer_change"]),("google","organic",-99))
        self.assertEqual(result["sensitivity"]["previous"]["buyers_7d"],341)
    def test_missing_group_fails_reconciliation(self):
        with self.assertRaises(ValueError):
            summarize_breakdown("2020-12-21",self.rows[1:],self.comparison)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            summarize_breakdown("2020-12-21",self.rows+self.rows[:1],self.comparison)
    def test_missing_week_rate_preserved(self):
        result=summarize_breakdown("2020-12-21",self.rows,self.comparison)
        group=next(r for r in result["source"]["groups"] if r["current_new_users"]==0)
        self.assertIsNone(group["current_rate"])
        self.assertTrue(group["missing_week_rate_imputed_for_decomposition"])
    def test_zero_buyer_baseline_and_structure_only(self):
        comparison=summarize_rows("2020-12-21",[("2020-12-14",100,0),("2020-12-21",100,10)])
        rows=[("2020-12-14","A","direct","desktop",100,0,100,0),
              ("2020-12-21","B","direct","desktop",100,10,100,10)]
        r=summarize_breakdown("2020-12-21",rows,comparison)
        self.assertAlmostEqual(r["source"]["mix_change_pp"],10)
        self.assertAlmostEqual(r["source"]["within_change_pp"],0)
    def test_null_and_blank_source_are_distinct(self):
        comparison=summarize_rows("2020-12-21",[("2020-12-14",2,0),("2020-12-21",2,1)])
        rows=[("2020-12-14",None,"x","desktop",1,0,1,0),
              ("2020-12-14","","x","desktop",1,0,1,0),
              ("2020-12-21",None,"x","desktop",1,1,1,1),
              ("2020-12-21","","x","desktop",1,0,1,0)]
        self.assertEqual(len(summarize_breakdown("2020-12-21",rows,comparison)["source"]["groups"]),2)

if __name__=="__main__": unittest.main()
