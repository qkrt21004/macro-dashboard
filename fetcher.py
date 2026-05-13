import os
import requests
import pandas as pd
import streamlit as st

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

FRED_SERIES = {
    # Economic
    "housing_starts": "HOUST",
    "cpi":            "CPIAUCSL",
    "wti":            "DCOILWTICO",
    # Yields
    "us2y":           "DGS2",
    "us10y":          "DGS10",
    "jgb10y":         "IRLTLT01JPM156N",   # Japan 10Y (monthly, OECD)
    "hy_spread":      "BAMLH0A0HYM2",      # ICE BofA HY OAS
    # Fed policy & balance sheet
    "fed_rate":       "FEDFUNDS",
    "fed_assets":     "WALCL",
    "fed_treasuries": "TREAST",
    "fed_mbs":        "WSHOMCB",
    # Liquidity
    "us_m2":          "M2SL",
    # BOJ (FRED proxy)
    "boj_assets":     "JPNASSETS",
}


@st.cache_data(ttl=3600)
def fetch_fred(series_id: str) -> pd.DataFrame:
    if not FRED_API_KEY:
        return pd.DataFrame()
    for attempt in range(3):  # 최대 3회 시도
        try:
            r = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"},
                timeout=30,
            )
            r.raise_for_status()
            df = pd.DataFrame(r.json().get("observations", []))
            if df.empty:
                return pd.DataFrame()
            df = df[df["value"] != "."].copy()
            df["date"]  = pd.to_datetime(df["date"])
            df["value"] = df["value"].astype(float)
            return df.sort_values("date").reset_index(drop=True)
        except Exception:
            if attempt == 2:
                return pd.DataFrame()
            continue
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_yahoo(ticker: str, interval: str = "1wk", range_: str = "max") -> pd.DataFrame:
    # Try both Yahoo Finance endpoints in case one is blocked
    urls = [
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}",
    ]
    for url in urls:
        try:
            r = requests.get(
                url,
                params={"interval": interval, "range": range_},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            if r.status_code != 200:
                continue
            payload = r.json()
            result  = payload.get("chart", {}).get("result")
            if not result:
                continue
            df = pd.DataFrame({
                "date":  pd.to_datetime(result[0]["timestamp"], unit="s"),
                "value": result[0]["indicators"]["quote"][0]["close"],
            }).dropna()
            return df.reset_index(drop=True)
        except Exception:
            continue
    return pd.DataFrame()


BOJ_API = "https://www.stat-search.boj.or.jp/api/v1"

BOJ_SERIES = {
    "boj_monetary_base": ("MD01", "MABS1AN11",    "M"),
    "boj_m2":            ("MD02", "MAM1NAM2M2MO", "M"),
    "boj_jgb":           ("BS01", "MABJMA5B",     "M"),
    "boj_total_assets":  ("BS01", "MABJMTA",      "M"),
    "boj_etf":           ("BS01", "MABJMA003",    "M"),
    "boj_call_rate":     ("FM01", "STRDCLUCON",   "D"),
    "boj_policy_rate":   ("IR01", "MADR1Z@D",     "D"),
}


@st.cache_data(ttl=86400)
def fetch_boj(key: str) -> pd.DataFrame:
    db, code, freq = BOJ_SERIES[key]
    for attempt in range(3):
        try:
            r = requests.get(
                f"{BOJ_API}/getDataCode",
                params={"format": "json", "lang": "en", "db": db, "code": code},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            r.raise_for_status()
            resultset = r.json().get("RESULTSET", [])
            if not resultset or not resultset[0].get("VALUES"):
                return pd.DataFrame()

            vals      = resultset[0]["VALUES"]
            dates_raw = vals["SURVEY_DATES"]
            values    = vals["VALUES"]

            if freq == "D":
                dates = pd.to_datetime([str(d) for d in dates_raw], format="%Y%m%d")
            else:
                dates = pd.to_datetime([str(d) + "01" for d in dates_raw], format="%Y%m%d")

            df = pd.DataFrame({"date": dates, "value": values}).dropna()
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            return df.dropna().sort_values("date").reset_index(drop=True)
        except Exception:
            if attempt == 2:
                return pd.DataFrame()
            continue
    return pd.DataFrame()


@st.cache_data(ttl=86400)
def fetch_cape() -> pd.DataFrame:
    import re
    r = requests.get(
        "https://www.multpl.com/shiller-pe/table/by-month",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    r.raise_for_status()
    rows = re.findall(r"<tr[^>]*>.*?</tr>", r.text, re.DOTALL)
    records = []
    for row in rows[1:]:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        cleaned = [re.sub(r"<[^>]+>|&#x2002;", "", c).strip() for c in cells]
        if len(cleaned) >= 2 and cleaned[0] and cleaned[1]:
            try:
                records.append({
                    "date":  pd.to_datetime(cleaned[0]),
                    "value": float(cleaned[1]),
                })
            except Exception:
                pass
    df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


def load_all() -> dict:
    # ── CPI YoY ───────────────────────────────────────────────────────────────
    df_cpi = fetch_fred(FRED_SERIES["cpi"])
    if not df_cpi.empty and "value" in df_cpi.columns:
        df_cpi_yoy = df_cpi.copy()
        df_cpi_yoy["value"] = df_cpi_yoy["value"].pct_change(12) * 100
        df_cpi_yoy = df_cpi_yoy.dropna().reset_index(drop=True)
    else:
        df_cpi_yoy = pd.DataFrame()

    # ── 2Y-10Y Yield Spread ───────────────────────────────────────────────────
    df_us2y  = fetch_fred(FRED_SERIES["us2y"])
    df_us10y = fetch_fred(FRED_SERIES["us10y"])
    if not df_us2y.empty and not df_us10y.empty:
        merged_y = pd.merge(
            df_us10y.rename(columns={"value": "us10y"}),
            df_us2y.rename(columns={"value": "us2y"}),
            on="date", how="inner",
        )
        df_spread = merged_y.copy()
        df_spread["value"] = merged_y["us10y"] - merged_y["us2y"]
        df_spread = df_spread[["date", "value"]].sort_values("date").reset_index(drop=True)
    else:
        df_spread = pd.DataFrame()

    result = {
        # Economic
        "housing":    fetch_fred(FRED_SERIES["housing_starts"]),
        "cpi_yoy":    df_cpi_yoy,
        "wti":        fetch_fred(FRED_SERIES["wti"]),
        "cape":       fetch_cape(),
        # Yields
        "us2y":       df_us2y,
        "us10y":      df_us10y,
        "spread_2y10y": df_spread,
        "jgb10y":     fetch_fred(FRED_SERIES["jgb10y"]),
        "hy_spread":  fetch_fred(FRED_SERIES["hy_spread"]),
        # Fed policy & balance sheet
        "fed_rate":       fetch_fred(FRED_SERIES["fed_rate"]),
        "fed_assets":     fetch_fred(FRED_SERIES["fed_assets"]),
        "fed_treasuries": fetch_fred(FRED_SERIES["fed_treasuries"]),
        "fed_mbs":        fetch_fred(FRED_SERIES["fed_mbs"]),
        # Liquidity
        "us_m2":       fetch_fred(FRED_SERIES["us_m2"]),
        # BOJ
        "boj_monetary_base": fetch_boj("boj_monetary_base"),
        "boj_m2":            fetch_boj("boj_m2"),
        "boj_total_assets":  fetch_boj("boj_total_assets"),
        "boj_jgb":           fetch_boj("boj_jgb"),
        "boj_etf":           fetch_boj("boj_etf"),
        "boj_call_rate":     fetch_boj("boj_call_rate"),
        "boj_policy_rate":   fetch_boj("boj_policy_rate"),
    }

    # ── Yahoo Finance: weekly (all history) + daily (2Y) ─────────────────────
    yahoo_tickers = {
        # FX
        "dxy":    "DX-Y.NYB",
        "eurusd": "EURUSD=X",
        "usdjpy": "JPY=X",
        "usdmxn": "MXN=X",
        # Equities & commodities
        "sp500":  "^GSPC",
        "nikkei": "^N225",
        "gold":   "GC=F",
        "vix":    "^VIX",
    }
    for key, ticker in yahoo_tickers.items():
        try:
            result[key] = fetch_yahoo(ticker, interval="1wk", range_="max")
        except Exception:
            result[key] = pd.DataFrame()
        try:
            result[f"{key}_daily"] = fetch_yahoo(ticker, interval="1d", range_="2y")
        except Exception:
            result[f"{key}_daily"] = pd.DataFrame()

    return result
