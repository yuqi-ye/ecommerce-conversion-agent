-- 在 DataGrip 的 MySQL 查询窗口执行，不在 BigQuery 执行。
-- 只新建独立试导入表，不删除或覆盖已有表。
-- 此文件只需执行一次；若提示表已存在，停止并反馈，不要删表。
CREATE TABLE ecommerce_analysis.sample_events_20201201 (
  source_row_no INT UNSIGNED NOT NULL PRIMARY KEY,
  source_table_date CHAR(8) NOT NULL,
  event_date CHAR(8) NOT NULL,
  event_name VARCHAR(32) NOT NULL,
  user_pseudo_id VARCHAR(255),
  event_timestamp_us BIGINT NOT NULL,
  user_first_touch_timestamp_us BIGINT,
  traffic_source_source VARCHAR(255),
  traffic_source_medium VARCHAR(255),
  device_category VARCHAR(32),
  user_pseudo_id_is_null BOOLEAN NOT NULL,
  traffic_source_source_is_null BOOLEAN NOT NULL,
  traffic_source_medium_is_null BOOLEAN NOT NULL,
  device_category_is_null BOOLEAN NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
