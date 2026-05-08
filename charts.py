import pandas as pd
import plotly.graph_objects as go

COLORS = {
    "dxy":     "rgb(99, 179, 237)",
    "eurusd":  "rgb(252, 129, 74)",
    "usdjpy":  "rgb(154, 230, 180)",
    "usdmxn":  "rgb(183, 148, 244)",
    "cpi":     "rgb(252, 129, 74)",
    "us10y":   "rgb(154, 230, 180)",
    "housing": "rgb(183, 148, 244)",
    "cape":    "rgb(251, 211, 141)",
    "wti":        "rgb(118, 169, 133)",
    "fed_rate":   "rgb(99, 179, 237)",
    "fed_assets": "rgb(252, 129, 74)",
    "us_m2":      "rgb(154, 230, 180)",
    "boj_assets":        "rgb(246, 135, 179)",
    "boj_monetary_base": "rgb(246, 135, 179)",
    "boj_m2":            "rgb(129, 230, 217)",
    "boj_total_assets":  "rgb(183, 148, 244)",
    "boj_jgb":           "rgb(251, 211, 141)",
    "boj_etf":           "rgb(118, 169, 133)",
    "boj_call_rate":     "rgb(99, 179, 237)",
    "boj_policy_rate":   "rgb(252, 129, 74)",
}


def _base_layout(fig: go.Figure, title: str, height: int = 300) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#ccc")),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#ccc"),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=False, color="#555"),
        yaxis=dict(showgrid=True, gridcolor="#1e1e2e", color="#555"),
        height=height,
        hovermode="x unified",
    )
    return fig


def make_line_chart(df: pd.DataFrame, title: str, color_key: str, unit: str = "") -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="데이터 없음", x=0.5, y=0.5, showarrow=False)
        return _base_layout(fig, title)

    color = COLORS.get(color_key, "#fff")
    padding = (df["value"].max() - df["value"].min()) * 0.15 or df["value"].mean() * 0.01
    y_floor = df["value"].min() - padding

    # 보이지 않는 기준선 → 데이터까지 채우기 (항상 차트 하단 기준)
    fig.add_trace(go.Scatter(
        x=df["date"], y=[y_floor] * len(df),
        mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["value"],
        mode="lines",
        line=dict(color=color, width=2),
        fill="tonexty",
        fillcolor=color.replace("rgb(", "rgba(").replace(")", ", 0.10)"),
        hovertemplate=f"%{{x|%Y-%m-%d}}: %{{y:.2f}}{unit}<extra></extra>",
    ))
    fig = _base_layout(fig, title)
    fig.update_layout(yaxis=dict(range=[y_floor, df["value"].max() + padding]))
    return fig


COMPARE_COLORS = [
    "rgb(99, 179, 237)",
    "rgb(252, 129, 74)",
    "rgb(154, 230, 180)",
    "rgb(183, 148, 244)",
    "rgb(251, 211, 141)",
    "rgb(246, 135, 179)",
    "rgb(129, 230, 217)",
    "rgb(190, 190, 190)",
]


def make_fed_balance_sheet_chart(df_tsy: pd.DataFrame, df_mbs: pd.DataFrame, period_label: str) -> go.Figure:
    """미국채 + MBS를 스택 영역으로, 비중(%)을 보조 축에 표시."""
    fig = go.Figure()

    if df_tsy.empty or df_mbs.empty:
        fig.add_annotation(text="데이터 없음", x=0.5, y=0.5, showarrow=False)
        return _base_layout(fig, "대차대조표 — 미국채 & MBS")

    # 공통 날짜 기준으로 병합
    merged = pd.merge(
        df_tsy.rename(columns={"value": "tsy"}),
        df_mbs.rename(columns={"value": "mbs"}),
        on="date", how="inner"
    ).sort_values("date")

    total = merged["tsy"] + merged["mbs"]
    tsy_pct = merged["tsy"] / total * 100
    mbs_pct = merged["mbs"] / total * 100

    # 스택 영역 (미국채)
    fig.add_trace(go.Scatter(
        x=merged["date"], y=merged["tsy"],
        name="미국채 (Treasuries)",
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color="rgb(99, 179, 237)"),
        fillcolor="rgba(99, 179, 237, 0.6)",
        hovertemplate="미국채: %{y:,.0f}M<extra></extra>",
    ))
    # 스택 영역 (MBS)
    fig.add_trace(go.Scatter(
        x=merged["date"], y=merged["mbs"],
        name="MBS",
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color="rgb(252, 129, 74)"),
        fillcolor="rgba(252, 129, 74, 0.6)",
        hovertemplate="MBS: %{y:,.0f}M<extra></extra>",
    ))
    # 비중 라인 (보조 y축)
    fig.add_trace(go.Scatter(
        x=merged["date"], y=tsy_pct,
        name="미국채 비중 (%)",
        mode="lines", yaxis="y2",
        line=dict(color="rgb(99, 179, 237)", width=1.5, dash="dot"),
        hovertemplate="미국채 비중: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=merged["date"], y=mbs_pct,
        name="MBS 비중 (%)",
        mode="lines", yaxis="y2",
        line=dict(color="rgb(252, 129, 74)", width=1.5, dash="dot"),
        hovertemplate="MBS 비중: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=f"대차대조표 — 미국채 & MBS ({period_label})", font=dict(size=13, color="#ccc")),
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font=dict(color="#ccc"),
        margin=dict(l=10, r=60, t=40, b=10),
        xaxis=dict(showgrid=False, color="#555"),
        yaxis=dict(title="보유액 (백만 달러)", showgrid=True, gridcolor="#1e1e2e", color="#555"),
        yaxis2=dict(title="비중 (%)", overlaying="y", side="right",
                    color="#888", showgrid=False, range=[0, 100], ticksuffix="%"),
        height=400,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.15, x=0),
    )
    return fig


def make_comparison_chart(dataframes: dict, period_label: str) -> go.Figure:
    """선택된 지표들을 기간 시작 기준 % 변화로 정규화해 비교."""
    fig = go.Figure()
    for i, (label, df) in enumerate(dataframes.items()):
        if df.empty or len(df) < 2:
            continue
        base = df.iloc[0]["value"]
        if base == 0:
            continue
        pct = (df["value"] / base - 1) * 100
        color = COMPARE_COLORS[i % len(COMPARE_COLORS)]
        fig.add_trace(go.Scatter(
            x=df["date"], y=pct,
            mode="lines", name=label,
            line=dict(color=color, width=2),
            hovertemplate=f"{label}: %{{y:+.2f}}%<extra></extra>",
        ))
    fig.add_hline(y=0, line_dash="dot", line_color="#444")
    _base_layout(fig, f"지표 비교 — 기간 시작 대비 % 변화 ({period_label})", height=450)
    fig.update_layout(
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=-0.12, x=0),
    )
    return fig


def make_fx_chart(dataframes: dict, period_label: str) -> go.Figure:
    LABEL_COLORS = {
        "DXY":     COLORS["dxy"],
        "EUR/USD": COLORS["eurusd"],
        "USD/JPY": COLORS["usdjpy"],
        "USD/MXN": COLORS["usdmxn"],
    }
    fig = go.Figure()
    for label, df in dataframes.items():
        if df.empty or len(df) < 2:
            continue
        pct = (df["value"] / df.iloc[0]["value"] - 1) * 100
        fig.add_trace(go.Scatter(
            x=df["date"], y=pct,
            mode="lines", name=label,
            line=dict(color=LABEL_COLORS.get(label, "#fff"), width=2),
            hovertemplate=f"{label}: %{{y:+.2f}}%<extra></extra>",
        ))
    fig.add_hline(y=0, line_dash="dot", line_color="#444")
    _base_layout(fig, f"DXY vs EUR/USD · USD/JPY · USD/MXN — 기간 시작 대비 % 변화 ({period_label})", height=380)
    fig.update_layout(
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", y=-0.12, x=0),
    )
    return fig
