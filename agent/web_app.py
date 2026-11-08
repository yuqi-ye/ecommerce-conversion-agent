"""仅本机运行的 Streamlit 展示页，复用已验证的 Agent 与 MySQL 工具。"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from run_agent import run_loop, chat, redact
from run_compare import run_query

ROOT = HERE.parent
RECORDS = ROOT / 'data' / 'agent_runs'
DEMOS = {
    '12 月 21 日 · 购买人数下降 214 人': 'agent_20261107T081311186649Z.json',
    '12 月 28 日 · 购买人数下降 58 人': 'agent_20261107T065842889887Z.json',
}


def reset_conversation():
    st.session_state.history = []
    st.session_state.turns = []
    st.session_state.session_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def forget():
    reset_conversation()
    st.session_state.api_key = ''
    st.session_state.db_password = ''


def latest_evidence(turns):
    for turn in reversed(turns):
        for trace in reversed(turn.get('tool_trace', [])):
            result = trace.get('result', {})
            if result.get('status') == 'ok' and 'previous' in result and 'current' in result:
                return result
    return None


import importlib
import dashboard_view
# Refresh the presentation module when this page reruns during local development.
show_metrics = importlib.reload(dashboard_view).show_metrics


st.set_page_config(page_title='新访客转化诊断台', page_icon='📊', layout='wide')
st.markdown('<style>' + (HERE / 'dashboard.css').read_text() + '</style>', unsafe_allow_html=True)
if 'history' not in st.session_state:
    reset_conversation()

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">◈</span> Cohort Lab</div>'
        ''
        '<div class="workspace"><div class="workspace-icon">◷</div>'
        '<p>新访客转化诊断台</p></div>', unsafe_allow_html=True)
    mode = st.radio('工作模式', ['历史演示', '实时分析'], key='mode')
    st.divider()
    if mode == '实时分析':
        st.text_input('DeepSeek API Key', type='password', key='api_key')
        st.text_input('MySQL · ecommerce_agent 密码', type='password', key='db_password')
        st.caption('密钥和密码仅在本次页面会话中使用，不写入记录。分析问题、聊天记录和汇总数据会发送至 DeepSeek，并产生 API 费用。')
        st.button('新对话', on_click=reset_conversation, width='stretch')
        st.button('清空密钥和对话', on_click=forget, width='stretch')
        st.caption(f"已提问 {len(st.session_state.turns)} / 8 个问题")
    else:
        demo = st.selectbox('选择历史分析', list(DEMOS))
        st.caption('查看已保存的分析，无需填写密钥，也不会产生费用。')
    st.divider()
    st.markdown('**指标口径**')
    st.caption('首访后 [0,168 小时) 购买；UTC 首访周；首次获客来源。有效目标为 2020-11-09 至 2021-01-18 之间的周一。')
    st.caption('公开混淆样本 · 描述性分析 · 不支持 ROI、因果判断或完整漏斗诊断')

st.markdown('<div class="topbar"><div><h1>新访客转化分析</h1>'
    '</div>'
    f'<span class="status-pill">● &nbsp; {mode}</span></div>', unsafe_allow_html=True)

if mode == '历史演示':
    st.markdown('<div class="notice">当前展示已保存的分析结果。</div>', unsafe_allow_html=True)
    try:
        record = json.loads((RECORDS / DEMOS[demo]).read_text())
    except (OSError, ValueError):
        st.error('历史记录无法读取，请检查项目 data/agent_runs 目录。')
        st.stop()
    show_metrics(latest_evidence([record]))
    report_tab, evidence_tab = st.tabs(['历史分析报告', '查询记录'])
    with report_tab:
        st.caption('以下为当时生成的报告。指标已核对，原因解释仍需进一步验证。')
        st.markdown(record['answer'])
    with evidence_tab:
        st.caption(DEMOS[demo])
        st.json(record['tool_trace'], expanded=False)
    st.stop()

show_metrics(latest_evidence(st.session_state.turns))
st.markdown('### 分析对话')
st.caption('例如：2020-12-21 这一周的新访客，7 日内购买人数为什么减少了？')
for turn in st.session_state.turns:
    with st.chat_message('user'):
        st.write(turn['question'])
    with st.chat_message('assistant'):
        if turn['status'] == 'completed':
            st.markdown(turn['answer'])
        else:
            st.error(turn['answer'])
            st.caption('这次请求未完成，也未加入聊天记录。请检查密钥或稍后重试。')
        with st.expander('查看查询记录与用量'):
            st.json({'工具': turn['tool_trace'], '用量': turn['usage']}, expanded=False)
            st.caption('没有查询记录时，表示本次未查询数据库，可能是在补充问题或使用之前的结果。')
        st.download_button('下载本轮记录', json.dumps(turn, ensure_ascii=False, indent=2),
            file_name=f"agent_turn_{turn['turn_number']}.json", mime='application/json',
            key=f"download_{turn['turn_number']}")

prompt = st.chat_input('输入问题、补充日期，或继续追问', max_chars=2000,
    disabled=len(st.session_state.turns) >= 8)
if prompt:
    key = st.session_state.get('api_key','').strip()
    password = st.session_state.get('db_password','')
    if not key or not key.isascii() or any(c.isspace() for c in key):
        st.error('请先在左侧填写完整的 DeepSeek API Key。')
    elif key in prompt or (password and password in prompt):
        st.error('问题中包含凭据，请删除后再提交。')
    elif len(json.dumps(st.session_state.history, ensure_ascii=False)) > 160000:
        st.warning('本段上下文较长，请点击“新对话”。')
    else:
        def query(week, details):
            if not password:
                raise ValueError('缺少数据库密码')
            return run_query(password, week, details=details)
        # 查询需要数据库密码；预先提示，避免把配置问题混作数据错误。
        if not password:
            st.warning('请在左侧填写 MySQL 密码后重新提交，实时查询需要它。')
        else:
            with st.status('正在分析，请稍候……', expanded=True) as progress:
                try:
                    result = run_loop(prompt, lambda messages: chat(key,messages), query,
                        progress=st.write, history=st.session_state.history)
                except (ValueError, KeyError, TypeError, IndexError, OSError):
                    result = {'status':'error', 'question':prompt,
                        'answer':'处理未完成：返回格式或本机执行异常，请反馈此提示，不要发送凭据。',
                        'tool_trace':[], 'usage':[]}
                progress.update(label='处理结束', state='complete' if result['status']=='completed' else 'error')
            result.update(model='deepseek-flash', session_id=st.session_state.session_id,
                turn_number=len(st.session_state.turns)+1,
                executed_at_utc=datetime.now(timezone.utc).isoformat(),
                history_message_count=len(st.session_state.history), interface='streamlit')
            safe = redact(result,(key,password))
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            try:
                RECORDS.mkdir(parents=True,exist_ok=True)
                (RECORDS/f'web_{stamp}.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2))
            except OSError:
                safe['answer'] += '\n\n本轮记录保存失败，可用下载按钮保留结果。'
            st.session_state.turns.append(safe)
            st.rerun()

