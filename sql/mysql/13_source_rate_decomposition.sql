-- MySQL：两周首次来源分解。输出的pp单位为百分点。
WITH g AS (
 SELECT traffic_source_source, traffic_source_medium,
 SUM(first_visit_us < 1608508800000000) AS n0,
 SUM(first_visit_us >= 1608508800000000) AS n1,
 SUM(CASE WHEN first_visit_us < 1608508800000000 THEN purchased_7d ELSE 0 END) AS b0,
 SUM(CASE WHEN first_visit_us >= 1608508800000000 THEN purchased_7d ELSE 0 END) AS b1
 FROM ecommerce_analysis.v_new_user_cohort
 WHERE main_analysis_eligible = 1
   AND first_visit_us >= 1607904000000000 AND first_visit_us < 1609113600000000
 GROUP BY traffic_source_source, traffic_source_medium
), rates AS (
 SELECT *,
 CAST(n0 AS DECIMAL(30,12))/SUM(n0) OVER () AS s0,
 CAST(n1 AS DECIMAL(30,12))/SUM(n1) OVER () AS s1,
 COALESCE(CAST(b0 AS DECIMAL(30,12))/NULLIF(n0,0),
          CAST(b1 AS DECIMAL(30,12))/NULLIF(n1,0)) AS r0,
 COALESCE(CAST(b1 AS DECIMAL(30,12))/NULLIF(n1,0),
          CAST(b0 AS DECIMAL(30,12))/NULLIF(n0,0)) AS r1
 FROM g
)
SELECT traffic_source_source, traffic_source_medium,
 n0 AS previous_new_users, n1 AS current_new_users,
 b0 AS previous_buyers, b1 AS current_buyers,
 b1-b0 AS buyer_change,
 -- 对缺失周显示NULL购买率；分解内部用对侧率填充，将变化分给结构项。
 CASE WHEN n0>0 THEN ROUND(r0*100,4) END AS previous_rate_pct,
 CASE WHEN n1>0 THEN ROUND(r1*100,4) END AS current_rate_pct,
 ROUND(s0*100,4) AS previous_share_pct,
 ROUND(s1*100,4) AS current_share_pct,
 ROUND((s1-s0)*(r0+r1)/2*100,6) AS source_mix_change_pp,
 ROUND((r1-r0)*(s0+s1)/2*100,6) AS within_source_change_pp
FROM rates
ORDER BY buyer_change, traffic_source_source, traffic_source_medium;
