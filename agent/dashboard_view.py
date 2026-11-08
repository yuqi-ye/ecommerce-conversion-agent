"""展示组件：所有图形均使用工具返回的真实汇总值。"""
from html import escape
import altair as alt
import pandas as pd
import streamlit as st

PALETTE = ['#aba4ed','#c9d2bc','#f1d88a']


def line_hint(previous, current, percent=False):
    """Two explicitly labelled observations, with proportional bars."""
    peak=max(previous,current,0.000001)
    fmt=lambda v: f'{v:.4%}' if percent else f'{v:,}'
    rows=''.join(f'<div class="mini-row"><span>{label}</span><div class="mini-track"><i style="width:{v/peak*100:.2f}%"></i></div><b>{fmt(v)}</b></div>' for label,v in [('前周',previous),('本周',current)])
    st.markdown('<div class="mini-compare">'+rows+'</div>',unsafe_allow_html=True)


def chart_style(chart):
    return chart.configure_view(stroke=None).configure_axis(
        labelColor='#919789',titleColor='#8a907f',gridColor='#e9e9df',
        domain=False,ticks=False,labelFontSize=11,titleFontSize=11).configure(background='transparent')


def show_metrics(result):
    if not result:
        st.markdown('<div class="empty-state"><h2>还没有分析结果</h2>'
            '<p>在左侧填写 API 密钥和数据库密码，再输入想分析的日期和问题。<br>'
            '查询完成后，结果会显示在这里。</p></div>',unsafe_allow_html=True)
        return
    a,b = result['previous'],result['current']
    st.caption(f"{a['cohort_week']} → {b['cohort_week']}  · 首访周（UTC）")
    # Unequal bento cells: the outcome owns the largest panel.
    hero,secondary = st.columns([1.7,1],gap='large')
    with hero:
        with st.container(key='kpi_buyers'):
            st.markdown('<div class="card-eyebrow"><span class="custom-glyph">◒</span> 购买人数</div>',unsafe_allow_html=True)
            st.metric('7 日购买人数',f"{b['buyers_7d']:,}",f"{b['buyers_7d']-a['buyers_7d']:+,} 人",delta_color='off')
            line_hint(a['buyers_7d'],b['buyers_7d'])
            change=b['buyers_7d']-a['buyers_7d']
            relative=f"{change/a['buyers_7d']:+.1%}" if a['buyers_7d'] else '前周为零，不计算相对变化'
            st.markdown(f'<div class="hero-foot">较前周 {relative}<span>统计首次访问后 7 日内的购买</span></div>',unsafe_allow_html=True)
    with secondary:
        with st.container(key='kpi_visitors'):
            st.metric('新访客人数',f"{b['new_users']:,}",f"{b['new_users']-a['new_users']:+,} 人",delta_color='off')
            st.markdown(f'<div class="compact-baseline">前周 {a["new_users"]:,} 人</div>',unsafe_allow_html=True)
        with st.container(key='kpi_rate'):
            st.metric('7 日购买率',f"{b['conversion_rate']:.4%}",f"{(b['conversion_rate']-a['conversion_rate'])*100:+.4f} 个百分点",delta_color='off')
            st.markdown(f'<div class="compact-baseline">前周 {a["conversion_rate"]:.4%}</div>',unsafe_allow_html=True)
    st.markdown('<div class="chapter"><span>分组对比</span></div>',unsafe_allow_html=True)
    main,rail = st.columns([2.1,1],gap='large')
    with main:
        diag=result.get('diagnostics')
        if diag:
            groups=diag['source']['groups']
            # 选取两周购买人数较多的6组；不省略原始来源于工具明细。
            visible=sorted(groups,key=lambda g: g['previous_buyers']+g['current_buyers'],reverse=True)[:6]
            rows=[]
            short={'shop.googlemerchandisestore.com':'商店站点','(direct)':'Direct','<Other>':'Other','google':'Google'}
            for g in visible:
                raw=f"{g['source']} / {g['medium']}"
                label=f"{short.get(g['source'],str(g['source']))} / {g['medium']}"
                rows.append({'来源':raw,'显示来源':label,'前周':g['previous_buyers'],'本周':g['current_buyers'],'变化':g['buyer_change']})
            df=pd.DataFrame(rows)
            st.markdown('<div class="section-head"><h3>来源购买人数</h3><span>两周购买人数最多的 6 个来源</span></div>',unsafe_allow_html=True)
            plot=df.melt(id_vars=['来源','显示来源','变化'],value_vars=['前周','本周'],var_name='周别',value_name='购买人数')
            base=alt.Chart(plot).encode(
                x=alt.X('购买人数:Q',title='7 日购买人数',axis=alt.Axis(grid=True)),
                y=alt.Y('显示来源:N',sort=df['显示来源'].tolist(),title=None,axis=alt.Axis(labelLimit=155)),
                yOffset=alt.YOffset('周别:N',sort=['前周','本周']),
                color=alt.Color('周别:N',scale=alt.Scale(domain=['前周','本周'],range=['#c7cbbd','#575044']),legend=alt.Legend(orient='top',title=None)),
                tooltip=['来源:N','周别:N','购买人数:Q','变化:Q'])
            bars=base.mark_bar(cornerRadiusEnd=5,size=13)
            labels=base.mark_text(align='left',dx=5,fontSize=11,color='#51584b').encode(text='购买人数:Q',color=alt.value('#51584b'))
            st.altair_chart(chart_style((bars+labels).properties(height=340)),width='stretch')
            st.markdown('<div class="section-head"><h3>来源明细</h3><span>按购买人数变化排序</span></div>',unsafe_allow_html=True)
            full=pd.DataFrame([{'来源':f"{g['source']} / {g['medium']}",'前周':g['previous_buyers'],'本周':g['current_buyers'],'变化':g['buyer_change']} for g in sorted(groups,key=lambda g:g['buyer_change'])])
            st.dataframe(full,hide_index=True,width='stretch',height=245)
        else:
            st.markdown('<div class="section-head"><h3>两周对比</h3></div>',unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{'首访周':x['cohort_week'],'新访客人数':x['new_users'],'购买人数':x['buyers_7d']} for x in (a,b)]),hide_index=True,width='stretch')
        parts=result.get('buyer_decomposition')
        if parts:
            st.markdown(f'<div class="summary-line">人数效应 <b>{parts["volume_effect_buyers"]:+.2f}</b> 人 &nbsp; / &nbsp;'
                f'购买率效应 <b>{parts["rate_effect_buyers"]:+.2f}</b> 人<br>'
                '按先人数、后购买率的顺序计算；换序会改变各项贡献，不能据此确定业务原因。</div>',unsafe_allow_html=True)
    with rail:
        with st.container(key='right_rail'):
            st.markdown('<div class="rail-heading">购买用户的设备分布</div><div class="rail-subtitle">本周新访客中，7 日内购买的用户</div>',unsafe_allow_html=True)
            if diag and b['buyers_7d']>0:
                device=diag['device']['groups']
                order={'desktop':0,'mobile':1,'tablet':2}
                device=sorted(device,key=lambda g:order.get(g['device'],3))
                d=pd.DataFrame([{'设备':g['device'] or '未知','购买人数':g['current_buyers']} for g in device])
                arc=alt.Chart(d).mark_arc(innerRadius=65,outerRadius=88,cornerRadius=5,padAngle=.025).encode(
                    theta=alt.Theta('购买人数:Q',stack=True),color=alt.Color('设备:N',scale=alt.Scale(domain=d['设备'].tolist(),range=PALETTE),legend=None),
                    tooltip=['设备:N','购买人数:Q'])
                text=alt.Chart(pd.DataFrame([{'value':str(b['buyers_7d'])}])).mark_text(fontSize=28,color='#33392c',fontWeight=600,dy=-2).encode(text='value:N')
                small=alt.Chart(pd.DataFrame([{'value':'购买用户'}])).mark_text(fontSize=11,color='#929886',dy=23).encode(text='value:N')
                st.altair_chart((arc+text+small).properties(height=205).configure_view(stroke=None).configure(background='transparent'),width='stretch')
                for i,g in enumerate(device):
                    label={'desktop':'桌面端','mobile':'移动端','tablet':'平板'}.get(g['device'],str(g['device']))
                    share=g['current_buyers']/b['buyers_7d']*100
                    st.markdown(f'<div class="device-row"><span class="dot" style="background:{PALETTE[i%3]}"></span>{escape(label)}<strong>{share:.1f}%</strong></div>',unsafe_allow_html=True)
            else:
                st.caption('本次查询未包含设备分布。')
            st.markdown('<div class="section-head"><h3>购买人数减少最多的来源</h3></div>',unsafe_allow_html=True)
            if diag:
                drops=sorted((g for g in diag['source']['groups'] if g['buyer_change']<0),key=lambda g:g['buyer_change'])[:3]
                for i,g in enumerate(drops,1):
                    name=escape(f"{g['source']} / {g['medium']}")
                    st.markdown(f'<div class="rank-card"><div class="rank-avatar">0{i}</div><div class="rank-text"><b title="{name}">{name}</b>'
                        f'<small>{g["previous_buyers"]} → {g["current_buyers"]} 位购买用户</small></div>'
                        f'<span class="rank-delta">{g["buyer_change"]}</span></div>',unsafe_allow_html=True)
                if not drops:
                    st.caption('本次没有购买人数减少的来源。')
                st.markdown(f'<div class="rail-note">来源结构净贡献<br><b>{diag["source"]["mix_change_pp"]:+.6f} 个百分点</b><br>'
                    f'来源内购买率贡献<br><b>{diag["source"]["within_change_pp"]:+.6f} 个百分点</b><br><br>'
                    '各来源的占比变化可能相互抵消。来源与设备的贡献不能相加。</div>',unsafe_allow_html=True)
