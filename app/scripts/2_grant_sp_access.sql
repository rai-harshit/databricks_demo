-- Run in the SQL Editor after `./deploy.sh` creates the app.
-- Replace <SP> with the service principal id that deploy.sh prints, then run.

GRANT USE CATALOG ON CATALOG eli_lilly_demo                    TO `<SP>`;
GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.gold_claims   TO `<SP>`;
GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.silver_claims TO `<SP>`;
GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA eli_lilly_demo.app_data TO `<SP>`;
