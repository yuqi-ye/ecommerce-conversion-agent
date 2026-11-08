-- 在 DataGrip/MySQL 执行整个 CREATE VIEW 语句；不修改或删除 raw_events。
-- 若视图已存在，请停止并反馈，不要重复创建。
-- 首访唯一最早时刻已经通过 CSV 检查。
CREATE VIEW ecommerce_analysis.v_new_user_cohort AS
WITH ranked AS (
 SELECT user_pseudo_id, event_timestamp_us AS first_visit_us,
        user_first_touch_timestamp_us AS first_touch_us,
        traffic_source_source, traffic_source_medium, device_category,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id
          ORDER BY event_timestamp_us, source_batch, source_row_no) AS rn
 FROM ecommerce_analysis.raw_events
 WHERE event_name = 'first_visit'
   AND user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) <> ''
), purchases AS (
 SELECT user_pseudo_id, MIN(event_timestamp_us) AS first_purchase_us
 FROM ecommerce_analysis.raw_events
 WHERE event_name = 'purchase'
   AND user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) <> ''
 GROUP BY user_pseudo_id
), base AS (
 SELECT f.user_pseudo_id, f.first_visit_us, f.first_touch_us,
        f.traffic_source_source, f.traffic_source_medium, f.device_category,
        p.first_purchase_us,
        (f.first_visit_us = f.first_touch_us) AS first_touch_exact,
        COALESCE(p.first_purchase_us < f.first_visit_us, 0) AS purchase_before_first_visit,
        (f.first_visit_us + 604800000000 <= 1612137600000000) AS has_full_7d_window,
        (f.first_visit_us >= 1604275200000000 AND f.first_visit_us < 1611532800000000) AS in_complete_cohort_week
 FROM ranked f LEFT JOIN purchases p ON f.user_pseudo_id = p.user_pseudo_id
 WHERE f.rn = 1
)
SELECT *,
 CASE WHEN purchase_before_first_visit = 1 OR has_full_7d_window = 0 THEN NULL
      WHEN first_purchase_us >= first_visit_us
       AND first_purchase_us < first_visit_us + 604800000000 THEN 1
      ELSE 0 END AS purchased_7d,
 (COALESCE(first_touch_exact, 0) = 1 AND purchase_before_first_visit = 0
  AND has_full_7d_window = 1 AND in_complete_cohort_week = 1) AS main_analysis_eligible
FROM base;
