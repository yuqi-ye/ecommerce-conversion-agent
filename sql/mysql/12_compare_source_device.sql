-- MySQL只读；关注首访周 2020-12-14 和 2020-12-21。
-- 同时输出主分析与放宽 first-touch 一致性条件的对照，其他资格一致。
-- 来源保留原始 source / medium；设备取首访记录。NULL 与空串保留，不擅自归并。
WITH dated AS (
 SELECT *, DATE(TIMESTAMPADD(SECOND, first_visit_us DIV 1000000,
                            CAST('1970-01-01 00:00:00' AS DATETIME))) AS first_date
 FROM ecommerce_analysis.v_new_user_cohort
 WHERE in_complete_cohort_week = 1 AND has_full_7d_window = 1
   AND purchase_before_first_visit = 0
), selected AS (
 SELECT *, DATE_SUB(first_date, INTERVAL WEEKDAY(first_date) DAY) AS cohort_week
 FROM dated WHERE first_date >= '2020-12-14' AND first_date < '2020-12-28'
)
SELECT cohort_week, traffic_source_source, traffic_source_medium, device_category,
       SUM(main_analysis_eligible) AS main_new_users,
       SUM(CASE WHEN main_analysis_eligible = 1 THEN purchased_7d ELSE 0 END) AS main_buyers_7d,
       COUNT(*) AS relaxed_new_users,
       SUM(purchased_7d) AS relaxed_buyers_7d
FROM selected
GROUP BY cohort_week, traffic_source_source, traffic_source_medium, device_category
ORDER BY cohort_week, traffic_source_source, traffic_source_medium, device_category;
