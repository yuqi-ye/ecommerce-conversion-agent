"""来源、设备和时间筛选敏感性工具；所有结果由数据库计数和程序计算。"""
from collections import defaultdict
from analysis_tools import build_comparison_query, validate_week

BREAKDOWN_SQL = """
SELECT
 CASE WHEN first_visit_us < %s THEN %s ELSE %s END AS cohort_week,
 traffic_source_source, traffic_source_medium, device_category,
 SUM(main_analysis_eligible) AS main_new_users,
 SUM(CASE WHEN main_analysis_eligible = 1 THEN purchased_7d ELSE 0 END) AS main_buyers_7d,
 COUNT(*) AS relaxed_new_users,
 SUM(purchased_7d) AS relaxed_buyers_7d
FROM ecommerce_analysis.v_new_user_cohort
WHERE in_complete_cohort_week = 1 AND has_full_7d_window = 1
 AND purchase_before_first_visit = 0
 AND first_visit_us >= %s AND first_visit_us < %s
GROUP BY cohort_week, traffic_source_source, traffic_source_medium, device_category
ORDER BY cohort_week, traffic_source_source, traffic_source_medium, device_category
"""

def _integer(value):
    if value is None:
        raise ValueError("分组计数缺失，不能按0处理。")
    n = int(value)
    if n != value or n < 0:
        raise ValueError("分组人数必须为非负整数。")
    return n

def summarize_breakdown(week_start, rows, comparison):
    previous, current = validate_week(week_start)
    weeks = [previous.isoformat(), current.isoformat()]
    groups = {}
    totals = [[0, 0, 0, 0], [0, 0, 0, 0]]
    for row in rows:
        if len(row) != 8:
            raise ValueError("来源设备查询列数不符。")
        week, source, medium, device, *raw_counts = row
        key = (str(week), source, medium, device)
        if key[0] not in weeks or key in groups:
            raise ValueError("分组重复或出现预期之外的首访周。")
        counts = [_integer(v) for v in raw_counts]
        n, b, relaxed_n, relaxed_b = counts
        if not (b <= n <= relaxed_n and b <= relaxed_b <= relaxed_n
                and relaxed_b-b <= relaxed_n-n):
            raise ValueError("分组人数与购买人数不一致。")
        groups[key] = counts
        i = weeks.index(key[0])
        totals[i] = [a+b for a,b in zip(totals[i], counts)]
    for i, label in enumerate(("previous", "current")):
        baseline = comparison[label]
        if baseline["cohort_week"] != weeks[i] or totals[i][:2] != [baseline["new_users"], baseline["buyers_7d"]]:
            raise ValueError("分组加总与周度查询不一致，停止生成诊断。")
        if totals[i][0] == 0:
            raise ValueError("某周没有主分析用户，无法分解购买率。")

    def decompose(indices, names):
        aggregated = defaultdict(lambda: [[0,0],[0,0]])
        for key, counts in groups.items():
            label = tuple(key[j] for j in indices)
            i = weeks.index(key[0])
            aggregated[label][i][0] += counts[0]
            aggregated[label][i][1] += counts[1]
        result = []
        for label, ((n0,b0),(n1,b1)) in aggregated.items():
            if n0+n1 == 0:
                continue
            observed0 = b0/n0 if n0 else None
            observed1 = b1/n1 if n1 else None
            r0 = observed0 if observed0 is not None else observed1
            r1 = observed1 if observed1 is not None else observed0
            s0, s1 = n0/totals[0][0], n1/totals[1][0]
            result.append({
                **dict(zip(names,label)),
                "previous_new_users": n0, "current_new_users": n1,
                "previous_buyers": b0, "current_buyers": b1,
                "previous_rate": observed0, "current_rate": observed1,
                "previous_share": s0, "current_share": s1,
                "buyer_change": b1-b0,
                "mix_change_pp": (s1-s0)*(r0+r1)/2*100,
                "within_change_pp": (r1-r0)*(s0+s1)/2*100,
                "missing_week_rate_imputed_for_decomposition": n0 == 0 or n1 == 0,
            })
        result.sort(key=lambda r:(r["buyer_change"],str([r[n] for n in names])))
        mix = sum(r["mix_change_pp"] for r in result)
        within = sum(r["within_change_pp"] for r in result)
        actual = (totals[1][1]/totals[1][0]-totals[0][1]/totals[0][0])*100
        if abs(mix+within-actual) > 1e-9:
            raise ValueError("结构与组内贡献未加回整体率差。")
        return {"mix_change_pp":mix,"within_change_pp":within,"groups":result}

    relaxed = []
    for i, week in enumerate(weeks):
        n,b = totals[i][2:]
        relaxed.append({"cohort_week":week,"new_users":n,"buyers_7d":b,"conversion_rate":b/n})
    return {
        "status":"ok",
        "group_count":len(groups),
        "reconciliation":"分组人数加总与周度查询一致；两项贡献加总与整体率差一致。",
        "source":decompose((1,2),("source","medium")),
        "device":decompose((3,),("device",)),
        "source_device":decompose((1,2,3),("source","medium","device")),
        "sensitivity":{
            "previous":relaxed[0],"current":relaxed[1],
            "conversion_change_pp":(relaxed[1]["conversion_rate"]-relaxed[0]["conversion_rate"])*100,
            "rule":"仅放宽first-touch时间一致性，其他人群资格不变。",
        },
        "limitations":[
            "对称分解是描述性算术，未证明原因或统计显著性。",
            "来源为首次获客source+medium，设备取首访记录。",
            "单周无用户时使用另一周率参与分解并将变化归结构项；展示的无样本周率仍为null。",
            "来源、设备和交叉分解是不同视角，贡献不可跨视角相加。",
        ],
    }

def get_source_device_breakdown(connection, week_start, comparison):
    _, params = build_comparison_query(week_start)
    cursor = connection.cursor()
    try:
        cursor.execute(BREAKDOWN_SQL, params)
        rows = cursor.fetchall()
    finally:
        cursor.close()
    return summarize_breakdown(week_start, rows, comparison)
