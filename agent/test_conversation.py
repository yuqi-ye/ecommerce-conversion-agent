import unittest
from unittest.mock import Mock
from run_agent import run_loop, redact
from test_agent import call

class ConversationTests(unittest.TestCase):
    def test_clarification_then_date_preserves_context(self):
        history = []
        query = Mock(return_value={'status':'ok','buyers':124})
        run_loop('为什么下降？',lambda _: ({'content':'请提供日期'},{}),query,lambda _:None,history)
        self.assertEqual([x['role'] for x in history], ['system','user','assistant'])
        def model(messages):
            if messages[-1]['role'] == 'user':
                self.assertEqual(messages[-1]['content'],'2020-12-21')
                self.assertEqual(messages[1]['content'],'为什么下降？')
                return call(), {}
            return {'content':'查询完成'}, {}
        run_loop('2020-12-21',model,query,lambda _:None,history)
        query.assert_called_once_with('2020-12-21',True)
        self.assertTrue(any(m['role']=='tool' and '124' in m['content'] for m in history))
        self.assertEqual(history[-1]['content'],'查询完成')

    def test_followup_can_reuse_evidence(self):
        history=[]
        model=Mock(side_effect=[(call(),{}),({'content':'124人'}, {})])
        query=Mock(return_value={'status':'ok','buyers':124})
        run_loop('分析2020-12-21',model,query,lambda _:None,history)
        def follow(messages):
            self.assertTrue(any(x['role']=='tool' for x in messages))
            return {'content':'沿用前一次查询的124人。'}, {}
        run_loop('解释一下',follow,query,lambda _:None,history)
        self.assertEqual(query.call_count,1)

    def test_failed_turn_does_not_commit_and_clear_removes_context(self):
        history=[]
        run_loop('你好',lambda _: ({'content':'请给日期'},{}),Mock(),lambda _:None,history)
        before=list(history)
        result=run_loop('分析',lambda _: (call(),{}),Mock(return_value={'status':'ok'}),lambda _:None,history)
        self.assertEqual(result['status'],'limit_reached')
        self.assertEqual(history,before)
        history.clear()
        def model(messages):
            self.assertEqual(len(messages),2)
            return {'content':'新对话'},{}
        run_loop('新问题',model,Mock(),lambda _:None,history)

    def test_http500_keeps_history_and_allows_manual_retry(self):
        import urllib.error
        history=[]
        run_loop('你好',lambda _: ({'content':'请给日期'},{}),Mock(),lambda _:None,history)
        before=list(history)
        failed=Mock(side_effect=urllib.error.HTTPError('https://api.deepseek.com',500,'secret',{},None))
        result=run_loop('2020-12-21',failed,Mock(),lambda _:None,history)
        self.assertEqual(result['http_status'],500)
        self.assertEqual(history,before)
        self.assertEqual(failed.call_count,1)
        self.assertNotIn('secret',str(result))
        result=run_loop('2020-12-21',lambda _: ({'content':'收到日期'},{}),Mock(),lambda _:None,history)
        self.assertEqual(result['status'],'completed')

    def test_network_failure_preserves_completed_tool_trace(self):
        import urllib.error
        model=Mock(side_effect=[(call(),{}),urllib.error.URLError('secret')])
        history=[]
        result=run_loop('分析2020-12-21',model,Mock(return_value={'status':'ok'}),lambda _:None,history)
        self.assertEqual(result['status'],'network_error')
        self.assertEqual(len(result['tool_trace']),1)
        self.assertEqual(history,[])
        self.assertNotIn('secret',str(result))

    def test_redact_special_characters(self):
        secret='a"b\\c'
        data={'answer':'密码'+secret,'nested':[secret,124]}
        self.assertEqual(redact(data,(secret,None)),{'answer':'密码[REDACTED]','nested':['[REDACTED]',124]})

if __name__=='__main__':
    unittest.main()
