-- 在 DataGrip 现有管理连接中逐条执行。只需执行一次。
-- 1. 创建本机专用账号。结果中的 generated password 是新账号密码，只在本机保存。
-- 若提示账号已存在，停止反馈；不要删除或重置已有账号。
CREATE USER 'ecommerce_agent'@'localhost' IDENTIFIED BY RANDOM PASSWORD;

-- 2. 只授权查询已审核的用户视图。
GRANT SELECT ON ecommerce_analysis.v_new_user_cohort TO 'ecommerce_agent'@'localhost';

-- 3. 核对授权（此查询不显示密码）。
SHOW GRANTS FOR 'ecommerce_agent'@'localhost';
