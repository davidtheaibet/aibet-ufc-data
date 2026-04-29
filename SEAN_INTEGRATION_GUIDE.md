# UFC Prediction System v2.0 — Changes for Sean

## Overview

Updated the UFC prediction pipeline to separate **Probability** from **Confidence** and add **Edge** calculation against market odds.

---

## Key Changes

### 1. PROBABILITY (What the model predicts)

**What it is:** The model's calculated win chance for each fighter.

**Example:**
```
Josh Emmett: 63% win probability
Kevin Vallejos: 37% win probability
```

**How it's calculated:**
- Striking score (25%)
- Grappling score (25%)
- Experience score (20%)
- Recent form score (20%)
- Finish threat score (10%)
- Sigmoid function converts score differential to probability

---

### 2. CONFIDENCE (How reliable is this prediction?)

**What it is:** A separate metric measuring prediction reliability — NOT the same as probability.

**Example:**
```
Confidence: 72.5% (Moderate)
```

**How it's calculated (5 factors):**

| Factor | Weight | Description |
|--------|--------|-------------|
| Data Quality | 25% | Completeness of fighter stats (SLpM, accuracy, defense, etc.) |
| Sample Size | 20% | Fight history depth (more fights = more reliable) |
| Recency | 15% | How recent the data is |
| Model Calibration | 25% | Historical accuracy at this probability level |
| Prediction Certainty | 15% | Internal model certainty based on score differential |

**Confidence Bands:**
- **High:** 80-100% — Very reliable prediction
- **Moderate:** 60-79% — Reasonably reliable
- **Low-Moderate:** 40-59% — Some uncertainty
- **Low:** 0-39% — High uncertainty, limited data

---

### 3. EDGE (Model vs Market)

**What it is:** The difference between model probability and market-implied probability.

**Formula:**
```
EDGE = Model Probability − Market Probability
```

**Example:**
```
Model: 63%
Market: 55% (after vig removal)
Edge: +8% (Value bet)
```

**Edge Ratings:**
| Edge | Rating | Meaning |
|------|--------|---------|
| ≥ +10% | Strong Value | Model sees significant value |
| +5% to +9.9% | Value | Model sees moderate value |
| +2% to +4.9% | Slight Value | Marginal value |
| −2% to +2% | Fair Price | Model agrees with market |
| −5% to −2.1% | Slight Underlay | Model sees slight negative value |
| < −5% | No Value | Model disagrees with market (don't bet) |

---

## New Files Created

### 1. `odds_integration.py`
Handles market odds:
- Fetch odds from bookmakers (Ladbrokes, Sportsbet, etc.)
- Convert between odds formats (decimal, American, fractional)
- Calculate implied probabilities: `1 / decimal_odds`
- **Remove vig:** Normalize probabilities so they sum to 100%
- Calculate edge: `Model Prob − Market Prob`

### 2. `confidence_calculator.py`
Calculates prediction confidence:
- Data quality assessment
- Sample size scoring
- Recency weighting
- Model calibration tracking
- Prediction certainty scoring

### 3. `analysis_engine_v2.py`
Updated analysis engine:
- Integrates odds and confidence
- Returns `FightPrediction` object with all metrics
- JSON output for API consumption

---

## API Output Format

```json
{
  "fighter_a": {
    "name": "Josh Emmett",
    "record": "19-4-0",
    "scores": { "striking": 78.5, "grappling": 65.2, ... }
  },
  "fighter_b": { ... },
  "prediction": {
    "winner": "Josh Emmett",
    "model_probability": {
      "fighter_a": "63.0%",
      "fighter_b": "37.0%"
    },
    "confidence": {
      "score": 72.5,
      "band": "Moderate",
      "factors": {
        "data_quality": 85.0,
        "sample_size": 80.0,
        "recency": 65.0,
        "model_calibration": 75.0,
        "prediction_certainty": 68.0
      }
    },
    "likely_method": "Decision",
    "ai_reason": "Emmett favored due to: Striking advantage (+15), Experience edge (23 vs 15 fights)"
  },
  "market": {
    "odds": {
      "fighter_a": "-125 (1.80)",
      "fighter_b": "+120 (2.20)",
      "source": "Ladbrokes"
    },
    "implied_probability": {
      "fighter_a": "55.0%",
      "fighter_b": "45.0%"
    }
  },
  "edge": {
    "fighter_a": {
      "value": "+8.0%",
      "rating": "Value"
    },
    "fighter_b": {
      "value": "-8.0%",
      "rating": "No Value"
    }
  }
}
```

---

## Next Steps for Integration

### 1. Odds API Integration

The `odds_integration.py` module has placeholders for bookmaker APIs. You need to implement:

```python
def fetch_odds_from_api(self, fighter_a, fighter_b, bookmaker="ladbrokes"):
    # TODO: Implement actual API calls
    # Options:
    # - Ladbrokes API
    # - Sportsbet API
    # - Bet365 API
    # - The Odds API (aggregated odds)
```

**Recommended:** Use [The Odds API](https://the-odds-api.com/) — single API for multiple bookmakers.

### 2. Model Calibration Data

Populate `calibration_data` with historical performance:

```python
calibration_data = {
    0.50: 0.48,  # When model predicts 50%, it wins 48% of the time
    0.60: 0.58,  # When model predicts 60%, it wins 58% of the time
    0.70: 0.72,  # When model predicts 70%, it wins 72% of the time
    ...
}
```

This improves confidence calculations over time.

### 3. Deployment

```bash
# Install dependencies
pip install requests beautifulsoup4

# Test the new engine
python3 analysis_engine_v2.py

# Use in your API
from analysis_engine_v2 import UFCAnalysisEngineV2
engine = UFCAnalysisEngineV2()
result = engine.analyze_matchup_to_dict("Fighter A", "Fighter B", market_odds)
```

---

## Summary Table

| Metric | Old System | New System | Purpose |
|--------|-----------|------------|---------|
| **Probability** | Win % only | Win % only | What the model predicts |
| **Confidence** | High/Med/Low (based on prob) | 0-100 score with factors | How reliable is this prediction? |
| **Edge** | Not calculated | Model − Market | Is there betting value? |
| **Market Data** | Not included | Odds + implied prob | Compare model to market |

---

## Questions?

The system is ready for integration. The main remaining work is:
1. Connect to a live odds API
2. Populate calibration data from historical results

Let me know if you need any adjustments to the calculations or output format.
