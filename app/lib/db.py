"""SQL helpers. Uses the viewer's OBO token in prod, CLI profile locally."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterable, Sequence

import pandas as pd
from databricks import sql
from databricks.sdk.core import Config

def _warehouse_id() -> str:
    wid = os.environ.get("DATABRICKS_WAREHOUSE_ID", "").strip()
    if not wid:
        raise RuntimeError(
            "DATABRICKS_WAREHOUSE_ID is not set. Set it in app.yaml (deploy) "
            "or export it locally."
        )
    return wid


def _server_hostname(cfg: Config | None = None) -> str:
    host = (cfg.host if cfg else None) or os.environ.get("DATABRICKS_HOST", "")
    return host.replace("https://", "").replace("http://", "").rstrip("/")


def _http_path() -> str:
    return f"/sql/1.0/warehouses/{_warehouse_id()}"


@contextmanager
def _connect(user_token: str | None = None):
    if user_token:
        conn = sql.connect(
            server_hostname=_server_hostname(),
            http_path=_http_path(),
            access_token=user_token,
        )
    else:
        cfg = Config()
        conn = sql.connect(
            server_hostname=_server_hostname(cfg),
            http_path=_http_path(),
            credentials_provider=lambda: cfg.authenticate,
        )
    try:
        yield conn
    finally:
        conn.close()


def sql_query(
    query: str,
    params: Sequence[Any] | None = None,
    *,
    user_token: str | None = None,
) -> pd.DataFrame:
    """Execute a query and return a DataFrame."""
    with _connect(user_token) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or [])
            try:
                return cur.fetchall_arrow().to_pandas()
            except Exception:
                cols = [d[0] for d in cur.description] if cur.description else []
                return pd.DataFrame(cur.fetchall(), columns=cols)


def sql_exec(
    query: str,
    params: Sequence[Any] | None = None,
    *,
    user_token: str | None = None,
) -> None:
    """Execute a non-returning statement (DDL, INSERT, DELETE)."""
    with _connect(user_token) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or [])


def sql_scalar(
    query: str,
    params: Sequence[Any] | None = None,
    *,
    user_token: str | None = None,
) -> Any:
    """Execute a query expected to return a single scalar value."""
    df = sql_query(query, params, user_token=user_token)
    if df.empty:
        return None
    return df.iloc[0, 0]


def get_user_token() -> str | None:
    """Return the OBO access token of the current Streamlit viewer, if any.

    Inside a Databricks App the user's access token is forwarded via the
    `X-Forwarded-Access-Token` header. When running locally there is no such
    header and we return None so the SDK Config flow takes over.
    """
    try:
        import streamlit as st

        headers = getattr(st.context, "headers", None)
        if headers is None:
            return None
        token = headers.get("x-forwarded-access-token") or headers.get(
            "X-Forwarded-Access-Token"
        )
        return token or None
    except Exception:
        return None


def get_current_user(user_token: str | None = None) -> str:
    """Return the username of the current user via SQL `current_user()`."""
    try:
        return str(sql_scalar("SELECT current_user()", user_token=user_token) or "unknown")
    except Exception:
        return "unknown"


def get_workspace_host() -> str:
    """Return the workspace host (https://...) for building embed URLs."""
    host = os.environ.get("DATABRICKS_HOST", "")
    if not host:
        try:
            host = Config().host or ""
        except Exception:
            host = ""
    host = host.rstrip("/")
    if host and not host.startswith("http"):
        host = f"https://{host}"
    return host
