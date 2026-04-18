-- Geographic Market Intelligence — one-time schema bootstrap.
--
-- What this does:
--   * Creates the schema used by Tab 2 (Build Territory) to store user input.
--   * Creates the `territory_definitions` Delta table the app reads/writes.
--
-- How to run:
--   Open this file in the Databricks SQL Editor (or any notebook) and click
--   Run. Both statements are idempotent — safe to re-run any time.
--
-- Customize for your workspace:
--   If your catalog or schema names differ from the demo defaults, replace
--   `eli_lilly_demo` / `app_data` below AND set the matching environment
--   variables (`APP_CATALOG`, `APP_SCHEMA`, ...) in `app.yaml`.

CREATE SCHEMA IF NOT EXISTS eli_lilly_demo.app_data
  COMMENT 'Storage for the Geographic Market Intelligence Streamlit app';

CREATE TABLE IF NOT EXISTS eli_lilly_demo.app_data.territory_definitions (
  territory_id     INT       COMMENT 'Auto-incremented unique territory id',
  territory_name   STRING    COMMENT 'User-supplied territory name',
  states_included  ARRAY<STRING> COMMENT '2-letter state codes covered by the territory',
  owner_name       STRING    COMMENT 'Manager / owner of the territory',
  created_by       STRING    COMMENT 'Username who created the territory (current_user())',
  created_date     TIMESTAMP COMMENT 'Creation timestamp',
  notes            STRING    COMMENT 'Optional strategy notes (<=500 chars)'
)
USING DELTA
COMMENT 'User-defined geographic territories captured from the Streamlit app';
