-- 在浏览器 BigQuery 中运行，不在 DataGrip/MySQL 运行。
-- 正式取数前按日期、事件生成数量基准；用于决定分批范围和后续对账。
-- 已编写，尚未运行。
SELECT
  _TABLE_SUFFIX AS source_table_date,
  event_name,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_pseudo_id) AS distinct_nonnull_users,
  COUNTIF(user_pseudo_id IS NULL) AS null_user_id_rows,
  COUNTIF(user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) = '') AS blank_user_id_rows,
  MIN(event_timestamp) AS min_event_timestamp_us,
  MAX(event_timestamp) AS max_event_timestamp_us
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  AND event_name IN ('first_visit', 'purchase')
GROUP BY source_table_date, event_name
ORDER BY source_table_date, event_name;
