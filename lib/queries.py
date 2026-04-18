"""All SQL used by the app, kept in one place for easy review.

Naming convention: `Q_*` queries return rows (use `sql_query`),
`STMT_*` are write statements (use `sql_exec`).

Parameters use the `databricks-sql-connector` `?` placeholder style.
"""

# ---------------------------------------------------------------------------
# Tab 1 - Population Health Dashboard
# ---------------------------------------------------------------------------

Q_KPIS = """
SELECT
  COUNT(DISTINCT patient_id)               AS total_patients,
  SUM(CAST(total_claims AS INT))           AS total_claims,
  AVG(CAST(total_claims AS INT))           AS avg_claims_per_patient
FROM eli_lilly_demo.gold_claims.patient_summary
"""

Q_UNIQUE_DIAGNOSES = """
SELECT COUNT(DISTINCT diagnosis_code) AS unique_diagnoses
FROM eli_lilly_demo.silver_claims.diagnosis
"""

Q_TOP_STATES = """
SELECT state, COUNT(DISTINCT patient_id) AS patients
FROM eli_lilly_demo.gold_claims.patient_summary
WHERE state IS NOT NULL
GROUP BY state
ORDER BY patients DESC
LIMIT 10
"""

Q_PATIENT_SAMPLE = """
SELECT
  patient_id,
  state,
  age,
  gender,
  CAST(total_claims AS INT) AS total_claims,
  enrollment_days
FROM eli_lilly_demo.gold_claims.patient_summary
ORDER BY CAST(total_claims AS INT) DESC NULLS LAST
LIMIT 25
"""

# ---------------------------------------------------------------------------
# Tab 2 - Territory Builder
# ---------------------------------------------------------------------------

Q_DISTINCT_STATES = """
SELECT DISTINCT state
FROM eli_lilly_demo.gold_claims.patient_summary
WHERE state IS NOT NULL
ORDER BY state
"""

Q_NEXT_TERRITORY_ID = """
SELECT COALESCE(MAX(territory_id), 0) + 1 AS next_id
FROM eli_lilly_demo.app_data.territory_definitions
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
        INSERT INTO eli_lilly_demo.app_data.territory_definitions
          (territory_id, territory_name, states_included,
           owner_name, created_by, created_date, notes)
        VALUES (?, ?, {array_expr}, ?, current_user(), current_timestamp(), ?)
    """

# ---------------------------------------------------------------------------
# Tab 3 - View Territories
# ---------------------------------------------------------------------------

Q_ALL_TERRITORIES = """
SELECT
  territory_id,
  territory_name,
  states_included,
  SIZE(states_included)                              AS num_states,
  owner_name,
  created_by,
  DATE_FORMAT(created_date, 'yyyy-MM-dd HH:mm')      AS created_date,
  notes
FROM eli_lilly_demo.app_data.territory_definitions
ORDER BY created_date DESC
"""

Q_TERRITORY_SUMMARY = """
SELECT
  COUNT(*)                       AS total_territories,
  COUNT(DISTINCT created_by)     AS total_contributors
FROM eli_lilly_demo.app_data.territory_definitions
"""

Q_UNIQUE_STATES_COVERED = """
SELECT COUNT(DISTINCT state) AS states_covered
FROM eli_lilly_demo.app_data.territory_definitions
LATERAL VIEW EXPLODE(states_included) t AS state
"""

Q_TERRITORY_PATIENT_ROLLUP = """
WITH territory_states AS (
  SELECT
    t.territory_id,
    t.territory_name,
    state_code
  FROM eli_lilly_demo.app_data.territory_definitions t
  LATERAL VIEW EXPLODE(t.states_included) s AS state_code
)
SELECT
  ts.territory_id,
  ts.territory_name,
  COUNT(DISTINCT p.patient_id)                    AS patients_in_territory,
  SUM(CAST(p.total_claims AS INT))                AS total_claims_in_territory
FROM territory_states ts
LEFT JOIN eli_lilly_demo.gold_claims.patient_summary p
  ON p.state = ts.state_code
GROUP BY ts.territory_id, ts.territory_name
ORDER BY patients_in_territory DESC NULLS LAST
"""

STMT_DELETE_TERRITORY = """
DELETE FROM eli_lilly_demo.app_data.territory_definitions
WHERE territory_id = ?
"""
