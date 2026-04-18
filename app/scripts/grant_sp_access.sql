-- Grant the Databricks App service principal permission to read the source
-- tables and read/write the app's Delta table.
--
-- How to use:
--   1. After `databricks apps create <app-name>`, grab the service principal
--      client id from `databricks apps get <app-name>` (field:
--      `service_principal_client_id`). Looks like a UUID.
--   2. Open this file in the Databricks SQL Editor, replace the two
--      placeholders below with real values, and click Run.
--
-- Notes:
--   * Object owners / account admins can run this. Regular users may need
--     their admin to execute it on their behalf.
--   * If your catalog / schemas differ from the demo defaults, change them
--     here too (and in `app.yaml`).

-- Replace this with the app service principal client id (UUID).
-- SET VAR app_sp = '<APP_SERVICE_PRINCIPAL_CLIENT_ID>';

GRANT USE CATALOG ON CATALOG eli_lilly_demo
  TO `<APP_SERVICE_PRINCIPAL_CLIENT_ID>`;

GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.gold_claims
  TO `<APP_SERVICE_PRINCIPAL_CLIENT_ID>`;

GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.silver_claims
  TO `<APP_SERVICE_PRINCIPAL_CLIENT_ID>`;

GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA eli_lilly_demo.app_data
  TO `<APP_SERVICE_PRINCIPAL_CLIENT_ID>`;
