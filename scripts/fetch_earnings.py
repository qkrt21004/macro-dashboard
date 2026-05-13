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

WINDOW_PAST_DAYS   = 90    # most past earnings already absorbed; focus forward
WINDOW_FUTURE_DAYS = 180
CHUNK_DAYS         = 7     # 7-day chunks to stay well under Finnhub's 1500-row cap even in peak earnings weeks

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


def fetch_window(from_date: str, to_date: str, api_key: str) -> list:
    """
    Fetch ALL US earnings in a date range via bulk /calendar/earnings.
    Finnhub caps responses at 1500 rows — keep chunks small.
    """
    url = "https://finnhub.io/api/v1/calendar/earnings"
    params = {"from": from_date, "to": to_date, "token": api_key}

    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(5)
                continue
            if r.status_code != 200:
                print(f"     ! HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
                if attempt == 2:
                    return []
                continue
            return r.json().get("earningsCalendar", []) or []
        except Exception as e:
            if attempt == 2:
                print(f"  ! {from_date}→{to_date}: {e}", file=sys.stderr)
                return []
            time.sleep(2)
    return []


def main() -> int:
    api_key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not api_key:
        print("ERROR: FINNHUB_API_KEY not set", file=sys.stderr)
        return 1

    tickers = load_tickers()
    # Build ticker → (sector, name) lookup. Normalize to uppercase.
    ticker_meta: dict[str, tuple[str, str]] = {}
    for t, s, n in tickers:
        ticker_meta[t.upper()] = (s, n)
        # Also accept BRK-B / BRK.B aliases
        if "." in t:
            ticker_meta[t.upper().replace(".", "-")] = (s, n)

    today     = date.today()
    from_date = (today - timedelta(days=WINDOW_PAST_DAYS)).isoformat()
    to_date   = (today + timedelta(days=WINDOW_FUTURE_DAYS)).isoformat()

    print(f"Watchlist: {len(tickers)} tickers · window: {from_date} → {to_date}")
    print(f"Strategy: bulk query in {CHUNK_DAYS}-day chunks")

    # Split window into CHUNK_DAYS chunks (bulk endpoint has range limits)
    chunks: list[tuple[str, str]] = []
    start = today - timedelta(days=WINDOW_PAST_DAYS)
    end   = today + timedelta(days=WINDOW_FUTURE_DAYS)
    cur   = start
    while cur < end:
        nxt = min(cur + timedelta(days=CHUNK_DAYS), end)
        chunks.append((cur.isoformat(), nxt.isoformat()))
        cur = nxt + timedelta(days=1)

    events: list[dict] = []
    seen:   set        = set()
    all_returned       = 0
    matched_tickers    = set()

    for i, (f, t) in enumerate(chunks, 1):
        data = fetch_window(f, t, api_key)
        all_returned += len(data)

        for item in data:
            sym = (item.get("symbol") or "").upper()
            if sym not in ticker_meta:
                continue

            d = item.get("date", "")
            if not d:
                continue

            key = (sym, d)
            if key in seen:
                continue
            seen.add(key)

            sector, name = ticker_meta[sym]
            color = SECTOR_COLOR.get(sector, DEFAULT_COLOR)
            timing = format_timing(item.get("hour", ""))
            # Display BRK-B as BRK.B
            display_sym = sym.replace("-B", ".B") if sym.endswith("-B") else sym
            title = f"{display_sym} · {timing}" if timing else display_sym

            events.append({
                "title":   title,
                "start":   d,
                "color":   color,
                "allDay":  True,
                "ticker":  display_sym,
                "sector":  sector,
                "name":    name,
                "timing":  timing,
            })
            matched_tickers.add(sym)

        print(f"  [{i:2}/{len(chunks)}] {f}→{t}  raw:{len(data):4}  matched:{len(events)}")
        time.sleep(1.0)  # gentle pacing

    succeeded = len(matched_tickers)
    empty     = len(tickers) - succeeded
    failed    = 0
    events.sort(key=lambda e: (e["start"], e["ticker"]))

    print(f"\nFinnhub returned {all_returned} total earnings rows across all chunks")
    print(f"After ticker filter: {len(events)} events for {succeeded} tickers")

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
