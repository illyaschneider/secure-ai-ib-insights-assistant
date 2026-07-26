-- Sample SQL questions for the fictional IB assistant

-- 1) Which sectors generated the most revenue in the latest completed quarter?
SELECT sector, total_revenue_usd_mm, qoq_growth_pct, story_flag
FROM revenue_by_sector_quarter
WHERE quarter = '2026Q1'
ORDER BY total_revenue_usd_mm DESC;

-- 2) Why did Technology weaken in 2026Q1?
SELECT r.quarter, r.sector, r.total_revenue_usd_mm, r.qoq_growth_pct,
       m.volatility_index, m.credit_spread_bps, m.financing_condition,
       s.outlook_tone, s.key_explanation
FROM revenue_by_sector_quarter r
JOIN market_conditions m ON r.quarter = m.quarter
JOIN sector_outlook_notes s ON r.quarter = s.quarter AND r.sector = s.sector
WHERE r.quarter = '2026Q1' AND r.sector = 'Technology';

-- 3) Which Technology deals were delayed in 2026Q1?
SELECT deal_id, client_id, deal_name, deal_type, deal_value_usd_mm, delay_or_loss_reason
FROM deals
WHERE quarter = '2026Q1' AND sector = 'Technology' AND status = 'Delayed';

-- 4) Which pipeline opportunities are delayed and why?
SELECT opportunity_id, client_id, opportunity_name, sector, expected_fee_usd_mm, probability, delay_reason
FROM pipeline_opportunities
WHERE stage = 'Delayed'
ORDER BY expected_fee_usd_mm DESC;

-- 5) Which bankers own the largest weighted pipeline?
SELECT b.banker_name, t.team_name, c.pipeline_opportunity_count, c.pipeline_weighted_fee_usd_mm
FROM banker_coverage_summary c
JOIN bankers b ON c.banker_id = b.banker_id
JOIN teams t ON b.team_id = t.team_id
ORDER BY c.pipeline_weighted_fee_usd_mm DESC;
