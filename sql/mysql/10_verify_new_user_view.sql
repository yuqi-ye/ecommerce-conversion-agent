-- 创建视图之后，单独运行这整个查询；预期两列、六行。
SELECT '视图总人数' AS metric, COUNT(*) AS value
FROM ecommerce_analysis.v_new_user_cohort
UNION ALL
SELECT '去重用户数', COUNT(DISTINCT user_pseudo_id) FROM ecommerce_analysis.v_new_user_cohort
UNION ALL
SELECT '首访与 first-touch 完全一致人数', SUM(first_touch_exact) FROM ecommerce_analysis.v_new_user_cohort
UNION ALL
SELECT '购买早于首访人数', SUM(purchase_before_first_visit) FROM ecommerce_analysis.v_new_user_cohort
UNION ALL
SELECT '主分析合格人数', SUM(main_analysis_eligible) FROM ecommerce_analysis.v_new_user_cohort
UNION ALL
SELECT '主分析合格人群中 7 日购买人数', SUM(CASE WHEN main_analysis_eligible = 1 THEN purchased_7d ELSE 0 END)
FROM ecommerce_analysis.v_new_user_cohort;
