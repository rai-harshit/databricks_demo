"""All SQL used by the app, kept in one place for easy review.

Naming convention: `Q_*` queries return rows (use `sql_query`),
`STMT_*` are write statements (use `sql_exec`).

Parameters use the `databricks-sql-connector` `?` placeholder style.

Table names are injected from `lib.config` so the same code works against a
different catalog / schema just by changing environment variables.
"""

from .config import (
    DIAGNOSIS_TABLE,
    PATIENT_SUMMARY_TABLE,
    TERRITORY_TABLE,
)

# ---------------------------------------------------------------------------
# Tab 1 - Population Health Dashboard
#
# The app embeds the published AI/BI dashboard via iframe, so these queries
# are kept only as a reference / fallback (e.g. if you want to build custom
# visualizations on top of the same source tables).
# ---------------------------------------------------------------------------

Q_KPIS = f"""
SELECT
  COUNT(DISTINCT patient_id)               AS total_patients,
  SUM(CAST(total_claims AS INT))           AS total_claims,
  AVG(CAST(total_claims AS INT))           AS avg_claims_per_patient
FROM {PATIENT_SUMMARY_TABLE}
"""

Q_UNIQUE_DIAGNOSES = f"""
SELECT COUNT(DISTINCT diagnosis_code) AS unique_diagnoses
FROM {DIAGNOSIS_TABLE}
"""

Q_TOP_STATES = f"""
SELECT state, COUNT(DISTINCT patient_id) AS patients
FROM {PATIENT_SUMMARY_TABLE}
WHERE state IS NOT NULL
GROUP BY state
ORDER BY patients DESC
LIMIT 10
"""

Q_PATIENT_SAMPLE = f"""
SELECT
  patient_id,
  state,
  age,
  gender,
  CAST(total_claims AS INT) AS total_claims,
  enrollment_days
FROM {PATIENT_SUMMARY_TABLE}
ORDER BY CAST(total_claims AS INT) DESC NULLS LAST
LIMIT 25
"""

# ---------------------------------------------------------------------------
# Tab 2 - Territory Builder
# ---------------------------------------------------------------------------

Q_DISTINCT_STATES = f"""
SELECT DISTINCT state
FROM {PATIENT_SUMMARY_TABLE}
WHERE state IS NOT NULL
ORDER BY state
"""

Q_NEXT_TERRITORY_ID = f"""
SELECT COALESCE(MAX(territory_id), 0) + 1 AS next_id
FROM {TERRITORY_TABLE}
"""


def insert_territory_stmt(num_states: int) -> str:
    """Build a parameterized INSERT for a territory with `num_states` states.

    `states_included` is built with an inline `ARRAY(?, ?, ...)` literal so we
    can pass each state as its own parameter. `created_date` and `created_by`
    are filled server-side via SQL functions.
    """
    array_placeholders = ", ".join(["?"] * num_states) if num_states else ""
    array_expr = f"ARRAY({array_placeholders})" if num_states else "ARRAY()"
    return f"""
        INSERT INTO {TERRITORY_TABLE}
          (territory_id, territory_name, states_included,
           owner_name, created_by, created_date, notes)
        VALUES (?, ?, {array_expr}, ?, current_user(), current_timestamp(), ?)
    """

# ---------------------------------------------------------------------------
# Tab 3 - View Territories
# ---------------------------------------------------------------------------

Q_ALL_TERRITORIES = f"""
SELECT
  territory_id,
  territory_name,
  states_included,
  SIZE(states_included)                              AS num_states,
  owner_name,
  created_by,
  DATE_FORMAT(created_date, 'yyyy-MM-dd HH:mm')      AS created_date,
  notes
FROM {TERRITORY_TABLE}
ORDER BY created_date DESC
"""

Q_TERRITORY_SUMMARY = f"""
SELECT
  COUNT(*)                       AS total_territories,
  COUNT(DISTINCT created_by)     AS total_contributors
FROM {TERRITORY_TABLE}
"""

Q_UNIQUE_STATES_COVERED = f"""
SELECT COUNT(DISTINCT state) AS states_covered
FROM {TERRITORY_TABLE}
LATERAL VIEW EXPLODE(states_included) t AS state
"""

Q_TERRITORY_PATIENT_ROLLUP = f"""
WITH territory_states AS (
  SELECT
    t.territory_id,
    t.territory_name,
    state_code
  FROM {TERRITORY_TABLE} t
  LATERAL VIEW EXPLODE(t.states_included) s AS state_code
)
SELECT
  ts.territory_id,
  ts.territory_name,
  COUNT(DISTINCT p.patient_id)                    AS patients_in_territory,
  SUM(CAST(p.total_claims AS INT))                AS total_claims_in_territory
FROM territory_states ts
LEFT JOIN {PATIENT_SUMMARY_TABLE} p
  ON p.state = ts.state_code
GROUP BY ts.territory_id, ts.territory_name
ORDER BY patients_in_territory DESC NULLS LAST
"""

STMT_DELETE_TERRITORY = f"""
DELETE FROM {TERRITORY_TABLE}
WHERE territory_id = ?
"""
