-- 在 DataGrip 的 MySQL 连接执行。只新建正式表，不删除已有表。
-- 表已存在时报错并停止，不要删表。source_batch + source_row_no 防止同批数据重复导入。
CREATE TABLE ecommerce_analysis.raw_events (
  source_batch VARCHAR(32) NOT NULL,
  source_row_no INT UNSIGNED NOT NULL,
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
  device_category_is_null BOOLEAN NOT NULL,
  PRIMARY KEY (source_batch, source_row_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;
