-- 在 MySQL 执行。第一项应为 263154，分批应为六行。
SELECT COUNT(*) AS total_rows FROM ecommerce_analysis.raw_events;
SELECT source_batch, COUNT(*) AS rows_in_batch FROM ecommerce_analysis.raw_events
GROUP BY source_batch ORDER BY source_batch;
-- 将下面的结果导出 CSV 后交给 Codex 与 BigQuery 基准逐项对账（预期 184 行）。
SELECT source_table_date, event_name,
 COUNT(*) AS event_count,
 COUNT(DISTINCT user_pseudo_id) AS distinct_nonnull_users,
 SUM(user_pseudo_id IS NULL) AS null_user_id_rows,
 SUM(user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) = '') AS blank_user_id_rows,
 MIN(event_timestamp_us) AS min_event_timestamp_us,
 MAX(event_timestamp_us) AS max_event_timestamp_us
FROM ecommerce_analysis.raw_events
GROUP BY source_table_date, event_name
ORDER BY source_table_date, event_name;
