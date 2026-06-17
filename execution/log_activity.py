"""
log_activity.py — Append a row to the Supabase agent_activity table.

Usage (from any execution script):
    from execution.log_activity import log_activity

    log_activity(
        agent_id="lead_gen",
        event_type="run_complete",
        message="Scraped 47 leads in Manchester",
        metrics={"leads_scraped": 47, "cost_gbp": 1.20},
        status="success"
    )

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in environment.
Fails silently so it never breaks the primary script.
"""

import os
import logging

import requests

logger = logging.getLogger("log_activity")


def log_activity(
    agent_id: str,
    event_type: str,
    message: str,
    metrics: dict = None,
    status: str = "success",
) -> None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        logger.warning(
            "[log_activity] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing — skipping"
        )
        return

    payload = {
        "agent_id": agent_id,
        "event_type": event_type,
        "message": message,
        "metrics": metrics or {},
        "status": status,
    }

    try:
        resp = requests.post(
            f"{url}/rest/v1/agent_activity",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=payload,
            timeout=5,
        )
        if resp.status_code >= 400:
            logger.warning(
                f"[log_activity] Supabase insert failed: {resp.status_code} {resp.text}"
            )
    except Exception as e:
        logger.warning(f"[log_activity] Failed silently: {e}")
