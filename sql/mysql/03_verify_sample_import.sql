-- 导入后核对。预期共 3410 行；first_visit 3303 行/3303 用户，purchase 107 行/98 用户。
SELECT COUNT(*) AS total_rows FROM ecommerce_analysis.sample_events_20201201;
SELECT source_table_date, event_name,
       COUNT(*) AS event_count,
       COUNT(DISTINCT user_pseudo_id) AS distinct_nonnull_users,
       SUM(user_pseudo_id IS NULL) AS null_user_id_rows,
       SUM(user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) = '') AS blank_user_id_rows,
       MIN(event_timestamp_us) AS min_event_timestamp_us,
       MAX(event_timestamp_us) AS max_event_timestamp_us
FROM ecommerce_analysis.sample_events_20201201
GROUP BY source_table_date, event_name
ORDER BY source_table_date, event_name;
