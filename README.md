# Aeon Position Sizing Calculator

**Kelly Criterion · Fixed-Risk (1R) · Conviction-Weighted Allocation**

*LiJie Guo · Aeon Nimbus Research · lijieguo.substack.com · [LinkedIn](https://www.linkedin.com/in/lijieguo-es/)*

---

## Overview

Position sizing is, mathematically, the most important decision in active portfolio management — more important than stock selection over the long run, because it determines the compound growth trajectory of capital. An investor with genuine edge and poor sizing will underperform or ruin; an investor with modest edge and optimal sizing will compound to outperformance. This tool implements the three frameworks used by professional PMs: the theoretically optimal Kelly Criterion, the practitioner-standard Fixed-Risk method (1R), and a conviction-tier framework that integrates both under portfolio-level constraints.

```bash
python main.py
```

Python 3.8 or later. No external dependencies.

---

## Methodology

### The Kelly Criterion

The Kelly Criterion identifies the bet size that maximises the expected logarithm of terminal wealth — which is equivalent, by the law of large numbers, to maximising the long-run compound growth rate. For a binary outcome where probability p of winning yields b times the stake, and probability (1−p) of losing the stake:

```
f* = (p·b − (1−p)) / b  =  edge / odds
```

This formula is derived by maximising E[log(W)]. For a fraction f bet on a position with win probability p and win/loss ratio b:

```
E[log(1+f)] = p·log(1+f·b) + (1−p)·log(1−f)
```

Differentiating with respect to f and setting equal to zero yields the Kelly fraction. The result is elegant: the optimal bet size equals the edge divided by the odds. A trade with no edge (p·b = 1−p) should attract zero capital. A trade where p·b > 1−p has positive expectancy and a positive Kelly fraction.

**Why full Kelly is rarely used in practice.** Three reasons conspire against it. First, the inputs — p and b — are estimates, not ground truths. Overestimating the edge by a modest amount leads to a Kelly fraction materially above optimal, generating severe drawdowns even in the absence of an adverse regime. Second, the Kelly strategy produces extreme short-term variance: drawdowns of 50% or more are theoretically consistent with full Kelly even when the true edge is large. Third, most institutional mandates and LP commitments impose constraints on drawdown that are incompatible with full Kelly volatility. For these reasons, practitioners consistently use half Kelly (½f*) or quarter Kelly (¼f*), sacrificing some terminal wealth optimality in exchange for dramatically reduced path-dependent risk.

### Fixed-Risk Method (1R)

The 1R framework, associated with Van Tharp's work in systematic trading, anchors position size directly to the maximum acceptable loss on the trade — a quantity the investor specifies before entering the position, not after observing the outcome:

```
Max Risk $  = Capital × Risk %
Risk/Share  = |Entry − Stop|
Shares      = floor(Max Risk $ / Risk per Share)
Position $  = Shares × Entry Price
```

The R-multiple — reward expressed in units of risk — then measures the quality of the trade's setup independent of its dollar size:

```
R-multiple = (Target − Entry) / (Entry − Stop)    [for a long]
```

The professional minimum is R ≥ 2.0: a trade must offer at least two units of expected reward per unit of accepted risk. The mathematical rationale is straightforward. At a realistic fundamental equity win rate of 40%:

```
E[P&L] = 0.40 × 2R − 0.60 × 1R = +0.20R per trade
```

Below R = 2.0, achieving positive expectancy requires a win rate above 50% — a threshold that is not sustainable systematically across a diversified book of fundamental ideas. The R-minimum is therefore not a conservative preference; it is a mathematical requirement for a viable long-run strategy.

### Conviction-Weighted Framework

Qualitative conviction — the analyst's subjective confidence in the thesis, scored on a 1–10 scale — should map explicitly to quantitative capital commitment. Leaving this mapping implicit allows cognitive biases (overconfidence, anchoring, recency) to contaminate sizing decisions. The conviction-tier framework makes it explicit:

| Conviction | Tier | Kelly Modifier | Maximum Allocation |
|------------|------|----------------|--------------------|
| 8–10 | High | ½ Kelly | 8% of portfolio |
| 5–7 | Medium | ¼ Kelly | 5% of portfolio |
| 1–4 | Low | Fixed 2% | 2% of portfolio |

The hard caps bind regardless of the Kelly fraction: no position exceeds its tier maximum even if Kelly recommends a larger allocation. This belt-and-suspenders design uses Kelly to capture the information in the edge estimate, conviction to temper the Kelly fraction for epistemic uncertainty, and hard caps to enforce portfolio-level discipline unconditionally.

### Comparison View

Evaluating all three methods simultaneously on the same trade is diagnostically valuable. When the methods converge — Kelly, 1R, and conviction-tier all recommend similar allocations — confidence in the sizing is high. When they diverge materially, the gap is a prompt to revisit inputs: either the probability estimate is too aggressive, the risk/stop level is poorly calibrated, or the conviction score does not reflect the quality of the underlying thesis.

---

## Why This Matters

The literature on optimal position sizing — from Kelly's original 1956 Bell System paper through Thorp's applications in blackjack and convertible arbitrage, and into the systematic equity context — converges on a consistent finding: compound growth is highly sensitive to bet sizing, and both over-betting and under-betting are costly, asymmetrically so.

Over-betting a losing sequence destroys capital faster than any other error in the investment process. Under-betting a winning sequence leaves compounding on the table. Because the distribution of outcomes in fundamental equity investing is fat-tailed and non-stationary, the Kelly framework provides a principled, dynamic response to changing edge estimates rather than a fixed allocation rule.

Ed Thorp demonstrated Kelly's practical superiority in blackjack, then in warrant arbitrage at Princeton-Newport Partners. Renaissance Technologies' Medallion Fund applies variants of Kelly-optimal sizing to systematic strategies. Buffett's concentrated portfolios at Berkshire — large positions in high-conviction ideas, nothing in low-conviction ideas — are Kelly-consistent in their structure if not in their derivation. The conviction-tier modification is how fundamental equity PMs operationalise this theory without the data infrastructure required for precise probability estimation.

A buy-side interviewer asking "how do you size positions?" expects an answer that addresses all three dimensions in this tool: mathematical optimality, practical risk control, and conviction-sensitive discretion.

---

## Example Output

```
════════════════════════════════════════════════════════════════
  AEON POSITION SIZING  —  VNET Long
════════════════════════════════════════════════════════════════
  Entry $10.51 | Stop $7.20 | Target $17.30
  Capital: $100,000  |  Conviction: 7/10

  ── Kelly Criterion ──────────────────────────────────────────
  p=0.60, b=2.50× win/loss ratio
  Kelly fraction f*  :  36.0%   (theoretical maximum)
  Full Kelly         :  $10,000   (capped at 10%)
  Half Kelly         :   $5,000   ( 5.0%)   ← recommended
  Quarter Kelly      :   $2,500   ( 2.5%)   ← conservative

  ── Fixed-Risk (1R) ──────────────────────────────────────────
  Risk per share     :  $3.31   (|10.51 − 7.20|)
  Max risk amount    :  $1,500   (1.5% of capital)
  Shares to buy      :  453
  Position value     :  $4,761   (4.8% of portfolio)
  R-multiple         :  2.1R   ✓ meets minimum 2R threshold

  ── Conviction Tier (Medium, 7/10) ───────────────────────────
  Rule:  Quarter Kelly, hard cap at 5%
  Final allocation   :  3.6%  →  $3,600

  ── Comparison ───────────────────────────────────────────────
  Method                 Allocation %    Amount
  Half Kelly                  5.0%       $5,000
  Fixed-Risk (1R)             4.8%       $4,761
  Conviction-weighted         3.6%       $3,600
  → Methods converge: $3,600–$5,000 range.
    Conviction tier is the binding constraint at medium confidence.
```

---

*LiJie Guo · Aeon Nimbus Research · lijieguo.substack.com · [LinkedIn](https://www.linkedin.com/in/lijieguo-es/)*
