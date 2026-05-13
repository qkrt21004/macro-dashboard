"""
Daily earnings data fetcher.

Reads tickers from data/tickers.csv, queries Finnhub per-symbol with rate
limiting (60/min free tier), writes results to data/earnings.json.

Designed to run via GitHub Actions cron (see .github/workflows/update_earnings.yml).
Requires FINNHUB_API_KEY environment variable.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import requests


# ── Configuration ─────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent.parent
TICKERS_CSV = REPO_ROOT / "data" / "tickers.csv"
OUTPUT_JSON = REPO_ROOT / "data" / "earnings.json"

WINDOW_PAST_DAYS   = 180
WINDOW_FUTURE_DAYS = 180
RATE_LIMIT_SLEEP   = 1.1   # seconds between calls → ~55 calls/min (under 60)

# Sector → color palette
SECTOR_COLOR = {
    "Financials":          "#4299E1",  # blue
    "Commodities":         "#F6AD55",  # orange
    "Tech":                "#B794F4",  # purple
    "Aerospace & Defense": "#FC8181",  # red
    "Consumer & Retail":   "#68D391",  # green
    "REITs":               "#4FD1C5",  # cyan
}
DEFAULT_COLOR = "#A0AEC0"  # gray fallback


def load_tickers() -> list[tuple[str, str, str]]:
    """Load (ticker, sector, name) tuples from CSV."""
    rows: list[tuple[str, str, str]] = []
    with open(TICKERS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = (row.get("Ticker") or "").strip()
            sector = (row.get("Sector") or "").strip()
            name   = (row.get("Company Name") or "").strip()
            if ticker:
                rows.append((ticker, sector, name))
    return rows


def format_timing(hour: str) -> str:
    """Map Finnhub 'hour' field to display label."""
    return {"bmo": "BMO", "amc": "AMC", "dmh": "DMH"}.get((hour or "").lower(), "")


def fetch_one(symbol: str, from_date: str, to_date: str, api_key: str) -> list:
    """Fetch earnings for a single symbol with 2-attempt retry."""
    url = "https://finnhub.io/api/v1/calendar/earnings"
    params = {"from": from_date, "to": to_date, "symbol": symbol, "token": api_key}

    for attempt in range(2):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 429:
                # Rate-limited — back off and retry once
                time.sleep(3)
                continue
            if r.status_code != 200:
                return []
            return r.json().get("earningsCalendar", []) or []
        except Exception as e:
            if attempt == 1:
                print(f"  ! {symbol}: {e}", file=sys.stderr)
                return []
            time.sleep(1)
    return []


def main() -> int:
    api_key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not api_key:
        print("ERROR: FINNHUB_API_KEY not set", file=sys.stderr)
        return 1

    tickers = load_tickers()
    today      = date.today()
    from_date  = (today - timedelta(days=WINDOW_PAST_DAYS)).isoformat()
    to_date    = (today + timedelta(days=WINDOW_FUTURE_DAYS)).isoformat()

    print(f"Fetching {len(tickers)} tickers · window: {from_date} → {to_date}")
    print(f"Rate limit: {RATE_LIMIT_SLEEP}s between calls "
          f"(~{int(60 / RATE_LIMIT_SLEEP)} calls/min)")

    events: list[dict] = []
    seen:   set        = set()
    succeeded = 0
    empty     = 0
    failed    = 0

    for i, (symbol, sector, name) in enumerate(tickers, 1):
        color = SECTOR_COLOR.get(sector, DEFAULT_COLOR)
        data  = fetch_one(symbol, from_date, to_date, api_key)

        if not data:
            empty += 1
        else:
            succeeded += 1

        for item in data:
            sym = (item.get("symbol") or "").upper()
            d   = item.get("date", "")
            if not d:
                continue
            key = (sym, d)
            if key in seen:
                continue
            seen.add(key)

            timing = format_timing(item.get("hour", ""))
            title  = f"{sym} · {timing}" if timing else sym

            events.append({
                "title":   title,
                "start":   d,
                "color":   color,
                "allDay":  True,
                "ticker":  sym,
                "sector":  sector,
                "name":    name,
                "timing":  timing,
            })

        if i % 20 == 0:
            print(f"  [{i:3}/{len(tickers)}]  succeeded:{succeeded}  empty:{empty}")

        time.sleep(RATE_LIMIT_SLEEP)

    failed = len(tickers) - succeeded - empty
    events.sort(key=lambda e: (e["start"], e["ticker"]))

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at":  today.isoformat(),
        "window_from":   from_date,
        "window_to":     to_date,
        "ticker_count":  len(tickers),
        "succeeded":     succeeded,
        "empty":         empty,
        "failed":        failed,
        "event_count":   len(events),
        "events":        events,
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ Wrote {len(events)} events to {OUTPUT_JSON.relative_to(REPO_ROOT)}")
    print(f"   Succeeded: {succeeded}/{len(tickers)}  ·  Empty: {empty}  ·  Failed: {failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
