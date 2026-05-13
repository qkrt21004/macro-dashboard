"""
Earnings Calendar — reads from data/earnings.json.

The JSON file is auto-refreshed daily via .github/workflows/update_earnings.yml,
which runs scripts/fetch_earnings.py against the Finnhub API.

This module loads the pre-fetched JSON instantly. No API calls happen at
app render time — the user always sees a fast page load.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).resolve().parent / "data" / "earnings.json"

# ── Sector → color palette (must match scripts/fetch_earnings.py) ─────────────
SECTOR_COLOR = {
    "Financials":          "#4299E1",  # blue
    "Commodities":         "#F6AD55",  # orange
    "Tech":                "#B794F4",  # purple
    "Aerospace & Defense": "#FC8181",  # red
    "Consumer & Retail":   "#68D391",  # green
    "REITs":               "#4FD1C5",  # cyan
}


@st.cache_data(ttl=600)
def load_earnings_payload() -> dict:
    """Load the cached earnings JSON. Returns empty payload if file missing."""
    if not DATA_PATH.exists():
        return {
            "generated_at": "",
            "ticker_count": 0,
            "event_count":  0,
            "events":       [],
        }
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "generated_at": "",
            "ticker_count": 0,
            "event_count":  0,
            "events":       [],
        }


def get_earnings_events() -> list:
    """Return list of FullCalendar-compatible event dicts."""
    payload = load_earnings_payload()
    # Strip extra fields (ticker/sector/name/timing) — FullCalendar ignores
    # unknown keys, but keep payload lean.
    events = []
    for e in payload.get("events", []):
        events.append({
            "title":  e.get("title", ""),
            "start":  e.get("start", ""),
            "color":  e.get("color", "#A0AEC0"),
            "allDay": True,
        })
    return events


def get_earnings_meta() -> dict:
    """Return metadata about the loaded payload."""
    payload = load_earnings_payload()
    return {
        "generated_at":  payload.get("generated_at", ""),
        "window_from":   payload.get("window_from", ""),
        "window_to":     payload.get("window_to", ""),
        "ticker_count":  payload.get("ticker_count", 0),
        "event_count":   payload.get("event_count", 0),
        "succeeded":     payload.get("succeeded", 0),
    }


# ── Legend metadata (for UI display) ─────────────────────────────────────────
EARNINGS_LEGEND = [
    ("Financials",          SECTOR_COLOR["Financials"]),
    ("Commodities",         SECTOR_COLOR["Commodities"]),
    ("Tech",                SECTOR_COLOR["Tech"]),
    ("Aerospace & Defense", SECTOR_COLOR["Aerospace & Defense"]),
    ("Consumer & Retail",   SECTOR_COLOR["Consumer & Retail"]),
    ("REITs",               SECTOR_COLOR["REITs"]),
]
