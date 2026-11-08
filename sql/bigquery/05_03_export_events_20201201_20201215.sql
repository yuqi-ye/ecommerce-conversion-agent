-- 在 BigQuery 网页运行，不在 MySQL 运行。
-- 第 3/6 批；预期 55006 条数据记录。不加 LIMIT，不去重。
-- 保存为 data/raw/events_20201201_20201215.csv。当前仅已编写，未执行。
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
WHERE _TABLE_SUFFIX BETWEEN '20201201' AND '20201215'
  AND event_name IN ('first_visit', 'purchase')
ORDER BY event_timestamp, event_name, user_pseudo_id;
