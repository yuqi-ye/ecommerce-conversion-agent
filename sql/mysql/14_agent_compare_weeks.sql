-- Agent 工具的 MySQL 手动验收版；在 DataGrip 全文执行。
-- 唯一需要改的参数是目标首访周（周一）。
-- Python 工具使用参数绑定；这里的会话变量仅为手动验证使用。
SET @target_week = DATE('2020-12-21');
SET @previous_week = DATE_SUB(@target_week, INTERVAL 7 DAY);
SET @valid = WEEKDAY(@target_week) = 0
    AND @previous_week >= DATE('2020-11-02')
    AND @target_week <= DATE('2021-01-18');

SELECT CASE WHEN @valid THEN 'ok'
            ELSE '不支持该日期：必须是2020-11-09至2021-01-18之间的周一'
       END AS input_status;

WITH selected AS (
 SELECT CASE
          WHEN first_visit_us < TIMESTAMPDIFF(SECOND,'1970-01-01 00:00:00',@target_week)*1000000
          THEN @previous_week ELSE @target_week
        END AS cohort_week,
        purchased_7d
 FROM ecommerce_analysis.v_new_user_cohort
 WHERE @valid AND main_analysis_eligible = 1
   AND first_visit_us >= TIMESTAMPDIFF(SECOND,'1970-01-01 00:00:00',@previous_week)*1000000
   AND first_visit_us < TIMESTAMPDIFF(SECOND,'1970-01-01 00:00:00',DATE_ADD(@target_week,INTERVAL 7 DAY))*1000000
)
SELECT cohort_week, COUNT(*) AS new_users, SUM(purchased_7d) AS buyers_7d,
 ROUND(CAST(SUM(purchased_7d) AS DECIMAL(30,12))/COUNT(*)*100,4) AS conversion_rate_pct
FROM selected
GROUP BY cohort_week
ORDER BY cohort_week;
