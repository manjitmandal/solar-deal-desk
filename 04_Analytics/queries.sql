-- Solar Deal Desk | sales performance analytics (SQLite dialect)
-- Tables: opportunities (synthetic_opportunities.csv), snapshots (weekly_pipeline_snapshots.csv)
-- All data is SYNTHETIC. Small samples per group -> treat results as directional.

-- name: overall
SELECT COUNT(*)                                             AS closed_deals,
       SUM(Is_Won)                                          AS won,
       ROUND(1.0 * SUM(Is_Won) / COUNT(*), 3)               AS win_rate_count,
       ROUND(SUM(CASE WHEN Is_Won = 1 THEN Amount_USD END) / SUM(Amount_USD), 3) AS win_rate_value,
       ROUND(SUM(CASE WHEN Is_Won = 1 THEN Amount_USD END) / 1e6, 1) AS bookings_usd_m
FROM opportunities
WHERE Is_Closed = 1;

-- name: by_lead_source
SELECT Lead_Source, COUNT(*) AS closed_deals, SUM(Is_Won) AS won,
       ROUND(1.0 * SUM(Is_Won) / COUNT(*), 3) AS win_rate
FROM opportunities WHERE Is_Closed = 1
GROUP BY Lead_Source ORDER BY win_rate DESC;

-- name: by_segment
SELECT Segment, COUNT(*) AS closed_deals, SUM(Is_Won) AS won,
       ROUND(1.0 * SUM(Is_Won) / COUNT(*), 3) AS win_rate,
       ROUND(AVG(Est_Contribution_Margin_Pct), 3) AS avg_cm
FROM opportunities WHERE Is_Closed = 1
GROUP BY Segment ORDER BY win_rate DESC;

-- name: by_region
SELECT Region, COUNT(*) AS closed_deals, SUM(Is_Won) AS won,
       ROUND(1.0 * SUM(Is_Won) / COUNT(*), 3) AS win_rate,
       ROUND(SUM(CASE WHEN Is_Won = 1 THEN Amount_USD ELSE 0 END) / 1e6, 1) AS bookings_usd_m
FROM opportunities WHERE Is_Closed = 1
GROUP BY Region ORDER BY win_rate DESC;

-- name: by_value_proposition
SELECT Value_Proposition, COUNT(*) AS closed_deals, SUM(Is_Won) AS won,
       ROUND(1.0 * SUM(Is_Won) / COUNT(*), 3) AS win_rate,
       ROUND(AVG(Est_Contribution_Margin_Pct), 3) AS avg_cm
FROM opportunities WHERE Is_Closed = 1
GROUP BY Value_Proposition ORDER BY win_rate DESC;

-- name: loss_reasons
SELECT Loss_Reason, COUNT(*) AS lost_deals,
       ROUND(1.0 * COUNT(*) / (SELECT COUNT(*) FROM opportunities WHERE Stage = 'Closed Lost'), 3) AS share,
       ROUND(SUM(Amount_USD) / 1e6, 1) AS lost_value_usd_m
FROM opportunities WHERE Stage = 'Closed Lost'
GROUP BY Loss_Reason ORDER BY lost_deals DESC;

-- name: discount_bands
SELECT CASE WHEN Discount_Pct = 0 THEN '0%'
            WHEN Discount_Pct <= 0.03 THEN '1-3%'
            WHEN Discount_Pct <= 0.06 THEN '4-6%'
            ELSE '>6%' END AS discount_band,
       COUNT(*) AS closed_deals,
       ROUND(1.0 * SUM(Is_Won) / COUNT(*), 3) AS win_rate,
       ROUND(AVG(Est_Contribution_Margin_Pct), 3) AS avg_cm
FROM opportunities WHERE Is_Closed = 1
GROUP BY discount_band ORDER BY MIN(Discount_Pct);

-- name: won_vs_lost_profile
SELECT CASE WHEN Is_Won = 1 THEN 'Won' ELSE 'Lost' END AS outcome,
       COUNT(*) AS deals,
       ROUND(AVG(Amount_USD) / 1e6, 2) AS avg_deal_usd_m,
       ROUND(AVG(Capacity_MWp), 0) AS avg_mwp,
       ROUND(AVG(Sales_Cycle_Days), 0) AS avg_cycle_days,
       ROUND(AVG(Discount_Pct), 3) AS avg_discount
FROM opportunities WHERE Is_Closed = 1
GROUP BY outcome;

-- name: q4_forecast_current
-- Current-quarter (Q4-2026) forecast by forecast category, as of the latest snapshot
SELECT Forecast_Category, COUNT(*) AS deals,
       ROUND(SUM(Amount_USD) / 1e6, 1) AS amount_usd_m,
       ROUND(SUM(Amount_USD * Probability_Pct / 100.0) / 1e6, 1) AS weighted_usd_m
FROM opportunities
WHERE Close_Date BETWEEN '2026-10-01' AND '2026-12-31'
GROUP BY Forecast_Category
ORDER BY CASE Forecast_Category WHEN 'Closed' THEN 1 WHEN 'Commit' THEN 2 WHEN 'Best Case' THEN 3 WHEN 'Pipeline' THEN 4 ELSE 5 END;

-- name: weekly_q4_forecast
-- Weekly trend of the Q4-2026 forecast (deals whose close date is in Q4)
SELECT Snapshot_Date,
       ROUND(SUM(CASE WHEN Forecast_Category = 'Closed'   THEN Amount_USD ELSE 0 END) / 1e6, 1) AS closed_won_usd_m,
       ROUND(SUM(CASE WHEN Forecast_Category = 'Commit'   THEN Amount_USD ELSE 0 END) / 1e6, 1) AS commit_usd_m,
       ROUND(SUM(CASE WHEN Forecast_Category = 'Best Case' THEN Amount_USD ELSE 0 END) / 1e6, 1) AS best_case_usd_m,
       ROUND(SUM(CASE WHEN Forecast_Category = 'Pipeline' THEN Amount_USD ELSE 0 END) / 1e6, 1) AS pipeline_usd_m,
       ROUND(SUM(Amount_USD * Probability_Pct / 100.0) / 1e6, 1) AS weighted_forecast_usd_m
FROM snapshots
WHERE Close_Date BETWEEN '2026-10-01' AND '2026-12-31'
GROUP BY Snapshot_Date ORDER BY Snapshot_Date;

-- name: open_pipeline_by_region
SELECT Region, COUNT(*) AS open_deals, ROUND(SUM(Capacity_MWp), 0) AS open_mwp,
       ROUND(SUM(Amount_USD) / 1e6, 1) AS open_usd_m,
       ROUND(SUM(Amount_USD * Probability_Pct / 100.0) / 1e6, 1) AS weighted_usd_m
FROM opportunities WHERE Is_Closed = 0
GROUP BY Region ORDER BY weighted_usd_m DESC;
