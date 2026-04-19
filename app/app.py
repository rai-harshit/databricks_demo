"""Geographic Market Intelligence — Eli Lilly demo Streamlit app.

Three tabs:
  1. Population Health Dashboard   (read-only KPIs / charts)
  2. Build Territory               (form -> insert into Delta)
  3. View Territories              (Delta read + multi-user analytics)
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Iterable

import pandas as pd
import streamlit as st

from lib import queries as Q
from lib.config import (
    POPULATION_HEALTH_DASHBOARD_ID,
    POPULATION_HEALTH_DASHBOARD_NAME,
    TERRITORY_TABLE,
)
from lib.db import (
    get_current_user,
    get_user_token,
    get_workspace_host,
    sql_exec,
    sql_query,
    sql_scalar,
)


# ---------------------------------------------------------------------------
# Page config / global state
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Geographic Market Intelligence",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Geographic Market Intelligence")
st.caption(
    "End-to-end demo: explore population health data, define custom market "
    "territories, and share them across the team via a Delta table."
)

USER_TOKEN = get_user_token()


# Static lookup so multi-select can show "California (CA)" but store the code.
US_STATE_NAMES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
    "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
    "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico",
}


def _state_label(code: str) -> str:
    name = US_STATE_NAMES.get(code, code)
    return f"{name} ({code})"


# ---------------------------------------------------------------------------
# Cached lookups (small, slow-changing)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def load_distinct_states() -> list[str]:
    df = sql_query(Q.Q_DISTINCT_STATES, user_token=USER_TOKEN)
    return df["state"].dropna().tolist()


def load_territories() -> pd.DataFrame:
    return sql_query(Q.Q_ALL_TERRITORIES, user_token=USER_TOKEN)


def load_territory_summary() -> tuple[int, int, int]:
    summary = sql_query(Q.Q_TERRITORY_SUMMARY, user_token=USER_TOKEN)
    states = sql_scalar(Q.Q_UNIQUE_STATES_COVERED, user_token=USER_TOKEN)
    if summary.empty:
        return 0, 0, int(states or 0)
    row = summary.iloc[0]
    return (
        int(row["total_territories"] or 0),
        int(row["total_contributors"] or 0),
        int(states or 0),
    )


def load_territory_rollup() -> pd.DataFrame:
    return sql_query(Q.Q_TERRITORY_PATIENT_ROLLUP, user_token=USER_TOKEN)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_dashboard, tab_builder, tab_view = st.tabs(
    ["📊 Dashboard", "🗺️ Build Territory", "📋 View Territories"]
)


# ===========================================================================
# Tab 1 — Population Health Dashboard (embedded AI/BI dashboard)
# ===========================================================================
with tab_dashboard:
    host = get_workspace_host()
    dashboard_url = (
        f"{host}/dashboardsv3/{POPULATION_HEALTH_DASHBOARD_ID}/published"
        if host
        else ""
    )
    embed_url = (
        f"{host}/embed/dashboardsv3/{POPULATION_HEALTH_DASHBOARD_ID}"
        if host
        else ""
    )

    header_cols = st.columns([5, 1])
    header_cols[0].subheader(POPULATION_HEALTH_DASHBOARD_NAME)
    if dashboard_url:
        header_cols[1].link_button("Open in Databricks ↗", dashboard_url)

    st.caption(
        f"Published AI/BI dashboard `{POPULATION_HEALTH_DASHBOARD_ID}` embedded "
        "from the workspace. It renders with the publisher's credentials "
        "(`embed_credentials: true`)."
    )

    if not embed_url:
        st.error(
            "Could not resolve the workspace host. Set `DATABRICKS_HOST` or "
            "use a CLI profile (`DATABRICKS_CONFIG_PROFILE=<your-profile>`)."
        )
    else:
        st.iframe(embed_url, height=900)


# ===========================================================================
# Tab 2 — Build Territory
# ===========================================================================
with tab_builder:
    st.subheader("Define a new geographic territory")
    st.caption(
        "Select states from the patient population, attach a name and owner, "
        f"and persist it to `{TERRITORY_TABLE}`."
    )

    try:
        available_states = load_distinct_states()
    except Exception as exc:
        st.error(f"Failed to load state list: {exc}")
        available_states = []

    current_user = get_current_user(USER_TOKEN)

    info_cols = st.columns(2)
    info_cols[0].text_input(
        "Created by", value=current_user, disabled=True,
        help="Auto-filled from current_user() — cannot be edited.",
    )
    info_cols[1].text_input(
        "Created date",
        value=datetime.now().strftime("%Y-%m-%d %H:%M"),
        disabled=True,
        help="Server-side current_timestamp() is used at insert time.",
    )

    with st.form("territory_form", clear_on_submit=True):
        territory_name = st.text_input(
            "Territory Name *",
            placeholder="e.g., Northeast Region, West Coast Markets",
        )
        states = st.multiselect(
            "Select States *",
            options=available_states,
            format_func=_state_label,
            placeholder="Pick one or more states",
        )
        owner_name = st.text_input(
            "Owner / Manager Name *",
            placeholder="e.g., Sarah Chen, John Smith",
        )
        notes = st.text_area(
            "Notes / Strategy",
            placeholder="e.g., High growth potential, competitive market, "
                        "expansion focus",
            max_chars=500,
            height=120,
        )

        submitted = st.form_submit_button("💾 Save Territory", type="primary")

    if submitted:
        missing = []
        if not territory_name.strip():
            missing.append("Territory Name")
        if not states:
            missing.append("Select States")
        if not owner_name.strip():
            missing.append("Owner / Manager Name")

        if missing:
            st.error("Missing required fields: " + ", ".join(missing))
        else:
            try:
                next_id = int(
                    sql_scalar(Q.Q_NEXT_TERRITORY_ID, user_token=USER_TOKEN) or 1
                )
                stmt = Q.insert_territory_stmt(len(states))
                params = [
                    next_id,
                    territory_name.strip(),
                    *states,
                    owner_name.strip(),
                    notes.strip() or None,
                ]
                sql_exec(stmt, params, user_token=USER_TOKEN)
            except Exception as exc:
                st.error(f"Save failed: {exc}")
            else:
                st.success(
                    f"Territory **{territory_name.strip()}** saved with "
                    f"`territory_id = {next_id}`."
                )
                st.balloons()


# ===========================================================================
# Tab 3 — View Territories
# ===========================================================================
with tab_view:
    st.subheader("All territories — shared across users")
    st.caption(
        f"Live read of `{TERRITORY_TABLE}`. "
        "Anyone using the app can see and analyze every territory."
    )

    try:
        terr_df = load_territories()
    except Exception as exc:
        st.error(f"Failed to load territories: {exc}")
        terr_df = pd.DataFrame()

    try:
        total, contributors, states_cov = load_territory_summary()
    except Exception:
        total, contributors, states_cov = (
            len(terr_df) if not terr_df.empty else 0,
            0,
            0,
        )

    s1, s2, s3 = st.columns(3)
    s1.metric("Territories created", f"{total:,}")
    s2.metric("Unique states covered", f"{states_cov:,}")
    s3.metric("Contributors", f"{contributors:,}")

    if terr_df.empty:
        st.info(
            "No territories created yet. Head to the **Build Territory** tab "
            "to create the first one."
        )
    else:
        f1, f2, f3 = st.columns([2, 2, 3])
        owner_filter = f1.multiselect(
            "Filter by owner",
            sorted(terr_df["owner_name"].dropna().unique().tolist()),
        )

        all_states_in_data = sorted(
            {s for arr in terr_df["states_included"].dropna() for s in arr}
        )
        state_filter = f2.multiselect(
            "Filter by state included",
            all_states_in_data,
        )
        name_filter = f3.text_input(
            "Search territory name",
            placeholder="Substring match…",
        )

        view = terr_df.copy()
        if owner_filter:
            view = view[view["owner_name"].isin(owner_filter)]
        if state_filter:
            view = view[
                view["states_included"].apply(
                    lambda arr: bool(set(arr if arr is not None else []) & set(state_filter))
                )
            ]
        if name_filter.strip():
            needle = name_filter.strip().lower()
            view = view[view["territory_name"].str.lower().str.contains(needle, na=False)]

        view_display = view.copy()
        view_display["states_included"] = view_display["states_included"].apply(
            lambda arr: ", ".join(arr) if arr is not None and len(arr) > 0 else ""
        )

        st.dataframe(
            view_display[
                [
                    "territory_id",
                    "territory_name",
                    "states_included",
                    "num_states",
                    "owner_name",
                    "created_by",
                    "created_date",
                    "notes",
                ]
            ],
            hide_index=True,
            width='stretch',
        )

        csv_buf = io.StringIO()
        view_display.to_csv(csv_buf, index=False)
        st.download_button(
            "⬇️ Export filtered territories as CSV",
            data=csv_buf.getvalue(),
            file_name="territories.csv",
            mime="text/csv",
        )

        st.divider()
        st.markdown("##### Patients per territory")
        st.caption(
            "Joins `territory_definitions` × exploded states × "
            "`patient_summary` to count covered patients and total claims."
        )
        try:
            rollup = load_territory_rollup()
        except Exception as exc:
            st.error(f"Failed to compute territory rollup: {exc}")
            rollup = pd.DataFrame()

        if rollup.empty:
            st.info("No rollup data yet.")
        else:
            rollup_display = rollup.copy()
            rollup_display["patients_in_territory"] = rollup_display[
                "patients_in_territory"
            ].fillna(0).astype(int)
            rollup_display["total_claims_in_territory"] = rollup_display[
                "total_claims_in_territory"
            ].fillna(0).astype(int)
            st.dataframe(
                rollup_display,
                hide_index=True,
                width='stretch',
            )

        st.divider()
        with st.expander("🗑️ Delete a territory", expanded=False):
            ids = view["territory_id"].tolist()
            if not ids:
                st.write("No territories match the current filters.")
            else:
                target = st.selectbox(
                    "Territory to delete",
                    options=ids,
                    format_func=lambda i: f"{i} — "
                    f"{view.loc[view['territory_id'] == i, 'territory_name'].iloc[0]}",
                )
                confirm = st.checkbox(
                    f"Yes, permanently delete territory `{target}` from the Delta table.",
                    key=f"confirm_delete_{target}",
                )
                if st.button("Delete", type="secondary", disabled=not confirm):
                    try:
                        sql_exec(
                            Q.STMT_DELETE_TERRITORY, [int(target)],
                            user_token=USER_TOKEN,
                        )
                    except Exception as exc:
                        st.error(f"Delete failed: {exc}")
                    else:
                        st.success(f"Territory {target} deleted.")
                        st.rerun()
