"""
Earnings Calendar with Finnhub API integration.

Strategy:
  1. Fetch live earnings dates from Finnhub for tickers in TICKER_SECTOR.
  2. Apply sector-based color coding.
  3. Fall back to hardcoded HARDCODED_EVENTS if API fails or key missing.

The Finnhub free tier (60 calls/min) is more than sufficient — we make one
batched call per cache window (1 hour TTL).
"""

import os
import requests
import streamlit as st
from datetime import date, timedelta

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# ── Color palette by sector ────────────────────────────────────────────────────
SC = {
    "health":     "#68D391",   # green   — Health Care / Managed Care
    "ins_pc":     "#4299E1",   # blue    — P&C / Reinsurance
    "ins_life":   "#63B3ED",   # lt blue — Life & Health Insurance
    "fin_div":    "#2B6CB0",   # dk blue — Diversified Financials (BRK)
    "staples":    "#F6E05E",   # yellow  — Consumer Staples
    "machinery":  "#A0AEC0",   # gray    — Industrials / Machinery
    "airlines":   "#81E6D9",   # teal    — Industrials / Airlines
    "hotels":     "#F6AD55",   # orange  — Hotels & Lodging
    "casinos":    "#FC8181",   # red     — Casinos & Gaming
    "cruise":     "#4FD1C5",   # cyan    — Cruise Lines
    "ota":        "#B794F4",   # purple  — Online Travel
}

# ── Ticker → sector mapping (used by Finnhub fetch) ───────────────────────────
# Note: Foreign-exchange tickers (7181.T, LFC, PNGAY) may not appear in
# Finnhub's free US-only dataset; they're omitted to avoid clutter.
TICKER_SECTOR = {
    # Health Care
    "UNH":  "health",  "ELV": "health",  "HUM": "health",
    # P&C / Reinsurance
    "PGR":  "ins_pc",  "TRV": "ins_pc",  "CB":  "ins_pc",
    "ACGL": "ins_pc",  "RNR": "ins_pc",  "ALL": "ins_pc",
    "AIG":  "ins_pc",  "EG":  "ins_pc",
    # Life & Health Insurance
    "AFL":  "ins_life", "PRU": "ins_life", "MET": "ins_life",
    # Diversified Financials
    "BRK.B": "fin_div", "BRK-B": "fin_div",   # Finnhub sometimes uses dash form
    # Consumer Staples
    "CL":   "staples",
    # Machinery
    "CAT":  "machinery",
    # Airlines
    "DAL":  "airlines", "ALK": "airlines", "UAL": "airlines",
    "LUV":  "airlines", "AAL": "airlines",
    # Hotels & Lodging
    "HLT":  "hotels", "WH":  "hotels", "H":  "hotels", "MAR": "hotels",
    # Casinos & Gaming
    "LVS":  "casinos", "CZR": "casinos", "MGM": "casinos", "WYNN": "casinos",
    # Cruise Lines
    "CCL":  "cruise", "RCL": "cruise", "NCLH": "cruise",
    # Online Travel
    "BKNG": "ota", "TRIP": "ota", "ABNB": "ota", "EXPE": "ota", "TCOM": "ota",
}


def _format_timing(hour: str) -> str:
    """Convert Finnhub 'hour' field to display label."""
    mapping = {"bmo": "BMO", "amc": "AMC", "dmh": "DMH"}
    return mapping.get((hour or "").lower(), "")


@st.cache_data(ttl=3600)
def fetch_finnhub_earnings() -> list:
    """
    Fetch earnings calendar from Finnhub — per-symbol query approach.
    The bulk /calendar/earnings endpoint returns limited results on free tier,
    so we query each ticker individually with a 6-month forward / 6-month back
    window. Total ~30-35 API calls, well within the 60/min free tier limit.
    """
    if not FINNHUB_API_KEY:
        return []

    today     = date.today()
    from_date = (today - timedelta(days=180)).isoformat()
    to_date   = (today + timedelta(days=180)).isoformat()

    # De-dupe ticker list (skip BRK-B alias; query only canonical BRK.B)
    unique_tickers = [t for t in TICKER_SECTOR.keys() if t != "BRK-B"]

    events = []
    seen   = set()

    for symbol in unique_tickers:
        try:
            r = requests.get(
                "https://finnhub.io/api/v1/calendar/earnings",
                params={
                    "from":   from_date,
                    "to":     to_date,
                    "symbol": symbol,
                    "token":  FINNHUB_API_KEY,
                },
                timeout=15,
            )
            if r.status_code != 200:
                continue

            data = r.json().get("earningsCalendar", []) or []
            for item in data:
                sym = (item.get("symbol") or "").upper()
                d   = item.get("date", "")
                if not d:
                    continue

                key = (sym, d)
                if key in seen:
                    continue
                seen.add(key)

                sector_key = TICKER_SECTOR.get(sym) or TICKER_SECTOR.get(symbol)
                if not sector_key:
                    continue

                timing      = _format_timing(item.get("hour", ""))
                display_sym = "BRK.B" if sym in ("BRK.B", "BRK-B") else sym
                title       = f"{display_sym} · {timing}" if timing else display_sym

                events.append({
                    "title":  title,
                    "start":  d,
                    "color":  SC[sector_key],
                    "allDay": True,
                })
        except Exception:
            continue

    return events


# ── Fallback hardcoded events (used only if Finnhub API unavailable) ──────────
def _ev(ticker: str, date_str: str, timing: str, sector_key: str) -> dict:
    return {
        "title":  f"{ticker} · {timing}" if timing else ticker,
        "start":  date_str,
        "color":  SC[sector_key],
        "allDay": True,
    }


HARDCODED_EVENTS = [
    # Health Care
    _ev("UNH",   "2026-04-21", "BMO", "health"),
    _ev("ELV",   "2026-04-22", "BMO", "health"),
    _ev("HUM",   "2026-04-29", "BMO", "health"),
    # P&C / Reinsurance
    _ev("PGR",   "2026-04-15", "BMO", "ins_pc"),
    _ev("TRV",   "2026-04-16", "BMO", "ins_pc"),
    _ev("CB",    "2026-04-21", "AMC", "ins_pc"),
    _ev("ACGL",  "2026-04-28", "AMC", "ins_pc"),
    _ev("RNR",   "2026-04-28", "AMC", "ins_pc"),
    _ev("ALL",   "2026-04-29", "AMC", "ins_pc"),
    _ev("AIG",   "2026-04-30", "AMC", "ins_pc"),
    _ev("EG",    "2026-04-30", "AMC", "ins_pc"),
    # Life Insurance
    _ev("AFL",   "2026-04-29", "AMC", "ins_life"),
    _ev("PRU",   "2026-05-05", "AMC", "ins_life"),
    _ev("MET",   "2026-05-06", "BMO", "ins_life"),
    # Diversified Financials
    _ev("BRK.B", "2026-05-02", "BMO", "fin_div"),
    _ev("BRK.B", "2026-08-03", "BMO", "fin_div"),
    # Consumer Staples
    _ev("CL",    "2026-05-01", "BMO", "staples"),
    # Machinery
    _ev("CAT",   "2026-04-30", "BMO", "machinery"),
    # Airlines
    _ev("DAL",   "2026-04-08", "BMO", "airlines"),
    _ev("ALK",   "2026-04-20", "AMC", "airlines"),
    _ev("UAL",   "2026-04-22", "AMC", "airlines"),
    _ev("LUV",   "2026-04-22", "AMC", "airlines"),
    _ev("AAL",   "2026-04-23", "BMO", "airlines"),
    # Hotels
    _ev("HLT",   "2026-04-28", "BMO", "hotels"),
    _ev("WH",    "2026-04-29", "AMC", "hotels"),
    _ev("H",     "2026-04-30", "BMO", "hotels"),
    _ev("MAR",   "2026-05-06", "BMO", "hotels"),
    # Casinos
    _ev("LVS",   "2026-04-22", "AMC", "casinos"),
    _ev("CZR",   "2026-04-28", "AMC", "casinos"),
    _ev("MGM",   "2026-04-29", "AMC", "casinos"),
    _ev("WYNN",  "2026-05-06", "AMC", "casinos"),
    # Cruise Lines
    _ev("CCL",   "2026-03-27", "BMO", "cruise"),
    _ev("RCL",   "2026-04-30", "BMO", "cruise"),
    _ev("NCLH",  "2026-05-04", "BMO", "cruise"),
    # Online Travel
    _ev("BKNG",  "2026-04-28", "AMC", "ota"),
    _ev("TRIP",  "2026-05-06", "AMC", "ota"),
    _ev("ABNB",  "2026-05-07", "AMC", "ota"),
    _ev("EXPE",  "2026-05-07", "AMC", "ota"),
    _ev("TCOM",  "2026-05-25", "BMO", "ota"),
    _ev("BKNG",  "2026-08-05", "AMC", "ota"),
    _ev("EXPE",  "2026-08-06", "AMC", "ota"),
]


def get_earnings_events() -> list:
    """
    Return earnings events.
    Prefers live Finnhub data; falls back to HARDCODED_EVENTS if unavailable.
    """
    events = fetch_finnhub_earnings()
    if events:
        return events
    return HARDCODED_EVENTS


# ── Legend metadata (for UI display) ──────────────────────────────────────────
EARNINGS_LEGEND = [
    ("Health Care",        SC["health"]),
    ("Insurance — P&C",    SC["ins_pc"]),
    ("Insurance — Life",   SC["ins_life"]),
    ("Diversified Fin.",   SC["fin_div"]),
    ("Consumer Staples",   SC["staples"]),
    ("Machinery",          SC["machinery"]),
    ("Airlines",           SC["airlines"]),
    ("Hotels & Lodging",   SC["hotels"]),
    ("Casinos & Gaming",   SC["casinos"]),
    ("Cruise Lines",       SC["cruise"]),
    ("Online Travel",      SC["ota"]),
]
