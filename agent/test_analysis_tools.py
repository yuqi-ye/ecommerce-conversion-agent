import unittest
from analysis_tools import build_comparison_query, summarize_rows, compare_weeks

class Tests(unittest.TestCase):
    def test_known_case(self):
        r=summarize_rows("2020-12-21",[("2020-12-14",24173,338),("2020-12-21",16984,124)])
        self.assertEqual(r["change"]["buyers_7d"],-214)
        self.assertAlmostEqual(r["change"]["conversion_percentage_points"],-0.6681553339827708)
    def test_invalid_dates_and_injection(self):
        for value in ["2020-12-20","2021-01-25","2020-11-02","2020-12-21'; DROP TABLE x; --","not-date"]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                build_comparison_query(value)
    def test_missing_duplicate_and_invalid_counts(self):
        cases=[[("2020-12-14",10,1)],
               [("2020-12-14",10,1),("2020-12-14",10,1)],
               [("2020-12-14",10,11),("2020-12-21",10,1)]]
        for rows in cases:
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                summarize_rows("2020-12-21",rows)
    def test_zero_baseline_buyers(self):
        r=summarize_rows("2020-12-21",[("2020-12-14",10,0),("2020-12-21",10,1)])
        self.assertIsNone(r["change"]["buyers_relative"])
    def test_bound_parameters_and_cursor_cleanup(self):
        class Cursor:
            closed=False
            def execute(self,sql,params):
                self.sql,self.params=sql,params
            def fetchall(self):
                return [("2020-12-14",24173,338),("2020-12-21",16984,124)]
            def close(self): self.closed=True
        class Connection:
            c=Cursor()
            def cursor(self):return self.c
        connection=Connection()
        compare_weeks(connection,"2020-12-21")
        self.assertTrue(connection.c.closed)
        self.assertEqual(connection.c.sql.count("%s"),5)
        self.assertNotIn("2020-12-21",connection.c.sql)
        self.assertEqual(connection.c.params[2],"2020-12-21")

if __name__=="__main__":unittest.main()
