"""Agent 的只读分析工具基础；连接对象由调用方注入，当前尚未接入模型。"""
from datetime import date, datetime, timedelta, timezone
import re

MIN_WEEK = date(2020, 11, 2)
MAX_WEEK = date(2021, 1, 18)
MICROS_PER_WEEK = 604800000000

COMPARE_SQL = """
SELECT
    CASE WHEN first_visit_us < %s THEN %s ELSE %s END AS cohort_week,
    COUNT(*) AS new_users,
    SUM(purchased_7d) AS buyers_7d
FROM ecommerce_analysis.v_new_user_cohort
WHERE main_analysis_eligible = 1
  AND first_visit_us >= %s AND first_visit_us < %s
GROUP BY cohort_week
ORDER BY cohort_week
"""

def validate_week(week_start):
    if not isinstance(week_start, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", week_start):
        raise ValueError("请使用 YYYY-MM-DD 格式的周一日期。")
    target = date.fromisoformat(week_start)
    if target.weekday() != 0:
        raise ValueError("目标首访周必须用周一日期表示。")
    previous = target - timedelta(days=7)
    if previous < MIN_WEEK or target > MAX_WEEK:
        raise ValueError("前后两周都必须具有完整观察期；当前可比较的目标周为2020-11-09至2021-01-18。")
    return previous, target

def epoch_us(day):
    return int(datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc).timestamp()) * 1000000

def build_comparison_query(week_start):
    previous, target = validate_week(week_start)
    # 所有参数通过驱动绑定，不拼接用户输入进 SQL。
    params = (epoch_us(target), previous.isoformat(), target.isoformat(),
              epoch_us(previous), epoch_us(target + timedelta(days=7)))
    return COMPARE_SQL, params

def summarize_rows(week_start, rows):
    previous, target = validate_week(week_start)
    expected = [previous.isoformat(), target.isoformat()]
    records = {}
    for week, new_users, buyers in rows:
        week = str(week)
        if week in records or week not in expected:
            raise ValueError("数据库返回重复或意外的首访周。")
        if new_users is None or buyers is None:
            raise ValueError("指标缺失，不能当作0处理。")
        n, b = int(new_users), int(buyers)
        if n != new_users or b != buyers or n <= 0 or not 0 <= b <= n:
            raise ValueError("人数口径异常，无法计算。")
        records[week] = dict(cohort_week=week, new_users=n, buyers_7d=b, conversion_rate=b/n)
    if set(records) != set(expected):
        raise ValueError("缺少某周数据，不能将未返回的数据当作0。")
    a, b = [records[w] for w in expected]
    return {
        "status": "ok",
        "metric_definition": "主分析合格新访客；UTC首访周；首访后[0,168小时)购买；first-touch严格一致",
        "source": "ecommerce_analysis.v_new_user_cohort",
        "previous": a,
        "current": b,
        "change": {
            "new_users": b["new_users"]-a["new_users"],
            "new_users_relative": b["new_users"]/a["new_users"]-1,
            "buyers_7d": b["buyers_7d"]-a["buyers_7d"],
            "buyers_relative": None if a["buyers_7d"] == 0 else b["buyers_7d"]/a["buyers_7d"]-1,
            "conversion_percentage_points": (b["conversion_rate"]-a["conversion_rate"])*100,
        },
        "limitations": ["描述性周度比较，尚不能确定原因。", "公开混淆样本，未提供ROI或漏斗诊断。"],
    }

def compare_weeks(connection, week_start):
    """使用支持 %s 参数绑定的 MySQL DB-API 连接和默认元组游标；只执行 SELECT。
    调用方必须配置数据库只读权限；函数不管理连接密码、创建账户或修改全局设置。
    """
    sql, params = build_comparison_query(week_start)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        cursor.close()
    return summarize_rows(week_start, rows)
