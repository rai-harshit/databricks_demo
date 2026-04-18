"""App config. Override any of these via env vars in app.yaml."""

from __future__ import annotations

import os

CATALOG = os.environ.get("APP_CATALOG", "eli_lilly_demo")
SILVER_SCHEMA = os.environ.get("APP_SILVER_SCHEMA", "silver_claims")
GOLD_SCHEMA = os.environ.get("APP_GOLD_SCHEMA", "gold_claims")
APP_SCHEMA = os.environ.get("APP_SCHEMA", "app_data")

PATIENT_SUMMARY_TABLE = (
    f"{CATALOG}.{GOLD_SCHEMA}."
    + os.environ.get("APP_PATIENT_TABLE", "patient_summary")
)
DIAGNOSIS_TABLE = (
    f"{CATALOG}.{SILVER_SCHEMA}."
    + os.environ.get("APP_DIAGNOSIS_TABLE", "diagnosis")
)
TERRITORY_TABLE = (
    f"{CATALOG}.{APP_SCHEMA}."
    + os.environ.get("APP_TERRITORY_TABLE", "territory_definitions")
)

POPULATION_HEALTH_DASHBOARD_ID = os.environ.get(
    "APP_DASHBOARD_ID", "01f13ac6dda01c0da0fc8039401cd345"
)
POPULATION_HEALTH_DASHBOARD_NAME = os.environ.get(
    "APP_DASHBOARD_NAME", "Population Health Executive Dashboard"
)
