"""
Macro calendar events:
  - Central bank meeting dates (hardcoded, 2025-2026)
  - Key US data release dates (FRED API)
"""

import os
import requests
import streamlit as st
from datetime import date

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# ── Color palette ─────────────────────────────────────────────────────────────
C = {
    "fomc": "#4299E1",   # blue
    "boj":  "#F6AD55",   # orange
    "ecb":  "#68D391",   # green
    "cpi":  "#B794F4",   # purple
    "nfp":  "#F687B3",   # pink
    "gdp":  "#81E6D9",   # teal
    "pce":  "#F6E05E",   # yellow
}

# ── Central bank meetings (start inclusive, end exclusive for multi-day) ──────
CB_EVENTS = [
    # ══ FOMC ══
    # 2025
    {"title": "FOMC",        "start": "2025-01-28", "end": "2025-01-30", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2025-03-18", "end": "2025-03-20", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2025-05-06", "end": "2025-05-08", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2025-06-17", "end": "2025-06-19", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2025-07-29", "end": "2025-07-31", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2025-09-16", "end": "2025-09-18", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2025-10-28", "end": "2025-10-30", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2025-12-09", "end": "2025-12-11", "color": C["fomc"]},
    # 2026
    {"title": "FOMC",        "start": "2026-01-27", "end": "2026-01-29", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2026-03-17", "end": "2026-03-19", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2026-04-28", "end": "2026-04-30", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2026-06-09", "end": "2026-06-11", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2026-07-28", "end": "2026-07-30", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2026-09-15", "end": "2026-09-17", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2026-10-27", "end": "2026-10-29", "color": C["fomc"]},
    {"title": "FOMC",        "start": "2026-12-08", "end": "2026-12-10", "color": C["fomc"]},

    # ══ BOJ MPM ══
    # 2025
    {"title": "BOJ MPM",     "start": "2025-01-23", "end": "2025-01-25", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2025-03-18", "end": "2025-03-20", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2025-04-30", "end": "2025-05-02", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2025-06-16", "end": "2025-06-18", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2025-07-30", "end": "2025-08-01", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2025-09-18", "end": "2025-09-20", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2025-10-28", "end": "2025-10-30", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2025-12-18", "end": "2025-12-20", "color": C["boj"]},
    # 2026
    {"title": "BOJ MPM",     "start": "2026-01-22", "end": "2026-01-24", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2026-03-18", "end": "2026-03-20", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2026-04-30", "end": "2026-05-02", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2026-06-15", "end": "2026-06-17", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2026-07-29", "end": "2026-07-31", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2026-09-17", "end": "2026-09-19", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2026-10-28", "end": "2026-10-30", "color": C["boj"]},
    {"title": "BOJ MPM",     "start": "2026-12-17", "end": "2026-12-19", "color": C["boj"]},

    # ══ ECB ══
    # 2025
    {"title": "ECB Meeting", "start": "2025-01-30", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2025-03-06", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2025-04-17", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2025-06-05", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2025-07-24", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2025-09-11", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2025-10-30", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2025-12-18", "color": C["ecb"]},
    # 2026
    {"title": "ECB Meeting", "start": "2026-01-29", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2026-03-05", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2026-04-16", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2026-06-04", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2026-07-23", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2026-09-10", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2026-10-29", "color": C["ecb"]},
    {"title": "ECB Meeting", "start": "2026-12-17", "color": C["ecb"]},
]

# ── FRED data release IDs ──────────────────────────────────────────────────────
RELEASE_IDS = {
    "CPI":  {"id": 10,  "color": C["cpi"]},
    "NFP":  {"id": 50,  "color": C["nfp"]},
    "GDP":  {"id": 53,  "color": C["gdp"]},
    "PCE":  {"id": 54,  "color": C["pce"]},
}


@st.cache_data(ttl=3600)
def fetch_fred_releases() -> list:
    """Fetch upcoming FRED data release dates via API."""
    if not FRED_API_KEY:
        return []
    today     = date.today().isoformat()
    end_date  = f"{date.today().year + 1}-12-31"
    events    = []
    for name, info in RELEASE_IDS.items():
        try:
            r = requests.get(
                "https://api.stlouisfed.org/fred/release/dates",
                params={
                    "release_id":                       info["id"],
                    "api_key":                          FRED_API_KEY,
                    "realtime_start":                   today,
                    "realtime_end":                     end_date,
                    "include_release_dates_with_no_data": "true",
                    "file_type":                        "json",
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
    """Return all events: CB meetings + FRED data releases."""
    return CB_EVENTS + fetch_fred_releases()


# ── Legend metadata (for UI display) ─────────────────────────────────────────
LEGEND = [
    ("FOMC",        C["fomc"]),
    ("BOJ MPM",     C["boj"]),
    ("ECB Meeting", C["ecb"]),
    ("CPI Release", C["cpi"]),
    ("NFP Release", C["nfp"]),
    ("GDP Release", C["gdp"]),
    ("PCE Release", C["pce"]),
]
