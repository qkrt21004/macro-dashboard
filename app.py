import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from fetcher import load_all
from charts import (
    make_line_chart,
    make_fx_chart,
    make_comparison_chart,
    make_fed_balance_sheet_chart,
)

st.set_page_config(
    page_title="Macro Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stMetric label { font-size: 0.85rem; color: #888; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stHorizontalBlock"] .stRadio label { font-size: 0.78rem; }

    @media (max-width: 640px) {
        .block-container { padding: 1rem 0.75rem !important; }
        [data-testid="stMetric"] { padding: 0.4rem !important; }
        [data-testid="metric-container"] label { font-size: 0.65rem !important; }
        [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1rem !important; }
        [data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 0.65rem !important; }
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
            min-width: 100% !important; flex: 1 1 100% !important;
        }
        [data-testid="stRadio"] > div {
            flex-wrap: nowrap !important; overflow-x: auto !important;
            -webkit-overflow-scrolling: touch; padding-bottom: 4px;
        }
        [data-testid="stRadio"] label { font-size: 0.7rem !important; white-space: nowrap; }
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.1rem !important; }
        h3 { font-size: 1rem !important; }
        [data-testid="stMultiSelect"] { font-size: 0.8rem !important; }
        [data-testid="stPlotlyChart"] { margin-bottom: 0.5rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ── Period config ─────────────────────────────────────────────────────────────

PERIODS = {
    "All": None,
    "10Y": 365 * 10,
    "5Y":  365 * 5,
    "1Y":  365,
    "6M":  183,
    "1M":  30,
}
SHORT_PERIOD_DAYS = 365


def filter_period(df: pd.DataFrame, days: int | None) -> pd.DataFrame:
    if df.empty or days is None:
        return df
    cutoff = pd.Timestamp(datetime.now() - timedelta(days=days))
    return df[df["date"] >= cutoff].reset_index(drop=True)


def pick_series(data: dict, key: str, days: int | None) -> pd.DataFrame:
    """Use daily data for ≤1Y periods, weekly otherwise."""
    use_daily = days is not None and days <= SHORT_PERIOD_DAYS
    df = data.get(f"{key}_daily", data[key]) if use_daily else data[key]
    return filter_period(df, days)


def get_latest(df: pd.DataFrame):
    if df.empty or len(df) < 2:
        return None, None
    return df.iloc[-1]["value"], df.iloc[-1]["value"] - df.iloc[-2]["value"]


def period_selector(key: str) -> tuple[str, int | None]:
    label = st.radio(
        "Period", options=list(PERIODS.keys()), index=0,
        horizontal=True, label_visibility="collapsed", key=key,
    )
    return label, PERIODS[label]


def chart_row(specs: list, data: dict, days: int | None):
    """Render a row of charts from a list of (df, title, color_key, unit, kwargs) specs."""
    cols = st.columns(len(specs))
    for col, spec in zip(cols, specs):
        df, title, ckey, unit = spec[:4]
        kwargs = spec[4] if len(spec) > 4 else {}
        with col:
            st.plotly_chart(
                make_line_chart(df, title, ckey, unit, **kwargs),
                use_container_width=True,
            )


# ── Load data ─────────────────────────────────────────────────────────────────

with st.spinner("Loading data..."):
    data = load_all()

# ── Header ────────────────────────────────────────────────────────────────────

st.title("Macro Dashboard")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Sources: FRED · Yahoo Finance · BOJ")
st.divider()

# ── Summary Metric Cards ──────────────────────────────────────────────────────

fed_v,    fed_d    = get_latest(data["fed_rate"])
boj_v,    boj_d    = get_latest(data["boj_policy_rate"])
us10y_v,  us10y_d  = get_latest(data["us10y"])
sprd_v,   sprd_d   = get_latest(data["spread_2y10y"])
dxy_v,    dxy_d    = get_latest(data["dxy"])
vix_v,    vix_d    = get_latest(data["vix"])

m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1:
    if fed_v:   st.metric("Fed Funds Rate",    f"{fed_v:.2f}%",   f"{fed_d:+.2f}pp")
with m2:
    if boj_v:   st.metric("BOJ Policy Rate",   f"{boj_v:.2f}%",   f"{boj_d:+.2f}pp")
with m3:
    if us10y_v: st.metric("US 10Y Yield",       f"{us10y_v:.3f}%", f"{us10y_d:+.3f}pp")
with m4:
    if sprd_v is not None:
        st.metric("2Y–10Y Spread", f"{sprd_v:+.2f}%", f"{sprd_d:+.2f}pp")
with m5:
    if dxy_v:   st.metric("DXY",               f"{dxy_v:.2f}",    f"{dxy_d:+.2f}")
with m6:
    if vix_v:   st.metric("VIX",               f"{vix_v:.2f}",    f"{vix_d:+.2f}")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 1. CENTRAL BANK POLICY
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("1 · Central Bank Policy")

# Row: Fed rate | BOJ policy rate
r1a, r1b = st.columns(2)
with r1a:
    _, d = period_selector("fed_rate_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["fed_rate"], d), "Fed Funds Rate (%)", "fed_rate", "%"),
        use_container_width=True,
    )
    st.caption("Source: Federal Reserve via FRED (FEDFUNDS)")

with r1b:
    _, d = period_selector("boj_rate_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_policy_rate"], d), "BOJ Policy Rate (%)", "boj_policy_rate", "%"),
        use_container_width=True,
    )
    st.caption("Source: Bank of Japan Official API — IR01/MADR1Z@D")

# Row: Fed QE/QT | BOJ call rate (overnight liquidity)
r1c, r1d = st.columns(2)
with r1c:
    _, d = period_selector("fed_assets_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["fed_assets"], d), "Fed Total Assets — QE / QT (Million USD)", "fed_assets", "M"),
        use_container_width=True,
    )
    st.caption("Source: Federal Reserve via FRED (WALCL)")

with r1d:
    _, d = period_selector("boj_call_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_call_rate"], d), "BOJ Uncollateralized Overnight Call Rate (%)", "boj_call_rate", "%"),
        use_container_width=True,
    )
    st.caption("Source: Bank of Japan Official API — FM01/STRDCLUCON")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 2. CENTRAL BANK BALANCE SHEETS
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("2 · Central Bank Balance Sheets")

# Fed: Treasuries + MBS breakdown (full width)
_, d = period_selector("fed_bs_p")
st.plotly_chart(
    make_fed_balance_sheet_chart(
        filter_period(data["fed_treasuries"], d),
        filter_period(data["fed_mbs"], d),
        _,
    ),
    use_container_width=True,
)
st.caption("Source: Federal Reserve via FRED — Treasuries (TREAST), MBS (WSHOMCB)")

# BOJ: total assets | JGB | ETF | monetary base
r2a, r2b = st.columns(2)
with r2a:
    _, d = period_selector("boj_ta_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_total_assets"], d), "BOJ Total Assets (100M JPY)", "boj_total_assets", "¥"),
        use_container_width=True,
    )
    st.caption("Source: Bank of Japan Official API — BS01/MABJMTA")

with r2b:
    _, d = period_selector("boj_jgb_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_jgb"], d), "BOJ JGB Holdings (100M JPY)", "boj_jgb", "¥"),
        use_container_width=True,
    )
    st.caption("Source: Bank of Japan Official API — BS01/MABJMA5B")

r2c, r2d = st.columns(2)
with r2c:
    _, d = period_selector("boj_etf_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_etf"], d), "BOJ ETF Holdings (100M JPY)", "boj_etf", "¥"),
        use_container_width=True,
    )
    st.caption("Source: Bank of Japan Official API — BS01/MABJMA003")

with r2d:
    _, d = period_selector("boj_mb_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_monetary_base"], d), "BOJ Monetary Base (100M JPY)", "boj_monetary_base", "¥"),
        use_container_width=True,
    )
    st.caption("Source: Bank of Japan Official API — MD01/MABS1AN11")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 3. SYSTEM LIQUIDITY & MONEY SUPPLY
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("3 · System Liquidity & Money Supply")

r3a, r3b = st.columns(2)
with r3a:
    _, d = period_selector("us_m2_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["us_m2"], d), "US M2 Money Supply (Billion USD)", "us_m2", "B"),
        use_container_width=True,
    )
    st.caption("Source: Federal Reserve via FRED (M2SL)")

with r3b:
    _, d = period_selector("boj_m2_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_m2"], d), "Japan M2 Money Supply (100M JPY)", "boj_m2", "¥"),
        use_container_width=True,
    )
    st.caption("Source: Bank of Japan Official API — MD02/MAM1NAM2M2MO")

r3c, r3d = st.columns(2)
with r3c:
    _, d = period_selector("rrp_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["rrp"], d), "Fed Overnight RRP (Billion USD)", "rrp", "B"),
        use_container_width=True,
    )
    st.caption("Source: Federal Reserve via FRED (RRPONTSYD)")

with r3d:
    _, d = period_selector("tga_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["tga"], d), "Treasury General Account — TGA (Billion USD)", "tga", "B"),
        use_container_width=True,
    )
    st.caption("Source: Federal Reserve via FRED (WTREGEN)")

_, d = period_selector("bank_credit_p")
st.plotly_chart(
    make_line_chart(filter_period(data["bank_credit"], d), "US Total Bank Credit (Billion USD)", "bank_credit", "B"),
    use_container_width=True,
)
st.caption("Source: Federal Reserve via FRED (TOTBKCR)")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 4. BOND MARKET & YIELD CURVE
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("4 · Bond Market & Yield Curve")

r4a, r4b = st.columns(2)
with r4a:
    _, d = period_selector("us2y_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["us2y"], d), "US 2Y Treasury Yield (%)", "us2y", "%"),
        use_container_width=True,
    )
    st.caption("Source: U.S. Treasury via FRED (DGS2)")

with r4b:
    _, d = period_selector("us10y_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["us10y"], d), "US 10Y Treasury Yield (%)", "us10y", "%"),
        use_container_width=True,
    )
    st.caption("Source: U.S. Treasury via FRED (DGS10)")

r4c, r4d = st.columns(2)
with r4c:
    _, d = period_selector("spread_p")
    st.plotly_chart(
        make_line_chart(
            filter_period(data["spread_2y10y"], d),
            "2Y–10Y Yield Spread (%)", "spread_2y10y", "%",
            zero_line=True, area=False,
        ),
        use_container_width=True,
    )
    st.caption("Source: Computed from FRED DGS10 − DGS2 · Negative = inverted curve")

with r4d:
    _, d = period_selector("jgb10y_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["jgb10y"], d), "JGB 10Y Yield — YCC Indicator (%)", "jgb10y", "%"),
        use_container_width=True,
    )
    st.caption("Source: OECD via FRED (IRLTLT01JPM156N) · Monthly · BOJ YCC target band shown as context")

_, d = period_selector("hy_spread_p")
st.plotly_chart(
    make_line_chart(filter_period(data["hy_spread"], d), "US HY Credit Spread — OAS (%)", "hy_spread", "%"),
    use_container_width=True,
)
st.caption("Source: ICE BofA via FRED (BAMLH0A0HYM2) · Higher = wider credit risk premium")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 5. FX & RISK ASSETS
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("5 · FX & Risk Assets")

# FX comparison (normalized %)
eurusd_v, eurusd_d = get_latest(data["eurusd"])
usdjpy_v, usdjpy_d = get_latest(data["usdjpy"])
usdmxn_v, usdmxn_d = get_latest(data["usdmxn"])

fx_m1, fx_m2, fx_m3, fx_m4 = st.columns(4)
with fx_m1:
    if dxy_v:    st.metric("DXY",     f"{dxy_v:.2f}",    f"{dxy_d:+.2f}")
with fx_m2:
    if eurusd_v: st.metric("EUR/USD", f"{eurusd_v:.4f}", f"{eurusd_d:+.4f}")
with fx_m3:
    if usdjpy_v: st.metric("USD/JPY", f"{usdjpy_v:.2f}", f"{usdjpy_d:+.2f}")
with fx_m4:
    if usdmxn_v: st.metric("USD/MXN", f"{usdmxn_v:.4f}", f"{usdmxn_d:+.4f}")

fx_label, fx_days = period_selector("fx_p")
st.plotly_chart(make_fx_chart({
    "DXY":     pick_series(data, "dxy",    fx_days),
    "EUR/USD": pick_series(data, "eurusd", fx_days),
    "USD/JPY": pick_series(data, "usdjpy", fx_days),
    "USD/MXN": pick_series(data, "usdmxn", fx_days),
}, fx_label), use_container_width=True)
st.caption("Source: Yahoo Finance — DXY (ICE), FX pairs (spot market)")

# Equities, Gold, VIX
sp500_v,  sp500_d  = get_latest(data["sp500"])
nikkei_v, nikkei_d = get_latest(data["nikkei"])
gold_v,   gold_d   = get_latest(data["gold"])

eq_m1, eq_m2, eq_m3, eq_m4 = st.columns(4)
with eq_m1:
    if sp500_v:  st.metric("S&P 500",  f"{sp500_v:,.0f}",  f"{sp500_d:+.0f}")
with eq_m2:
    if nikkei_v: st.metric("Nikkei",   f"{nikkei_v:,.0f}", f"{nikkei_d:+.0f}")
with eq_m3:
    if gold_v:   st.metric("Gold ($/oz)", f"${gold_v:,.0f}", f"{gold_d:+.0f}")
with eq_m4:
    if vix_v:    st.metric("VIX",      f"{vix_v:.2f}",     f"{vix_d:+.2f}")

r5a, r5b = st.columns(2)
with r5a:
    _, d = period_selector("sp500_p")
    st.plotly_chart(
        make_line_chart(pick_series(data, "sp500", d), "S&P 500", "sp500", ""),
        use_container_width=True,
    )
    st.caption("Source: Yahoo Finance (^GSPC)")

with r5b:
    _, d = period_selector("nikkei_p")
    st.plotly_chart(
        make_line_chart(pick_series(data, "nikkei", d), "Nikkei 225", "nikkei", ""),
        use_container_width=True,
    )
    st.caption("Source: Yahoo Finance (^N225)")

r5c, r5d = st.columns(2)
with r5c:
    _, d = period_selector("gold_p")
    st.plotly_chart(
        make_line_chart(pick_series(data, "gold", d), "Gold (USD/oz)", "gold", "$"),
        use_container_width=True,
    )
    st.caption("Source: Yahoo Finance (GC=F — Gold Futures front month)")

with r5d:
    _, d = period_selector("vix_p")
    st.plotly_chart(
        make_line_chart(pick_series(data, "vix", d), "VIX — Volatility Index", "vix", "", area=False),
        use_container_width=True,
    )
    st.caption("Source: CBOE via Yahoo Finance (^VIX)")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 6. ECONOMIC INDICATORS
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("6 · Economic Indicators")

r6a, r6b = st.columns(2)
with r6a:
    _, d = period_selector("cpi_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["cpi_yoy"], d), "CPI — Year-over-Year (%)", "cpi", "%"),
        use_container_width=True,
    )
    st.caption("Source: U.S. Bureau of Labor Statistics via FRED (CPIAUCSL)")

with r6b:
    _, d = period_selector("wti_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["wti"], d), "WTI Crude Oil ($/bbl)", "wti", "$"),
        use_container_width=True,
    )
    st.caption("Source: U.S. EIA via FRED (DCOILWTICO)")

r6c, r6d = st.columns(2)
with r6c:
    _, d = period_selector("housing_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["housing"], d), "Housing Starts (K units)", "housing", "K"),
        use_container_width=True,
    )
    st.caption("Source: U.S. Census Bureau via FRED (HOUST)")

with r6d:
    _, d = period_selector("cape_p")
    st.plotly_chart(
        make_line_chart(filter_period(data["cape"], d), "CAPE Ratio (Shiller PE)", "cape", ""),
        use_container_width=True,
    )
    st.caption("Source: Robert Shiller / multpl.com — Since 1871, monthly updates")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# INDICATOR COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("Indicator Comparison")

ALL_INDICATORS = {
    # Section 1
    "Fed Funds Rate":     lambda d, days: filter_period(d["fed_rate"],       days),
    "BOJ Policy Rate":    lambda d, days: filter_period(d["boj_policy_rate"], days),
    "Fed Total Assets":   lambda d, days: filter_period(d["fed_assets"],      days),
    "BOJ Call Rate":      lambda d, days: filter_period(d["boj_call_rate"],   days),
    # Section 2
    "BOJ Total Assets":   lambda d, days: filter_period(d["boj_total_assets"],  days),
    "BOJ JGB Holdings":   lambda d, days: filter_period(d["boj_jgb"],           days),
    "BOJ ETF Holdings":   lambda d, days: filter_period(d["boj_etf"],           days),
    "BOJ Monetary Base":  lambda d, days: filter_period(d["boj_monetary_base"], days),
    # Section 3
    "US M2":              lambda d, days: filter_period(d["us_m2"],        days),
    "Japan M2":           lambda d, days: filter_period(d["boj_m2"],       days),
    "Fed RRP":            lambda d, days: filter_period(d["rrp"],          days),
    "TGA":                lambda d, days: filter_period(d["tga"],          days),
    "Bank Credit":        lambda d, days: filter_period(d["bank_credit"],  days),
    # Section 4
    "US 2Y Yield":        lambda d, days: filter_period(d["us2y"],          days),
    "US 10Y Yield":       lambda d, days: filter_period(d["us10y"],         days),
    "2Y–10Y Spread":      lambda d, days: filter_period(d["spread_2y10y"],  days),
    "JGB 10Y Yield":      lambda d, days: filter_period(d["jgb10y"],        days),
    "HY Credit Spread":   lambda d, days: filter_period(d["hy_spread"],     days),
    # Section 5
    "DXY":                lambda d, days: pick_series(d, "dxy",    days),
    "EUR/USD":            lambda d, days: pick_series(d, "eurusd", days),
    "USD/JPY":            lambda d, days: pick_series(d, "usdjpy", days),
    "USD/MXN":            lambda d, days: pick_series(d, "usdmxn", days),
    "S&P 500":            lambda d, days: pick_series(d, "sp500",  days),
    "Nikkei 225":         lambda d, days: pick_series(d, "nikkei", days),
    "Gold":               lambda d, days: pick_series(d, "gold",   days),
    "VIX":                lambda d, days: pick_series(d, "vix",    days),
    # Section 6
    "CPI YoY":            lambda d, days: filter_period(d["cpi_yoy"], days),
    "WTI Crude":          lambda d, days: filter_period(d["wti"],     days),
    "Housing Starts":     lambda d, days: filter_period(d["housing"], days),
    "CAPE":               lambda d, days: filter_period(d["cape"],    days),
}

cmp_left, cmp_right = st.columns([3, 1])
with cmp_left:
    selected = st.multiselect(
        "Select indicators",
        options=list(ALL_INDICATORS.keys()),
        default=["Fed Funds Rate", "US 10Y Yield", "2Y–10Y Spread"],
        label_visibility="collapsed",
    )
with cmp_right:
    cmp_label, cmp_days = period_selector("compare_p")

if selected:
    cmp_data = {name: ALL_INDICATORS[name](data, cmp_days) for name in selected}
    st.plotly_chart(make_comparison_chart(cmp_data, cmp_label), use_container_width=True)
else:
    st.info("Select indicators above to compare.")
