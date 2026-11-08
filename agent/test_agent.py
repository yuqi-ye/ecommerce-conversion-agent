import unittest
from unittest.mock import Mock
import pymysql
from run_agent import dispatch, run_loop


def call(args='{"week_start":"2020-12-21"}', name='diagnose_week'):
    return {'role':'assistant','content':None,'tool_calls':[{'id':'test1','type':'function',
        'function':{'name':name,'arguments':args}}]}


class AgentTests(unittest.TestCase):
    def test_reject_before_database(self):
        query = Mock()
        for name, args in [('sql', '{}'), ('compare_weeks','{}'),
                ('compare_weeks','{"week_start":"2021-01-25"}'),
                ('compare_weeks','{"week_start":"2020-12-21","sql":"DROP TABLE x"}')]:
            self.assertEqual(dispatch(name,args,query)['status'],'error')
        query.assert_not_called()

    def test_model_gets_real_tool_result(self):
        query = Mock(return_value={'status':'ok','buyers':124})
        def model(messages):
            if len(messages) == 2:
                return call(), {}
            self.assertIn('124', messages[-1]['content'])
            self.assertEqual(messages[-1]['role'], 'tool')
            return {'content':'根据查询，124人。'}, {}
        result = run_loop('分析2020-12-21',model,query,lambda _:None)
        query.assert_called_once_with('2020-12-21',True)
        self.assertEqual(result['status'],'completed')
        self.assertEqual(len(result['tool_trace']),1)

    def test_buyer_decomposition(self):
        from analysis_tools import summarize_rows
        result = summarize_rows('2020-12-21', [('2020-12-14',24173,338),('2020-12-21',16984,124)])
        output = dispatch('diagnose_week', '{"week_start":"2020-12-21"}', Mock(return_value=result))
        parts = output['buyer_decomposition']
        self.assertAlmostEqual(parts['volume_effect_buyers'], -100.520498, places=5)
        self.assertAlmostEqual(parts['rate_effect_buyers'], -113.479502, places=5)
        self.assertAlmostEqual(parts['volume_effect_buyers'] + parts['rate_effect_buyers'], -214)

    def test_error_not_exposed(self):
        query = Mock(side_effect=pymysql.OperationalError(1045,'secret password'))
        result = dispatch('compare_weeks','{"week_start":"2020-12-21"}',query)
        self.assertEqual(result['code'],1045)
        self.assertNotIn('secret',str(result))

    def test_loop_limit_and_cache(self):
        model = Mock(return_value=(call(), {}))
        query = Mock(return_value={'status':'ok'})
        result = run_loop('分析',model,query,lambda _:None)
        self.assertEqual(result['status'],'limit_reached')
        self.assertEqual(model.call_count,4)
        self.assertEqual(query.call_count,1)

    def test_clarification_needs_no_database(self):
        query = Mock()
        result = run_loop('分析一下',lambda _: ({'content':'请提供目标周。'},{}),query,lambda _:None)
        query.assert_not_called()
        self.assertEqual(result['tool_trace'],[])

if __name__ == '__main__':
    unittest.main()
