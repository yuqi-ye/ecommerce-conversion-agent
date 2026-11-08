-- 在 BigQuery 的 SQL 编辑器运行（GoogleSQL），不在 MySQL 运行。
-- 目的：导出一天的首次访问和购买明细，供后续 MySQL 试导入。
-- 当前状态：用户已保存导出 CSV；2026-10-21 本地明细与核对 CSV 对账通过，未独立重跑云端查询。
-- 不使用 LIMIT，不去重、不排除缺失用户或缺失来源。
-- *_is_null 标记用于保留 CSV 中 NULL 与空字符串的区别。
SELECT
  _TABLE_SUFFIX AS source_table_date,
  event_date,
  event_name,
  user_pseudo_id,
  event_timestamp AS event_timestamp_us,
  user_first_touch_timestamp AS user_first_touch_timestamp_us,
  traffic_source.source AS traffic_source_source,
  traffic_source.medium AS traffic_source_medium,
  device.category AS device_category,
  user_pseudo_id IS NULL AS user_pseudo_id_is_null,
  traffic_source.source IS NULL AS traffic_source_source_is_null,
  traffic_source.medium IS NULL AS traffic_source_medium_is_null,
  device.category IS NULL AS device_category_is_null
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX = '20201201'
  AND event_name IN ('first_visit', 'purchase')
ORDER BY event_timestamp, event_name, user_pseudo_id;
