import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from fetcher import load_all
from charts import make_line_chart, make_fx_chart, make_comparison_chart, make_fed_balance_sheet_chart

st.set_page_config(
    page_title="Macro Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* ── 공통 ── */
    .stMetric label { font-size: 0.85rem; color: #888; }
    .block-container { padding-top: 2rem; }
    div[data-testid="stHorizontalBlock"] .stRadio label { font-size: 0.78rem; }

    /* ── 모바일 (640px 이하) ── */
    @media (max-width: 640px) {
        /* 전체 여백 축소 */
        .block-container {
            padding: 1rem 0.75rem !important;
        }

        /* 메트릭 카드 폰트 축소 */
        [data-testid="stMetric"] {
            padding: 0.4rem !important;
        }
        [data-testid="metric-container"] label {
            font-size: 0.65rem !important;
        }
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 1rem !important;
        }
        [data-testid="metric-container"] [data-testid="stMetricDelta"] {
            font-size: 0.65rem !important;
        }

        /* 컬럼 → 세로 스택 */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* 라디오 버튼 가로 스크롤 */
        [data-testid="stRadio"] > div {
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 4px;
        }
        [data-testid="stRadio"] label {
            font-size: 0.7rem !important;
            white-space: nowrap;
        }

        /* 제목 크기 */
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.1rem !important; }
        h3 { font-size: 1rem !important; }

        /* 멀티셀렉트 */
        [data-testid="stMultiSelect"] { font-size: 0.8rem !important; }

        /* 차트 여백 */
        [data-testid="stPlotlyChart"] { margin-bottom: 0.5rem !important; }
    }
</style>
""", unsafe_allow_html=True)

PERIODS = {
    "전체":  None,
    "10년":  365 * 10,
    "5년":   365 * 5,
    "1년":   365,
    "6개월": 183,
    "1개월": 30,
}
SHORT_PERIOD_DAYS = 365


def filter_period(df: pd.DataFrame, days: int | None) -> pd.DataFrame:
    if df.empty or days is None:
        return df
    cutoff = pd.Timestamp(datetime.now() - timedelta(days=days))
    return df[df["date"] >= cutoff].reset_index(drop=True)


def pick_fx(data: dict, key: str, days: int | None) -> pd.DataFrame:
    use_daily = days is not None and days <= SHORT_PERIOD_DAYS
    df = data[f"{key}_daily"] if use_daily else data[key]
    return filter_period(df, days)


def get_latest(df: pd.DataFrame):
    if df.empty or len(df) < 2:
        return None, None
    return df.iloc[-1]["value"], df.iloc[-1]["value"] - df.iloc[-2]["value"]


def period_selector(key: str) -> tuple[str, int | None]:
    """지표별 기간 선택 라디오. (label, days) 반환."""
    label = st.radio(
        "기간", options=list(PERIODS.keys()), index=0,
        horizontal=True, label_visibility="collapsed", key=key,
    )
    return label, PERIODS[label]


# ── Data ──────────────────────────────────────────────────────────────────────

with st.spinner("데이터 불러오는 중..."):
    data = load_all()

# ── Header ────────────────────────────────────────────────────────────────────

st.title("Macro Dashboard")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Data: FRED, Yahoo Finance")

st.divider()

# ── Metric cards (항상 최신값) ────────────────────────────────────────────────

dxy_v,     dxy_d     = get_latest(data["dxy"])
housing_v, housing_d = get_latest(data["housing"])
cpi_v,     cpi_d     = get_latest(data["cpi_yoy"])
us10y_v,   us10y_d   = get_latest(data["us10y"])
eurusd_v,  eurusd_d  = get_latest(data["eurusd"])
usdjpy_v,  usdjpy_d  = get_latest(data["usdjpy"])
usdmxn_v,  usdmxn_d  = get_latest(data["usdmxn"])
cape_v,    cape_d    = get_latest(data["cape"])
wti_v,     wti_d     = get_latest(data["wti"])

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    if dxy_v:     st.metric("DXY",                f"{dxy_v:.2f}",      f"{dxy_d:+.2f}")
with col2:
    if housing_v: st.metric("Housing Starts (천)", f"{housing_v:,.0f}", f"{housing_d:+.0f}")
with col3:
    if cpi_v:     st.metric("CPI YoY (%)",         f"{cpi_v:.2f}%",     f"{cpi_d:+.2f}pp")
with col4:
    if us10y_v:   st.metric("US 10Y (%)",           f"{us10y_v:.3f}%",   f"{us10y_d:+.3f}pp")
with col5:
    if cape_v:    st.metric("CAPE (Shiller PE)",    f"{cape_v:.1f}",     f"{cape_d:+.1f}")
with col6:
    if wti_v:     st.metric("WTI 원유 ($/배럴)",     f"${wti_v:.2f}",     f"{wti_d:+.2f}")

st.divider()

# ── FX 비교 차트 ───────────────────────────────────────────────────────────────

fx_m1, fx_m2, fx_m3 = st.columns(3)
with fx_m1:
    if eurusd_v: st.metric("EUR/USD", f"{eurusd_v:.4f}", f"{eurusd_d:+.4f}")
with fx_m2:
    if usdjpy_v: st.metric("USD/JPY", f"{usdjpy_v:.2f}",  f"{usdjpy_d:+.2f}")
with fx_m3:
    if usdmxn_v: st.metric("USD/MXN", f"{usdmxn_v:.4f}", f"{usdmxn_d:+.4f}")

fx_label, fx_days = period_selector("fx_period")
fig_fx = make_fx_chart({
    "DXY":     pick_fx(data, "dxy",    fx_days),
    "EUR/USD": pick_fx(data, "eurusd", fx_days),
    "USD/JPY": pick_fx(data, "usdjpy", fx_days),
    "USD/MXN": pick_fx(data, "usdmxn", fx_days),
}, fx_label)
st.plotly_chart(fig_fx, use_container_width=True)

st.divider()

# ── 개별 지표 차트 (2열 그리드) ───────────────────────────────────────────────

col_a, col_b = st.columns(2)

with col_a:
    _, cpi_days = period_selector("cpi_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["cpi_yoy"], cpi_days), "CPI — Year-over-Year (%)", "cpi", "%"),
        use_container_width=True,
    )

with col_b:
    _, us10y_days = period_selector("us10y_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["us10y"], us10y_days), "US 10Y Treasury Yield (%)", "us10y", "%"),
        use_container_width=True,
    )

col_c, col_d = st.columns(2)

with col_c:
    _, housing_days = period_selector("housing_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["housing"], housing_days), "Housing Starts (천 호)", "housing", "K"),
        use_container_width=True,
    )

with col_d:
    _, dxy_days = period_selector("dxy_period")
    st.plotly_chart(
        make_line_chart(pick_fx(data, "dxy", dxy_days), "DXY — US Dollar Index", "dxy", ""),
        use_container_width=True,
    )

col_e, col_f = st.columns(2)

with col_e:
    _, cape_days = period_selector("cape_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["cape"], cape_days), "CAPE Ratio (Shiller PE)", "cape", ""),
        use_container_width=True,
    )

with col_f:
    _, wti_days = period_selector("wti_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["wti"], wti_days), "WTI 원유 가격 ($/배럴)", "wti", "$"),
        use_container_width=True,
    )

st.divider()

# ── 중앙은행 통화정책 ──────────────────────────────────────────────────────────

st.subheader("미국")

cb_col1, cb_col2 = st.columns(2)

with cb_col1:
    _, fed_rate_days = period_selector("fed_rate_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["fed_rate"], fed_rate_days), "기준금리 (%)", "fed_rate", "%"),
        use_container_width=True,
    )

with cb_col2:
    _, us_m2_days = period_selector("us_m2_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["us_m2"], us_m2_days), "M2 통화량 (십억 달러)", "us_m2", "B"),
        use_container_width=True,
    )

cb_col3, cb_col4 = st.columns(2)

with cb_col3:
    _, fed_assets_days = period_selector("fed_assets_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["fed_assets"], fed_assets_days), "총자산 — 대차대조표 (백만 달러)", "fed_assets", "M"),
        use_container_width=True,
    )

with cb_col4:
    _, fed_assets_days2 = period_selector("fed_assets_period2")
    st.plotly_chart(
        make_line_chart(filter_period(data["fed_assets"], fed_assets_days2), "총자산 — QE/QT (백만 달러)", "fed_assets", "M"),
        use_container_width=True,
    )

_, fed_bs_days = period_selector("fed_bs_period")
st.plotly_chart(
    make_fed_balance_sheet_chart(
        filter_period(data["fed_treasuries"], fed_bs_days),
        filter_period(data["fed_mbs"],        fed_bs_days),
        _,
    ),
    use_container_width=True,
)

st.divider()

# ── BOJ 통화정책 ───────────────────────────────────────────────────────────────

st.subheader("일본")

boj_col1, boj_col2 = st.columns(2)

with boj_col1:
    _, boj_rate_days = period_selector("boj_policy_rate_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_policy_rate"], boj_rate_days),
                        "정책금리 (%)", "boj_policy_rate", "%"),
        use_container_width=True,
    )

with boj_col2:
    _, boj_call_days = period_selector("boj_call_rate_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_call_rate"], boj_call_days),
                        "무담보 익일물 콜금리 (%)", "boj_call_rate", "%"),
        use_container_width=True,
    )

boj_col3, boj_col4 = st.columns(2)

with boj_col3:
    _, boj_mb_days = period_selector("boj_mb_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_monetary_base"], boj_mb_days),
                        "통화기반 — Monetary Base (억 엔)", "boj_monetary_base", "¥"),
        use_container_width=True,
    )

with boj_col4:
    _, boj_m2_days = period_selector("boj_m2_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_m2"], boj_m2_days),
                        "일본 M2 통화량 (억 엔)", "boj_m2", "¥"),
        use_container_width=True,
    )

boj_col5, boj_col6 = st.columns(2)

with boj_col5:
    _, boj_ta_days = period_selector("boj_total_assets_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_total_assets"], boj_ta_days),
                        "총자산 — 대차대조표 (억 엔)", "boj_total_assets", "¥"),
        use_container_width=True,
    )

with boj_col6:
    _, boj_jgb_days = period_selector("boj_jgb_period")
    st.plotly_chart(
        make_line_chart(filter_period(data["boj_jgb"], boj_jgb_days),
                        "JGB 보유잔액 (억 엔)", "boj_jgb", "¥"),
        use_container_width=True,
    )

_, boj_etf_days = period_selector("boj_etf_period")
st.plotly_chart(
    make_line_chart(filter_period(data["boj_etf"], boj_etf_days),
                    "ETF 보유잔액 (억 엔)", "boj_etf", "¥"),
    use_container_width=True,
)

st.divider()

# ── 지표 비교 툴 ───────────────────────────────────────────────────────────────

st.subheader("지표 비교")

# 비교 가능한 모든 지표 목록
ALL_INDICATORS = {
    "DXY":            lambda d, days: pick_fx(d, "dxy",    days),
    "EUR/USD":        lambda d, days: pick_fx(d, "eurusd", days),
    "USD/JPY":        lambda d, days: pick_fx(d, "usdjpy", days),
    "USD/MXN":        lambda d, days: pick_fx(d, "usdmxn", days),
    "CPI YoY":        lambda d, days: filter_period(d["cpi_yoy"], days),
    "US 10Y":         lambda d, days: filter_period(d["us10y"],   days),
    "Housing Starts": lambda d, days: filter_period(d["housing"], days),
    "CAPE":           lambda d, days: filter_period(d["cape"],    days),
    "WTI 원유":        lambda d, days: filter_period(d["wti"],       days),
    "Fed 기준금리":    lambda d, days: filter_period(d["fed_rate"],   days),
    "Fed 자산 (QE)":  lambda d, days: filter_period(d["fed_assets"], days),
    "US M2":          lambda d, days: filter_period(d["us_m2"],      days),
    "BOJ 총자산":          lambda d, days: filter_period(d["boj_total_assets"],  days),
    "BOJ Monetary Base":  lambda d, days: filter_period(d["boj_monetary_base"], days),
    "BOJ M2":             lambda d, days: filter_period(d["boj_m2"],            days),
    "BOJ JGB":            lambda d, days: filter_period(d["boj_jgb"],           days),
    "BOJ ETF":            lambda d, days: filter_period(d["boj_etf"],           days),
    "BOJ 콜금리":          lambda d, days: filter_period(d["boj_call_rate"],     days),
}

cmp_left, cmp_right = st.columns([3, 1])
with cmp_left:
    selected = st.multiselect(
        "비교할 지표 선택",
        options=list(ALL_INDICATORS.keys()),
        default=["DXY", "US 10Y", "CAPE"],
        label_visibility="collapsed",
    )
with cmp_right:
    cmp_label, cmp_days = period_selector("compare_period")

if selected:
    cmp_data = {name: ALL_INDICATORS[name](data, cmp_days) for name in selected}
    st.plotly_chart(make_comparison_chart(cmp_data, cmp_label), use_container_width=True)
else:
    st.info("위에서 비교할 지표를 선택하세요.")
