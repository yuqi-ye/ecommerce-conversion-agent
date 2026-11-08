-- 在 DataGrip / MySQL 执行。只读检查，不修改原始数据。
-- 一次运行整个 WITH ... SELECT 语句，结果为两列。
-- 以下是问题筛查，异常标记不等于数据必然错误。
WITH first_visits AS (
    SELECT user_pseudo_id,
           COUNT(*) AS first_visit_rows,
           MIN(event_timestamp_us) AS first_visit_us
    FROM ecommerce_analysis.raw_events
    WHERE event_name = 'first_visit'
      AND user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) <> ''
    GROUP BY user_pseudo_id
), purchase_users AS (
    SELECT user_pseudo_id,
           MIN(event_timestamp_us) AS first_purchase_us
    FROM ecommerce_analysis.raw_events
    WHERE event_name = 'purchase'
      AND user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) <> ''
    GROUP BY user_pseudo_id
), metrics AS (
    SELECT 1 AS seq, '首次访问事件条数' AS metric,
           COUNT(*) AS value
    FROM ecommerce_analysis.raw_events WHERE event_name = 'first_visit'
    UNION ALL
    SELECT 2, '有首访标记的去重用户数', COUNT(*) FROM first_visits
    UNION ALL
    SELECT 3, '有多条首访记录的用户数', COUNT(*)
    FROM first_visits WHERE first_visit_rows > 1
    UNION ALL
    SELECT 4, '首访记录中缺失 first-touch 的条数', COUNT(*)
    FROM ecommerce_analysis.raw_events
    WHERE event_name = 'first_visit' AND user_first_touch_timestamp_us IS NULL
    UNION ALL
    SELECT 5, '首访记录与 first-touch 时间不相等的条数', COUNT(*)
    FROM ecommerce_analysis.raw_events
    WHERE event_name = 'first_visit'
      AND user_first_touch_timestamp_us IS NOT NULL
      AND event_timestamp_us <> user_first_touch_timestamp_us
    UNION ALL
    SELECT 6, '购买事件条数', COUNT(*)
    FROM ecommerce_analysis.raw_events WHERE event_name = 'purchase'
    UNION ALL
    SELECT 7, '有购买记录的去重用户数', COUNT(*) FROM purchase_users
    UNION ALL
    SELECT 8, '购买用户中匹配到首访标记的人数', COUNT(*)
    FROM purchase_users p JOIN first_visits f ON p.user_pseudo_id = f.user_pseudo_id
    UNION ALL
    SELECT 9, '购买用户中没有首访标记的人数', COUNT(*)
    FROM purchase_users p LEFT JOIN first_visits f ON p.user_pseudo_id = f.user_pseudo_id
    WHERE f.user_pseudo_id IS NULL
    UNION ALL
    SELECT 10, '最早购买时间早于最早首访时间的用户数', COUNT(*)
    FROM purchase_users p JOIN first_visits f ON p.user_pseudo_id = f.user_pseudo_id
    WHERE p.first_purchase_us < f.first_visit_us
)
SELECT metric, value FROM metrics ORDER BY seq;
