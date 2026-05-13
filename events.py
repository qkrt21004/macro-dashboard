"""
Macro Calendar events:
  - FOMC rate decision days (hardcoded, 2025-2026)
  - CPI release dates (FRED API)
  - US stock market holidays (NYSE, 2025-2026)
  - Quadruple Witching days (3rd Friday of Mar/Jun/Sep/Dec)
"""

import os
import requests
import streamlit as st
from datetime import date

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# ── Color palette ─────────────────────────────────────────────────────────────
C = {
    "fomc":     "#4299E1",   # blue
    "cpi":      "#B794F4",   # purple
    "holiday":  "#FC8181",   # red
    "witching": "#F6E05E",   # yellow
}

# ── FOMC Rate Decision days (final/announcement day of each meeting) ──────────
FOMC_EVENTS = [
    # 2025
    {"title": "FOMC Decision", "start": "2025-01-29", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2025-03-19", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2025-05-07", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2025-06-18", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2025-07-30", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2025-09-17", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2025-10-29", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2025-12-10", "color": C["fomc"]},
    # 2026
    {"title": "FOMC Decision", "start": "2026-01-28", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2026-03-18", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2026-04-29", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2026-06-10", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2026-07-29", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2026-09-16", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2026-10-28", "color": C["fomc"]},
    {"title": "FOMC Decision", "start": "2026-12-09", "color": C["fomc"]},
]

# ── US Stock Market Holidays (NYSE) ──────────────────────────────────────────
US_HOLIDAYS = [
    # 2025
    {"title": "Market Closed — New Year's Day",   "start": "2025-01-01", "color": C["holiday"]},
    {"title": "Market Closed — MLK Day",           "start": "2025-01-20", "color": C["holiday"]},
    {"title": "Market Closed — Presidents' Day",   "start": "2025-02-17", "color": C["holiday"]},
    {"title": "Market Closed — Good Friday",       "start": "2025-04-18", "color": C["holiday"]},
    {"title": "Market Closed — Memorial Day",      "start": "2025-05-26", "color": C["holiday"]},
    {"title": "Market Closed — Juneteenth",        "start": "2025-06-19", "color": C["holiday"]},
    {"title": "Market Closed — Independence Day",  "start": "2025-07-04", "color": C["holiday"]},
    {"title": "Market Closed — Labor Day",         "start": "2025-09-01", "color": C["holiday"]},
    {"title": "Market Closed — Thanksgiving",      "start": "2025-11-27", "color": C["holiday"]},
    {"title": "Market Closed — Christmas Day",     "start": "2025-12-25", "color": C["holiday"]},
    # 2026
    {"title": "Market Closed — New Year's Day",   "start": "2026-01-01", "color": C["holiday"]},
    {"title": "Market Closed — MLK Day",           "start": "2026-01-19", "color": C["holiday"]},
    {"title": "Market Closed — Presidents' Day",   "start": "2026-02-16", "color": C["holiday"]},
    {"title": "Market Closed — Good Friday",       "start": "2026-04-03", "color": C["holiday"]},
    {"title": "Market Closed — Memorial Day",      "start": "2026-05-25", "color": C["holiday"]},
    {"title": "Market Closed — Juneteenth",        "start": "2026-06-19", "color": C["holiday"]},
    {"title": "Market Closed — Independence Day",  "start": "2026-07-03", "color": C["holiday"]},  # observed (Jul 4 is Sat)
    {"title": "Market Closed — Labor Day",         "start": "2026-09-07", "color": C["holiday"]},
    {"title": "Market Closed — Thanksgiving",      "start": "2026-11-26", "color": C["holiday"]},
    {"title": "Market Closed — Christmas Day",     "start": "2026-12-25", "color": C["holiday"]},
]

# ── Quadruple Witching Days (3rd Friday of Mar / Jun / Sep / Dec) ─────────────
QUAD_WITCHING = [
    # 2025
    {"title": "Quad Witching", "start": "2025-03-21", "color": C["witching"]},
    {"title": "Quad Witching", "start": "2025-06-20", "color": C["witching"]},
    {"title": "Quad Witching", "start": "2025-09-19", "color": C["witching"]},
    {"title": "Quad Witching", "start": "2025-12-19", "color": C["witching"]},
    # 2026
    {"title": "Quad Witching", "start": "2026-03-20", "color": C["witching"]},
    {"title": "Quad Witching", "start": "2026-06-19", "color": C["witching"]},
    {"title": "Quad Witching", "start": "2026-09-18", "color": C["witching"]},
    {"title": "Quad Witching", "start": "2026-12-18", "color": C["witching"]},
]

# ── FRED CPI release ID ───────────────────────────────────────────────────────
RELEASE_IDS = {
    "CPI Release": {"id": 10, "color": C["cpi"]},
}


@st.cache_data(ttl=3600)
def fetch_fred_releases() -> list:
    """Fetch upcoming CPI release dates via FRED API."""
    if not FRED_API_KEY:
        return []
    today    = date.today().isoformat()
    end_date = f"{date.today().year + 1}-12-31"
    events   = []
    for name, info in RELEASE_IDS.items():
        try:
            r = requests.get(
                "https://api.stlouisfed.org/fred/release/dates",
                params={
                    "release_id":                         info["id"],
                    "api_key":                            FRED_API_KEY,
                    "realtime_start":                     today,
                    "realtime_end":                       end_date,
                    "include_release_dates_with_no_data": "true",
                    "file_type":                          "json",
                },
                timeout=15,
            )
            if r.status_code != 200:
                continue
            for item in r.json().get("release_dates", []):
                d = item.get("date", "")
                if d >= today:
                    events.append({
                        "title":  name,
                        "start":  d,
                        "color":  info["color"],
                        "allDay": True,
                    })
        except Exception:
            continue
    return events


def get_calendar_events() -> list:
    """Return all macro calendar events."""
    return FOMC_EVENTS + US_HOLIDAYS + QUAD_WITCHING + fetch_fred_releases()


# ── Legend metadata (for UI display) ─────────────────────────────────────────
LEGEND = [
    ("FOMC Decision",     C["fomc"]),
    ("CPI Release",       C["cpi"]),
    ("US Market Holiday", C["holiday"]),
    ("Quad Witching",     C["witching"]),
]
