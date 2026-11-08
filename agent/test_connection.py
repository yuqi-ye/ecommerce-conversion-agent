import unittest
from unittest.mock import MagicMock, patch
import pymysql
from run_compare import run_query

class ConnectionTests(unittest.TestCase):
    @patch("run_compare.compare_weeks")
    @patch("run_compare.pymysql.connect")
    def test_readonly_setup_and_cleanup(self, connect, compare):
        conn=MagicMock();connect.return_value=conn;compare.return_value={"status":"ok"}
        self.assertEqual(run_query("test-only","2020-12-21"),{"status":"ok"})
        setup=conn.cursor.return_value.__enter__.return_value
        self.assertIn(unittest.mock.call("START TRANSACTION READ ONLY"),setup.execute.call_args_list)
        self.assertEqual(connect.call_args.kwargs["user"],"ecommerce_agent")
        self.assertEqual(connect.call_args.kwargs["local_infile"],False)
        conn.close.assert_called_once()
    @patch("run_compare.compare_weeks",side_effect=ValueError("missing rows"))
    @patch("run_compare.pymysql.connect")
    def test_close_after_query_failure(self,connect,compare):
        conn=MagicMock();connect.return_value=conn
        with self.assertRaises(ValueError):run_query("test-only","2020-12-21")
        conn.close.assert_called_once()

if __name__=="__main__":unittest.main()
