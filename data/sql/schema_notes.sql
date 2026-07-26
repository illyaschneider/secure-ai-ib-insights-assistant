-- SQLite schema for Fictional Investment Bank AI Assistant Dataset
-- The ingestion script creates tables from CSV headers and adds traceability columns.
-- This file documents intended keys/relationships.

-- Dimension-style tables:
-- teams(team_id)
-- bankers(banker_id, team_id -> teams.team_id)
-- clients(client_id, primary_banker_id -> bankers.banker_id)

-- Fact/context tables:
-- deals(deal_id, client_id -> clients.client_id, lead_banker_id -> bankers.banker_id)
-- pipeline_opportunities(opportunity_id, client_id -> clients.client_id, owner_banker_id -> bankers.banker_id)
-- revenue_by_sector_quarter(quarter, sector)
-- revenue_by_region_quarter(quarter, region)
-- market_conditions(quarter)
-- sector_outlook_notes(quarter, sector)
-- client_activity(client_id, quarter)
-- banker_coverage_summary(banker_id)
