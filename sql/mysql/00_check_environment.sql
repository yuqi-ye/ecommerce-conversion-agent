-- 在你平时使用的 MySQL 客户端中执行；只读取环境信息，不修改数据。
SELECT VERSION() AS mysql_version,
       DATABASE() AS current_database,
       @@local_infile AS local_infile_enabled,
       @@secure_file_priv AS server_import_directory,
       @@session.time_zone AS session_time_zone;
