"""
Aeon Nimbus — Position Sizing Calculator
=========================================
Standalone CLI tool implementing three institutional position sizing methods:
  1. Kelly Criterion (full, half, quarter Kelly)
  2. Fixed-Risk / 1R Method (Van Tharp framework)
  3. Conviction-Weighted Framework (tiered Kelly)

No external dependencies — Python standard library only.
"""

import math
import statistics


# ---------------------------------------------------------------------------
# Default parameters
# ---------------------------------------------------------------------------
DEFAULTS = {
    "p":         0.60,       # win probability
    "b":         2.50,       # win/loss ratio (reward / risk)
    "capital":   100_000.0,  # portfolio capital ($)
    "max_cap":   0.10,       # maximum single-position cap (fraction)
    "entry":     10.51,      # entry price ($)
    "stop":      7.20,       # stop-loss price ($)
    "target":    17.30,      # price target ($)
    "risk_pct":  0.015,      # risk per trade as fraction of capital
    "conviction": 7,          # 1–10 conviction score
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def fmt_dollar(amount: float) -> str:
    """Format a float as a dollar amount with commas."""
    return f"${amount:,.2f}"


def fmt_pct(fraction: float) -> str:
    """Format a fraction as a percentage string."""
    return f"{fraction * 100:.2f}%"


def divider(char: str = "-", width: int = 62) -> str:
    return char * width


def header(title: str, char: str = "=", width: int = 62) -> None:
    print()
    print(divider(char, width))
    print(f"  {title}")
    print(divider(char, width))


def section(title: str) -> None:
    print()
    print(f"  {title}")
    print("  " + divider("-", 40))


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------
def prompt_float(label: str, default: float, lo: float = None, hi: float = None) -> float:
    while True:
        raw = input(f"  {label} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            val = float(raw)
            if lo is not None and val < lo:
                print(f"    ! Value must be >= {lo}")
                continue
            if hi is not None and val > hi:
                print(f"    ! Value must be <= {hi}")
                continue
            return val
        except ValueError:
            print("    ! Please enter a valid number.")


def prompt_int(label: str, default: int, lo: int = None, hi: int = None) -> int:
    while True:
        raw = input(f"  {label} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            val = int(raw)
            if lo is not None and val < lo:
                print(f"    ! Value must be >= {lo}")
                continue
            if hi is not None and val > hi:
                print(f"    ! Value must be <= {hi}")
                continue
            return val
        except ValueError:
            print("    ! Please enter a valid integer.")


def collect_kelly_inputs() -> dict:
    section("Kelly Criterion Inputs")
    p         = prompt_float("Win probability (0–1)", DEFAULTS["p"],        lo=0.01, hi=0.99)
    b         = prompt_float("Win/Loss ratio (b)",    DEFAULTS["b"],        lo=0.01)
    capital   = prompt_float("Portfolio capital ($)", DEFAULTS["capital"],  lo=1.0)
    max_cap   = prompt_float("Max position cap (0–1)", DEFAULTS["max_cap"], lo=0.01, hi=1.0)
    return {"p": p, "b": b, "capital": capital, "max_cap": max_cap}


def collect_fixed_risk_inputs() -> dict:
    section("Fixed-Risk (1R) Inputs")
    capital   = prompt_float("Portfolio capital ($)",  DEFAULTS["capital"],   lo=1.0)
    risk_pct  = prompt_float("Risk % per trade (0–1)", DEFAULTS["risk_pct"],  lo=0.001, hi=0.5)
    entry     = prompt_float("Entry price ($)",         DEFAULTS["entry"],     lo=0.01)
    stop      = prompt_float("Stop-loss price ($)",     DEFAULTS["stop"],      lo=0.01)
    target    = prompt_float("Price target ($)",        DEFAULTS["target"],    lo=0.01)
    conviction = prompt_int( "Conviction score (1–10)", DEFAULTS["conviction"], lo=1, hi=10)
    return {
        "capital": capital,
        "risk_pct": risk_pct,
        "entry": entry,
        "stop": stop,
        "target": target,
        "conviction": conviction,
    }


def collect_conviction_inputs() -> dict:
    section("Conviction-Weighted Framework Inputs")
    p          = prompt_float("Win probability (0–1)",  DEFAULTS["p"],          lo=0.01, hi=0.99)
    b          = prompt_float("Win/Loss ratio (b)",     DEFAULTS["b"],          lo=0.01)
    capital    = prompt_float("Portfolio capital ($)",  DEFAULTS["capital"],    lo=1.0)
    conviction = prompt_int(  "Conviction score (1–10)",DEFAULTS["conviction"], lo=1, hi=10)
    return {"p": p, "b": b, "capital": capital, "conviction": conviction}


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------
def kelly_fraction(p: float, b: float) -> float:
    """
    Kelly Criterion: f* = (p*b - (1-p)) / b
    Returns the raw (full) Kelly fraction.
    """
    return (p * b - (1 - p)) / b


def conviction_tier(conviction: int) -> tuple:
    """
    Returns (tier_label, kelly_modifier, position_cap) for a conviction score.
    High  8–10 : half Kelly, cap 8%
    Medium 5–7 : quarter Kelly, cap 5%
    Low   1–4  : fixed 2% (Kelly ignored)
    """
    if conviction >= 8:
        return ("High (8–10)", 0.5, 0.08)
    elif conviction >= 5:
        return ("Medium (5–7)", 0.25, 0.05)
    else:
        return ("Low (1–4)", None, 0.02)


# ---------------------------------------------------------------------------
# Method 1 — Kelly Criterion
# ---------------------------------------------------------------------------
def run_kelly(inputs: dict = None, silent: bool = False) -> dict:
    """
    Display Kelly Criterion analysis.
    Returns dict with allocation fractions for comparison mode.
    """
    if inputs is None:
        inputs = collect_kelly_inputs()

    p       = inputs["p"]
    b       = inputs["b"]
    capital = inputs["capital"]
    max_cap = inputs["max_cap"]

    raw_kelly = kelly_fraction(p, b)
    half_kelly    = raw_kelly * 0.5
    quarter_kelly = raw_kelly * 0.25

    # Apply cap
    full_k_applied    = min(raw_kelly,    max_cap) if raw_kelly    > 0 else 0.0
    half_k_applied    = min(half_kelly,   max_cap) if half_kelly   > 0 else 0.0
    quarter_k_applied = min(quarter_kelly,max_cap) if quarter_kelly > 0 else 0.0

    if not silent:
        header("METHOD 1 — KELLY CRITERION")

        print(f"\n  Inputs:")
        print(f"    Win Probability (p) : {fmt_pct(p)}")
        print(f"    Win/Loss Ratio  (b) : {b:.2f}x")
        print(f"    Portfolio Capital   : {fmt_dollar(capital)}")
        print(f"    Max Position Cap    : {fmt_pct(max_cap)}")

        section("Kelly Formula:  f* = (p × b − (1 − p)) / b")
        print(f"  f* = ({p:.2f} × {b:.2f} − {1-p:.2f}) / {b:.2f}")
        print(f"  f* = ({p*b:.4f} − {1-p:.4f}) / {b:.2f}")
        print(f"  f* = {p*b-(1-p):.4f} / {b:.2f}")
        print(f"  f* = {raw_kelly:.4f}  ({fmt_pct(raw_kelly)})")

        section("Kelly Fractions")
        rows = [
            ("Full Kelly",    raw_kelly,     full_k_applied),
            ("Half Kelly",    half_kelly,    half_k_applied),
            ("Quarter Kelly", quarter_kelly, quarter_k_applied),
        ]
        print(f"  {'Fraction':<16} {'Raw %':>9} {'Applied %':>11} {'$ Amount':>12}  {'Note'}")
        print("  " + divider("-", 58))
        for label, raw, applied in rows:
            capped = " [capped]" if raw > max_cap else ""
            print(
                f"  {label:<16} {fmt_pct(raw):>9} {fmt_pct(applied):>11} "
                f"{fmt_dollar(applied * capital):>12}  {capped}"
            )

        section("Interpretation")
        if raw_kelly <= 0:
            print("  WARNING: Negative Kelly — this edge has no positive expectancy.")
            print("  Do not trade this setup.")
        else:
            print(f"  Full Kelly ({fmt_pct(raw_kelly)}) maximizes log-wealth growth but carries")
            print(f"  severe drawdown risk in practice due to parameter estimation error.")
            print()
            print(f"  >> Recommended: Half Kelly at {fmt_pct(half_k_applied)}")
            print(f"     ({fmt_dollar(half_k_applied * capital)}) — balances growth with risk.")
            print()
            if raw_kelly > max_cap:
                print(f"  NOTE: Raw Kelly ({fmt_pct(raw_kelly)}) exceeds your cap of {fmt_pct(max_cap)}.")
                print(f"        All fractions capped accordingly.")

    return {
        "full_kelly":    full_k_applied,
        "half_kelly":    half_k_applied,
        "quarter_kelly": quarter_k_applied,
        "raw_kelly":     raw_kelly,
        "capital":       capital,
    }


# ---------------------------------------------------------------------------
# Method 2 — Fixed-Risk (1R)
# ---------------------------------------------------------------------------
def run_fixed_risk(inputs: dict = None, silent: bool = False) -> dict:
    """
    Display Fixed-Risk (1R) analysis.
    Returns dict with position data for comparison mode.
    """
    if inputs is None:
        inputs = collect_fixed_risk_inputs()

    capital    = inputs["capital"]
    risk_pct   = inputs["risk_pct"]
    entry      = inputs["entry"]
    stop       = inputs["stop"]
    target     = inputs["target"]
    conviction = inputs["conviction"]

    risk_dollars    = capital * risk_pct
    risk_per_share  = abs(entry - stop)
    shares          = math.floor(risk_dollars / risk_per_share) if risk_per_share > 0 else 0
    position_value  = shares * entry
    alloc_pct       = position_value / capital if capital > 0 else 0.0

    # R-multiple (assumes long: entry > stop, target > entry)
    if (entry - stop) != 0:
        r_multiple = (target - entry) / (entry - stop)
    else:
        r_multiple = 0.0

    r_below_threshold = r_multiple < 2.0

    # Conviction commentary
    if conviction >= 8:
        conv_comment = "High conviction — sizing justified; manage the trade actively."
    elif conviction >= 5:
        conv_comment = "Medium conviction — standard 1R sizing appropriate."
    else:
        conv_comment = "Low conviction — consider reducing size or passing the trade."

    if not silent:
        header("METHOD 2 — FIXED-RISK (1R) METHOD")

        print(f"\n  Inputs:")
        print(f"    Portfolio Capital   : {fmt_dollar(capital)}")
        print(f"    Risk Per Trade      : {fmt_pct(risk_pct)}  ({fmt_dollar(risk_dollars)})")
        print(f"    Entry Price         : {fmt_dollar(entry)}")
        print(f"    Stop-Loss Price     : {fmt_dollar(stop)}")
        print(f"    Price Target        : {fmt_dollar(target)}")
        print(f"    Conviction Score    : {conviction}/10")

        section("Position Sizing Calculation")
        print(f"  Risk ($)         = Capital × Risk%")
        print(f"                   = {fmt_dollar(capital)} × {fmt_pct(risk_pct)}")
        print(f"                   = {fmt_dollar(risk_dollars)}")
        print()
        print(f"  Risk/Share       = |Entry − Stop|")
        print(f"                   = |{fmt_dollar(entry)} − {fmt_dollar(stop)}|")
        print(f"                   = {fmt_dollar(risk_per_share)}")
        print()
        print(f"  Shares           = floor(Risk$ / Risk/Share)")
        print(f"                   = floor({fmt_dollar(risk_dollars)} / {fmt_dollar(risk_per_share)})")
        print(f"                   = {shares:,} shares")
        print()
        print(f"  Position Value   = Shares × Entry")
        print(f"                   = {shares:,} × {fmt_dollar(entry)}")
        print(f"                   = {fmt_dollar(position_value)}")
        print(f"  Allocation       = {fmt_pct(alloc_pct)} of capital")

        section("R-Multiple Analysis")
        print(f"  R-Multiple       = (Target − Entry) / (Entry − Stop)")
        print(f"                   = ({fmt_dollar(target)} − {fmt_dollar(entry)}) / ({fmt_dollar(entry)} − {fmt_dollar(stop)})")
        print(f"                   = {fmt_dollar(target - entry)} / {fmt_dollar(entry - stop)}")
        print(f"                   = {r_multiple:.2f}R")
        print()
        if r_below_threshold:
            print(f"  !! WARNING: R-multiple of {r_multiple:.2f}R is BELOW the 2.0R minimum threshold.")
            print(f"     A reward-to-risk ratio under 2:1 makes it difficult to overcome")
            print(f"     transaction costs and losses over a large sample of trades.")
            print(f"     Consider adjusting your target or stop before entering.")
        else:
            print(f"  R-multiple of {r_multiple:.2f}R exceeds the 2.0R minimum — reward structure is sound.")

        section("Conviction Adjustment")
        print(f"  Score: {conviction}/10 — {conv_comment}")

        section("Result")
        print(f"  Shares to Buy    : {shares:,}")
        print(f"  Position Value   : {fmt_dollar(position_value)}")
        print(f"  Capital At Risk  : {fmt_dollar(risk_dollars)}  ({fmt_pct(risk_pct)})")
        print(f"  Portfolio Alloc  : {fmt_pct(alloc_pct)}")
        print(f"  R-Multiple       : {r_multiple:.2f}R")

    return {
        "shares":         shares,
        "position_value": position_value,
        "alloc_pct":      alloc_pct,
        "risk_dollars":   risk_dollars,
        "risk_pct":       risk_pct,
        "r_multiple":     r_multiple,
        "capital":        capital,
        "r_below_threshold": r_below_threshold,
    }


# ---------------------------------------------------------------------------
# Method 3 — Conviction-Weighted Framework
# ---------------------------------------------------------------------------
def run_conviction(inputs: dict = None, silent: bool = False) -> dict:
    """
    Display Conviction-Weighted Framework analysis.
    Returns dict with allocation data for comparison mode.
    """
    if inputs is None:
        inputs = collect_conviction_inputs()

    p          = inputs["p"]
    b          = inputs["b"]
    capital    = inputs["capital"]
    conviction = inputs["conviction"]

    raw_kelly               = kelly_fraction(p, b)
    tier_label, modifier, cap = conviction_tier(conviction)

    if modifier is None:
        # Low conviction — fixed 2%
        final_alloc = cap
        applied_kelly = None
        modifier_label = "Fixed 2% (Kelly ignored)"
    else:
        applied_kelly = raw_kelly * modifier
        final_alloc   = min(applied_kelly, cap)
        modifier_label = f"× {modifier} (Kelly modifier)"

    dollar_amount = final_alloc * capital

    if not silent:
        header("METHOD 3 — CONVICTION-WEIGHTED FRAMEWORK")

        print(f"\n  Inputs:")
        print(f"    Win Probability (p) : {fmt_pct(p)}")
        print(f"    Win/Loss Ratio  (b) : {b:.2f}x")
        print(f"    Portfolio Capital   : {fmt_dollar(capital)}")
        print(f"    Conviction Score    : {conviction}/10")

        section("Conviction Tier Classification")
        print(f"  Score {conviction}/10 maps to: {tier_label}")
        print()
        print(f"  {'Score Range':<14} {'Tier':<12} {'Kelly Modifier':<20} {'Position Cap'}")
        print("  " + divider("-", 55))
        print(f"  {'8–10':<14} {'High':<12} {'Half Kelly (×0.5)':<20} {'8%'}")
        print(f"  {'5–7':<14} {'Medium':<12} {'Quarter Kelly (×0.25)':<20} {'5%'}")
        print(f"  {'1–4':<14} {'Low':<12} {'Fixed 2%':<20} {'2%'}")

        section("Allocation Calculation")
        print(f"  Raw (Full) Kelly    : {fmt_pct(raw_kelly)}" +
              (" [negative — no edge]" if raw_kelly <= 0 else ""))

        if modifier is not None:
            print(f"  Kelly Modifier      : {modifier_label}")
            print(f"  Modified Kelly      : {fmt_pct(applied_kelly)}")
            print(f"  Position Cap        : {fmt_pct(cap)}")
            capped = applied_kelly > cap
            print(f"  Final Allocation    : {fmt_pct(final_alloc)}" +
                  (" [capped at tier limit]" if capped else ""))
        else:
            print(f"  Modifier            : {modifier_label}")
            print(f"  Final Allocation    : {fmt_pct(final_alloc)}")

        print(f"  Dollar Amount       : {fmt_dollar(dollar_amount)}")

        section("Interpretation")
        if conviction >= 8:
            print(f"  High conviction warrants half Kelly. You have strong evidence for this")
            print(f"  trade and can justify larger sizing — capped at 8% to prevent")
            print(f"  overconcentration in any single name.")
        elif conviction >= 5:
            print(f"  Medium conviction uses quarter Kelly — a conservative stance that")
            print(f"  acknowledges uncertainty. At 5% cap, the position can move meaningfully")
            print(f"  without catastrophic portfolio impact if the thesis is wrong.")
        else:
            print(f"  Low conviction bypasses Kelly entirely. A fixed 2% keeps exposure")
            print(f"  minimal. If you cannot articulate a clear edge, sizing should reflect")
            print(f"  that epistemic humility.")

    return {
        "tier_label":    tier_label,
        "raw_kelly":     raw_kelly,
        "modifier":      modifier,
        "final_alloc":   final_alloc,
        "dollar_amount": dollar_amount,
        "capital":       capital,
    }


# ---------------------------------------------------------------------------
# Method 4 — Compare All
# ---------------------------------------------------------------------------
def run_compare_all() -> None:
    """
    Run all three methods with shared default inputs and display a comparison table.
    """
    header("METHOD 4 — COMPARE ALL (DEFAULT INPUTS)", "=")
    print(f"\n  All methods use the same default parameters:")
    print(f"    p={DEFAULTS['p']}, b={DEFAULTS['b']}, Capital={fmt_dollar(DEFAULTS['capital'])}")
    print(f"    Max Cap={fmt_pct(DEFAULTS['max_cap'])}, Entry={fmt_dollar(DEFAULTS['entry'])},")
    print(f"    Stop={fmt_dollar(DEFAULTS['stop'])}, Target={fmt_dollar(DEFAULTS['target'])},")
    print(f"    Risk%={fmt_pct(DEFAULTS['risk_pct'])}, Conviction={DEFAULTS['conviction']}/10")

    # Run each silently with defaults
    kelly_res = run_kelly(inputs={
        "p": DEFAULTS["p"], "b": DEFAULTS["b"],
        "capital": DEFAULTS["capital"], "max_cap": DEFAULTS["max_cap"],
    }, silent=True)

    fr_res = run_fixed_risk(inputs={
        "capital": DEFAULTS["capital"], "risk_pct": DEFAULTS["risk_pct"],
        "entry": DEFAULTS["entry"], "stop": DEFAULTS["stop"],
        "target": DEFAULTS["target"], "conviction": DEFAULTS["conviction"],
    }, silent=True)

    conv_res = run_conviction(inputs={
        "p": DEFAULTS["p"], "b": DEFAULTS["b"],
        "capital": DEFAULTS["capital"], "conviction": DEFAULTS["conviction"],
    }, silent=True)

    capital = DEFAULTS["capital"]

    # Build comparison rows
    kelly_alloc = kelly_res["half_kelly"]   # recommended half Kelly
    fr_alloc    = fr_res["alloc_pct"]
    conv_alloc  = conv_res["final_alloc"]

    kelly_comment = f"Half Kelly; raw={fmt_pct(kelly_res['raw_kelly'])}"
    fr_r          = fr_res["r_multiple"]
    fr_comment    = f"{fr_r:.2f}R" + (" [below 2R threshold]" if fr_res["r_below_threshold"] else "")
    conv_comment  = f"Tier: {conv_res['tier_label']}"

    rows = [
        ("Kelly (Half)",       kelly_alloc, kelly_alloc * capital, kelly_comment),
        ("Fixed-Risk (1R)",    fr_alloc,    fr_alloc * capital,    fr_comment),
        ("Conviction-Weighted",conv_alloc,  conv_alloc * capital,  conv_comment),
    ]

    section("Comparison Table")
    col1, col2, col3, col4 = 24, 14, 14, 32
    header_row = f"  {'Method':<{col1}} {'Alloc %':>{col2}} {'$ Amount':>{col3}}  {'Commentary'}"
    print(header_row)
    print("  " + divider("-", col1 + col2 + col3 + col4))
    for method, alloc, dollar, comment in rows:
        print(f"  {method:<{col1}} {fmt_pct(alloc):>{col2}} {fmt_dollar(dollar):>{col3}}  {comment}")

    # Identify most conservative
    allocs = {
        "Kelly (Half)":        kelly_alloc,
        "Fixed-Risk (1R)":     fr_alloc,
        "Conviction-Weighted": conv_alloc,
    }
    most_conservative = min(allocs, key=allocs.get)
    min_alloc = allocs[most_conservative]

    section("Analysis")
    print(f"  Most conservative method : {most_conservative} at {fmt_pct(min_alloc)}")
    print()

    alloc_vals = list(allocs.values())
    spread = max(alloc_vals) - min(alloc_vals)
    print(f"  Spread across methods    : {fmt_pct(spread)}")
    print(f"  Highest allocation       : {fmt_pct(max(alloc_vals))}")
    print(f"  Lowest allocation        : {fmt_pct(min(alloc_vals))}")
    print()

    print(f"  When methods diverge significantly, that divergence itself is a signal.")
    print(f"  A disciplined PM uses the most conservative allocation when conviction")
    print(f"  is ambiguous, and revisits inputs before sizing up.")
    print()
    if fr_res["r_below_threshold"]:
        print(f"  !! NOTE: The Fixed-Risk method flagged an R-multiple of {fr_res['r_multiple']:.2f}R —")
        print(f"     below the 2.0R minimum. Reconsider the target or stop before entering.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def print_banner() -> None:
    print()
    print(divider("=", 62))
    print("  AEON NIMBUS — POSITION SIZING CALCULATOR")
    print("  Python Standard Library Edition")
    print(divider("=", 62))
    print()
    print("  Methods:")
    print("    1  Kelly Criterion")
    print("    2  Fixed-Risk (1R) Method")
    print("    3  Conviction-Weighted Framework")
    print("    4  Compare All (uses defaults)")
    print("    0  Exit")
    print()


def main() -> None:
    print_banner()
    while True:
        try:
            choice = input("  Select method [0–4]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Exiting. Trade well.")
            break

        if choice == "0":
            print("\n  Exiting. Trade well.")
            break
        elif choice == "1":
            run_kelly()
        elif choice == "2":
            run_fixed_risk()
        elif choice == "3":
            run_conviction()
        elif choice == "4":
            run_compare_all()
        else:
            print("  Invalid choice. Enter 0, 1, 2, 3, or 4.")
            continue

        print()
        input("  Press Enter to return to the menu...")
        print_banner()


if __name__ == "__main__":
    main()
