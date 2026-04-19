-- Source of truth for the app's schema + territory_definitions table.
-- Applied automatically by `./deploy.sh` — placeholders are substituted
-- from `app.yaml`. To run manually in the SQL Editor, replace
-- {{CATALOG}} and {{APP_SCHEMA}} with your actual names.

CREATE SCHEMA IF NOT EXISTS {{CATALOG}}.{{APP_SCHEMA}};

CREATE TABLE IF NOT EXISTS {{CATALOG}}.{{APP_SCHEMA}}.territory_definitions (
  territory_id     INT,
  territory_name   STRING,
  states_included  ARRAY<STRING>,
  owner_name       STRING,
  created_by       STRING,
  created_date     TIMESTAMP,
  notes            STRING
)
USING DELTA;
