-- MySQL 只读。先为每个用户选最早首访，再按时间差分组。
-- 1 秒、1 天只是诊断区间，不是已经确定的排除阈值。
WITH ranked AS (
 SELECT user_pseudo_id, event_timestamp_us, user_first_touch_timestamp_us,
        ROW_NUMBER() OVER (
          PARTITION BY user_pseudo_id
          ORDER BY event_timestamp_us, source_batch, source_row_no
        ) AS rn
 FROM ecommerce_analysis.raw_events
 WHERE event_name = 'first_visit'
   AND user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) <> ''
), classified AS (
 SELECT CASE
   WHEN user_first_touch_timestamp_us IS NULL THEN 0
   WHEN event_timestamp_us = user_first_touch_timestamp_us THEN 1
   WHEN event_timestamp_us < user_first_touch_timestamp_us THEN 2
   WHEN event_timestamp_us - user_first_touch_timestamp_us <= 1000000 THEN 3
   WHEN event_timestamp_us - user_first_touch_timestamp_us <= 86400000000 THEN 4
   ELSE 5 END AS category
 FROM ranked WHERE rn = 1
)
SELECT CASE category
 WHEN 0 THEN 'first-touch 缺失'
 WHEN 1 THEN '两个时间完全相等'
 WHEN 2 THEN '首访早于 first-touch'
 WHEN 3 THEN '首访晚于 first-touch：不超过 1 秒'
 WHEN 4 THEN '首访晚于 first-touch：超过 1 秒至 1 天'
 WHEN 5 THEN '首访晚于 first-touch：超过 1 天'
 END AS time_difference_group,
 COUNT(*) AS users
FROM classified GROUP BY category ORDER BY category;
