"""Central configuration read from environment variables.

Every workspace-specific identifier the app touches lives here. Set these
as environment variables (locally via `.env` / shell export, in Databricks
Apps via `app.yaml` `env:`) and the rest of the codebase will follow.

Defaults match the original Eli Lilly demo so the repo runs unchanged
against the reference workspace. Override any of them to point the app at
a different catalog, schema, or dashboard.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Unity Catalog namespace
# ---------------------------------------------------------------------------

#: Catalog that holds all schemas the app reads or writes.
CATALOG: str = os.environ.get("APP_CATALOG", "eli_lilly_demo")

#: Schema with silver-tier claims tables (diagnosis, medical_claim, ...).
SILVER_SCHEMA: str = os.environ.get("APP_SILVER_SCHEMA", "silver_claims")

#: Schema with gold-tier patient / claims analytics tables.
GOLD_SCHEMA: str = os.environ.get("APP_GOLD_SCHEMA", "gold_claims")

#: Schema the app creates and writes user-defined territories into.
APP_SCHEMA: str = os.environ.get("APP_SCHEMA", "app_data")

# ---------------------------------------------------------------------------
# Fully-qualified table names
# ---------------------------------------------------------------------------

PATIENT_SUMMARY_TABLE: str = (
    f"{CATALOG}.{GOLD_SCHEMA}."
    + os.environ.get("APP_PATIENT_TABLE", "patient_summary")
)

DIAGNOSIS_TABLE: str = (
    f"{CATALOG}.{SILVER_SCHEMA}."
    + os.environ.get("APP_DIAGNOSIS_TABLE", "diagnosis")
)

TERRITORY_TABLE: str = (
    f"{CATALOG}.{APP_SCHEMA}."
    + os.environ.get("APP_TERRITORY_TABLE", "territory_definitions")
)

# ---------------------------------------------------------------------------
# Embedded AI/BI dashboard
# ---------------------------------------------------------------------------

#: Dashboard ID shown on Tab 1. Empty means "no dashboard configured" and
#: the app renders a friendly placeholder instead of an iframe.
POPULATION_HEALTH_DASHBOARD_ID: str = os.environ.get(
    "APP_DASHBOARD_ID",
    "01f13ac6dda01c0da0fc8039401cd345",
)

POPULATION_HEALTH_DASHBOARD_NAME: str = os.environ.get(
    "APP_DASHBOARD_NAME",
    "Population Health Executive Dashboard",
)
