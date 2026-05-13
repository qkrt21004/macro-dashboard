"""
Earnings Calendar events for the macro dashboard.
Companies grouped by GICS sector with confirmed earnings dates.
Includes BMO (Before Market Open) / AMC (After Market Close) timing.
"""

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


def _ev(ticker: str, date: str, timing: str, sector_key: str) -> dict:
    """Build a calendar event dict."""
    return {
        "title":  f"{ticker} · {timing}",
        "start":  date,
        "color":  SC[sector_key],
        "allDay": True,
    }


# ── Earnings events (Q1 2026 reported + TCOM upcoming + Q2 2026 confirmed) ────
EARNINGS_EVENTS = [
    # ══ Health Care — Managed Care ═══════════════════════════════════════════
    _ev("UNH",   "2026-04-21", "BMO", "health"),
    _ev("ELV",   "2026-04-22", "BMO", "health"),
    _ev("HUM",   "2026-04-29", "BMO", "health"),

    # ══ Financials — P&C / Reinsurance ═══════════════════════════════════════
    _ev("PGR",   "2026-04-15", "BMO", "ins_pc"),
    _ev("TRV",   "2026-04-16", "BMO", "ins_pc"),
    _ev("CB",    "2026-04-21", "AMC", "ins_pc"),
    _ev("ACGL",  "2026-04-28", "AMC", "ins_pc"),
    _ev("RNR",   "2026-04-28", "AMC", "ins_pc"),
    _ev("ALL",   "2026-04-29", "AMC", "ins_pc"),
    _ev("AIG",   "2026-04-30", "AMC", "ins_pc"),
    _ev("EG",    "2026-04-30", "AMC", "ins_pc"),

    # ══ Financials — Life & Health Insurance ═════════════════════════════════
    _ev("AFL",   "2026-04-29", "AMC", "ins_life"),
    _ev("PRU",   "2026-05-05", "AMC", "ins_life"),
    _ev("MET",   "2026-05-06", "BMO", "ins_life"),

    # ══ Financials — Diversified (Berkshire) ═════════════════════════════════
    _ev("BRK.B", "2026-05-02", "BMO", "fin_div"),
    _ev("BRK.B", "2026-08-03", "BMO", "fin_div"),    # Q2 2026 confirmed

    # ══ Consumer Staples ═════════════════════════════════════════════════════
    _ev("CL",    "2026-05-01", "BMO", "staples"),

    # ══ Industrials — Machinery ══════════════════════════════════════════════
    _ev("CAT",   "2026-04-30", "BMO", "machinery"),

    # ══ Industrials — Airlines ═══════════════════════════════════════════════
    _ev("DAL",   "2026-04-08", "BMO", "airlines"),
    _ev("ALK",   "2026-04-20", "AMC", "airlines"),
    _ev("UAL",   "2026-04-22", "AMC", "airlines"),
    _ev("LUV",   "2026-04-22", "AMC", "airlines"),
    _ev("AAL",   "2026-04-23", "BMO", "airlines"),

    # ══ Consumer Discretionary — Hotels & Lodging ════════════════════════════
    _ev("HLT",   "2026-04-28", "BMO", "hotels"),
    _ev("WH",    "2026-04-29", "AMC", "hotels"),
    _ev("H",     "2026-04-30", "BMO", "hotels"),
    _ev("MAR",   "2026-05-06", "BMO", "hotels"),

    # ══ Consumer Discretionary — Casinos & Gaming ════════════════════════════
    _ev("LVS",   "2026-04-22", "AMC", "casinos"),
    _ev("CZR",   "2026-04-28", "AMC", "casinos"),
    _ev("MGM",   "2026-04-29", "AMC", "casinos"),
    _ev("WYNN",  "2026-05-06", "AMC", "casinos"),

    # ══ Consumer Discretionary — Cruise Lines ════════════════════════════════
    _ev("CCL",   "2026-03-27", "BMO", "cruise"),     # FY Nov-end fiscal Q1
    _ev("RCL",   "2026-04-30", "BMO", "cruise"),
    _ev("NCLH",  "2026-05-04", "BMO", "cruise"),

    # ══ Consumer Discretionary — Online Travel (OTAs) ════════════════════════
    _ev("BKNG",  "2026-04-28", "AMC", "ota"),
    _ev("TRIP",  "2026-05-06", "AMC", "ota"),
    _ev("ABNB",  "2026-05-07", "AMC", "ota"),
    _ev("EXPE",  "2026-05-07", "AMC", "ota"),
    _ev("TCOM",  "2026-05-25", "BMO", "ota"),        # 🔜 UPCOMING Q1 2026
    _ev("BKNG",  "2026-08-05", "AMC", "ota"),        # Q2 2026 confirmed
    _ev("EXPE",  "2026-08-06", "AMC", "ota"),        # Q2 2026 confirmed
]


def get_earnings_events() -> list:
    """Return all earnings calendar events."""
    return EARNINGS_EVENTS


# ── Legend metadata (for UI display) ─────────────────────────────────────────
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
