-- Run once in the Databricks SQL Editor before the first deploy.
-- Safe to re-run. Creates the schema and table the app writes to.

CREATE SCHEMA IF NOT EXISTS eli_lilly_demo.app_data;

CREATE TABLE IF NOT EXISTS eli_lilly_demo.app_data.territory_definitions (
  territory_id     INT,
  territory_name   STRING,
  states_included  ARRAY<STRING>,
  owner_name       STRING,
  created_by       STRING,
  created_date     TIMESTAMP,
  notes            STRING
)
USING DELTA;
