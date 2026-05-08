import io
import os
import requests
import pandas as pd
import streamlit as st

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

FRED_SERIES = {
    "housing_starts": "HOUST",
    "cpi":            "CPIAUCSL",
    "us10y":          "DGS10",
    "wti":            "DCOILWTICO",
    "fed_rate":        "FEDFUNDS",
    "fed_assets":      "WALCL",
    "fed_treasuries":  "TREAST",
    "fed_mbs":         "WSHOMCB",
    "us_m2":           "M2SL",
    "boj_assets":      "JPNASSETS",
}


@st.cache_data(ttl=3600)
def fetch_fred(series_id: str) -> pd.DataFrame:
    if not FRED_API_KEY:
        return pd.DataFrame()
    r = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"},
        timeout=10,
    )
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("observations", []))
    df = df[df["value"] != "."].copy()
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = df["value"].astype(float)
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def fetch_yahoo(ticker: str, interval: str = "1wk", range_: str = "max") -> pd.DataFrame:
    r = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
        params={"interval": interval, "range": range_},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    r.raise_for_status()
    result = r.json()["chart"]["result"][0]
    df = pd.DataFrame({
        "date":  pd.to_datetime(result["timestamp"], unit="s"),
        "value": result["indicators"]["quote"][0]["close"],
    }).dropna()
    return df.reset_index(drop=True)


BOJ_API = "https://www.stat-search.boj.or.jp/api/v1"

BOJ_SERIES = {
    # db,         code,            freq
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
    r = requests.get(
        f"{BOJ_API}/getDataCode",
        params={"format": "json", "lang": "en", "db": db, "code": code},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    r.raise_for_status()
    resultset = r.json().get("RESULTSET", [])
    if not resultset or not resultset[0].get("VALUES"):
        return pd.DataFrame()

    vals = resultset[0]["VALUES"]
    dates_raw = vals["SURVEY_DATES"]
    values    = vals["VALUES"]

    if freq == "D":
        dates = pd.to_datetime([str(d) for d in dates_raw], format="%Y%m%d")
    else:
        dates = pd.to_datetime([str(d) + "01" for d in dates_raw], format="%Y%m%d")

    df = pd.DataFrame({"date": dates, "value": values}).dropna()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=86400)  # 하루 1회 갱신 (월별 데이터)
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
    # 날짜를 월 시작일로 정규화
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


def load_all() -> dict:
    df_cpi = fetch_fred(FRED_SERIES["cpi"])

    df_cpi_yoy = df_cpi.copy()
    df_cpi_yoy["value"] = df_cpi_yoy["value"].pct_change(12) * 100
    df_cpi_yoy = df_cpi_yoy.dropna().reset_index(drop=True)

    fx_tickers = {"dxy": "DX-Y.NYB", "eurusd": "EURUSD=X", "usdjpy": "JPY=X", "usdmxn": "MXN=X"}

    result = {
        "housing":    fetch_fred(FRED_SERIES["housing_starts"]),
        "cpi_yoy":    df_cpi_yoy,
        "us10y":      fetch_fred(FRED_SERIES["us10y"]),
        "wti":        fetch_fred(FRED_SERIES["wti"]),
        "cape":       fetch_cape(),
        "fed_rate":   fetch_fred(FRED_SERIES["fed_rate"]),
        "fed_assets":     fetch_fred(FRED_SERIES["fed_assets"]),
        "fed_treasuries": fetch_fred(FRED_SERIES["fed_treasuries"]),
        "fed_mbs":        fetch_fred(FRED_SERIES["fed_mbs"]),
        "us_m2":      fetch_fred(FRED_SERIES["us_m2"]),
        # BOJ 공식 API
        "boj_monetary_base": fetch_boj("boj_monetary_base"),
        "boj_m2":            fetch_boj("boj_m2"),
        "boj_total_assets":  fetch_boj("boj_total_assets"),
        "boj_jgb":           fetch_boj("boj_jgb"),
        "boj_etf":           fetch_boj("boj_etf"),
        "boj_call_rate":     fetch_boj("boj_call_rate"),
        "boj_policy_rate":   fetch_boj("boj_policy_rate"),
    }

    # 주봉 (전체 기간용) + 일봉 (1년 이내용)
    for key, ticker in fx_tickers.items():
        result[key]            = fetch_yahoo(ticker, interval="1wk", range_="max")
        result[f"{key}_daily"] = fetch_yahoo(ticker, interval="1d",  range_="2y")

    return result
