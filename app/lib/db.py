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
    """Deprecated: OBO disabled for Free Edition compatibility.

    The app now runs all SQL as the service principal. Kept as a stub so
    existing imports don't break; always returns None.
    """
    return None


def _header(name: str) -> str | None:
    try:
        import streamlit as st

        headers = getattr(st.context, "headers", None)
        if headers is None:
            return None
        return headers.get(name) or headers.get(name.lower()) or headers.get(name.title())
    except Exception:
        return None


def get_current_user(user_token: str | None = None) -> str:
    """Return the viewer's email from Databricks Apps forwarded headers.

    Databricks Apps always forwards the viewer identity via
    `X-Forwarded-Email` / `X-Forwarded-Preferred-Username`, even when OBO
    user-token passthrough is not enabled (e.g. Free Edition). Falls back to
    `SELECT current_user()` when running locally.
    """
    email = (
        _header("X-Forwarded-Email")
        or _header("X-Forwarded-Preferred-Username")
        or _header("X-Forwarded-User")
    )
    if email:
        return str(email)
    try:
        return str(sql_scalar("SELECT current_user()") or "unknown")
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
