-- 修正：除法前转换 DECIMAL，避免整数计数相除提前舍入。
-- 在 DataGrip/MySQL 执行全文。仅使用主分析合格用户。
-- UTC 日期通过 epoch + 秒计算，避免 FROM_UNIXTIME 受连接时区影响。
-- 每行是一个首访周；购买人数是在这些用户各自首访后168小时内购买的人数。
WITH dated AS (
 SELECT DATE(TIMESTAMPADD(SECOND, first_visit_us DIV 1000000,
                         CAST('1970-01-01 00:00:00' AS DATETIME))) AS first_visit_date_utc,
        purchased_7d
 FROM ecommerce_analysis.v_new_user_cohort
 WHERE main_analysis_eligible = 1
), weekly AS (
 SELECT DATE_SUB(first_visit_date_utc, INTERVAL WEEKDAY(first_visit_date_utc) DAY) AS cohort_week,
        COUNT(*) AS new_users,
        SUM(purchased_7d) AS buyers_7d
 FROM dated
 GROUP BY cohort_week
), compared AS (
 SELECT *, CAST(buyers_7d AS DECIMAL(30, 12)) / NULLIF(new_users, 0) AS conversion_rate,
        LAG(new_users) OVER (ORDER BY cohort_week) AS prev_new_users,
        LAG(buyers_7d) OVER (ORDER BY cohort_week) AS prev_buyers,
        LAG(CAST(buyers_7d AS DECIMAL(30, 12)) / NULLIF(new_users, 0)) OVER (ORDER BY cohort_week) AS prev_rate
 FROM weekly
)
SELECT cohort_week, new_users, buyers_7d,
       ROUND(conversion_rate * 100, 4) AS conversion_rate_pct,
       ROUND((CAST(new_users AS DECIMAL(30, 12)) / NULLIF(prev_new_users, 0) - 1) * 100, 2) AS new_users_wow_pct,
       ROUND((CAST(buyers_7d AS DECIMAL(30, 12)) / NULLIF(prev_buyers, 0) - 1) * 100, 2) AS buyers_wow_pct,
       ROUND((conversion_rate - prev_rate) * 100, 4) AS conversion_change_pp
FROM compared
ORDER BY cohort_week;
