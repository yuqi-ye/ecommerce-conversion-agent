import json
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
APP=str(ROOT/'agent/web_app.py')

class WebTests(unittest.TestCase):
    def test_demo_cases(self):
        app=AppTest.from_file(APP,default_timeout=60).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'124')
        app.selectbox[0].select('12 月 28 日 · 购买人数下降 58 人').run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'66')

    def test_missing_key_blocks_network(self):
        app=AppTest.from_file(APP,default_timeout=60).run()
        app.radio[0].set_value('实时分析').run()
        with patch('run_agent.chat') as model:
            app.chat_input[0].set_value('分析2020-12-21').run()
            model.assert_not_called()
        self.assertTrue(app.error)
        self.assertEqual(len(app.exception),0)

    def test_live_query_followup_and_reset(self):
        app=AppTest.from_file(APP,default_timeout=60).run()
        app.radio[0].set_value('实时分析').run()
        app.text_input(key='api_key').set_value('test-key').run()
        app.text_input(key='db_password').set_value('test-password').run()
        record=json.loads((ROOT/'data/agent_runs/agent_20261107T081311186649Z.json').read_text())
        evidence=record['tool_trace'][0]['result']
        tool={'content':None,'tool_calls':[{'id':'t1','type':'function','function':{
            'name':'diagnose_week','arguments':'{"week_start":"2020-12-21"}'}}]}
        with patch('run_agent.chat',side_effect=[(tool,{}),({'content':'购买人数减少214人'}, {})]), \
             patch('run_compare.run_query',return_value=evidence) as query, \
             patch('pathlib.Path.write_text'):
            app.chat_input[0].set_value('分析2020-12-21').run()
            query.assert_called_once()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'124')
        def follow(key,messages):
            self.assertTrue(any(x['role']=='tool' for x in messages))
            return {'content':'沿用结果，google/organic减少99人。'},{}
        with patch('run_agent.chat',side_effect=follow),patch('run_compare.run_query') as query,patch('pathlib.Path.write_text'):
            app.chat_input[0].set_value('哪个来源最多？').run()
            query.assert_not_called()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.session_state['turns']),2)
        next(b for b in app.button if b.label=='清空密钥和对话').click().run()
        self.assertEqual(app.session_state['history'],[])
        self.assertEqual(app.text_input(key='api_key').value,'')

if __name__=='__main__':
    unittest.main()
