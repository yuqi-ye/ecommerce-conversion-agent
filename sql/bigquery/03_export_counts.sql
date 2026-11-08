-- 在 BigQuery 运行（GoogleSQL）。
-- 与 02_export_events.sql 使用完全相同的源表、日期和事件筛选。
-- 当前状态：用户已保存导出 CSV；2026-10-21 本地明细与核对 CSV 对账通过，未独立重跑云端查询。
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
WHERE _TABLE_SUFFIX = '20201201'
  AND event_name IN ('first_visit', 'purchase')
GROUP BY source_table_date, event_name
ORDER BY source_table_date, event_name;
