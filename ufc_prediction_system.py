"""
UFC Prediction System - Production Ready
Calibrated Confidence with Market Adjustments

Core Principle:
- Probability = raw model prediction
- Confidence = calibrated accuracy adjusted for market conditions  
- Edge = separate metric (0-10), never mixed with confidence
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# ============================================================================
# CALIBRATION DATA (from 292 historical fights)
# ============================================================================

CALIBRATION_BINS = [
    # (min_prob, max_prob, historical_accuracy)
    (0.50, 0.55, 0.68),
    (0.55, 0.58, 0.72),
    (0.58, 1.00, 0.84),  # 58%+ benchmark
]

# ============================================================================
# MARKET ADJUSTMENT CONFIG
# ============================================================================

MARKET_PENALTY_AGAINST_MARKET = 0.05   # Model favors, market doesn't
MARKET_PENALTY_AGAINST_MODEL = 0.08    # Market favors, model doesn't
MARKET_AGREEMENT_THRESHOLD = 0.05      # 5% diff = agreement
ODDS_GAP_PENALTY_PER_10C = 0.01        # -1% per $0.10 gap
MAX_ODDS_GAP_PENALTY = 0.10            # Cap at 10%


# ============================================================================
# EDGE CONFIG
# ============================================================================

EDGE_SCALE_FACTOR = 25  # 0.20 edge = +5 points on 0-10 scale


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_calibrated_confidence(probability: float) -> float:
    """Map probability to calibrated confidence based on historical accuracy."""
    for min_p, max_p, calibrated in CALIBRATION_BINS:
        if min_p <= probability < max_p:
            return calibrated
    return 0.84  # Default to highest band


def get_probability_band(probability: float) -> str:
    """Get probability band for display."""
    if probability < 0.55:
        return "50-55%"
    elif probability < 0.58:
        return "55-58%"
    return "58%+"


def calculate_market_penalty(
    model_prob: float,
    market_prob: Optional[float]
) -> Tuple[float, str]:
    """
    Calculate penalty when market disagrees with model.
    
    Returns: (penalty_amount, alignment_status)
    """
    if market_prob is None:
        return 0.0, "neutral"
    
    diff = abs(model_prob - market_prob)
    
    if diff <= MARKET_AGREEMENT_THRESHOLD:
        return 0.0, "aligned"
    
    if model_prob > market_prob:
        # Model favors fighter more than market
        return MARKET_PENALTY_AGAINST_MARKET, "against_market"
    
    # Market favors fighter more than model
    return MARKET_PENALTY_AGAINST_MODEL, "against_model"


def calculate_odds_gap_penalty(odds_a: float, odds_b: float) -> float:
    """Calculate penalty based on odds gap. Rule: $0.10 = -1% confidence."""
    if not odds_a or not odds_b or odds_a <= 0 or odds_b <= 0:
        return 0.0
    
    gap = abs(odds_a - odds_b)
    penalty = (gap / 0.10) * ODDS_GAP_PENALTY_PER_10C
    return min(penalty, MAX_ODDS_GAP_PENALTY)


def calculate_confidence(
    model_prob: float,
    market_prob: Optional[float] = None,
    market_odds_a: Optional[float] = None,
    market_odds_b: Optional[float] = None
) -> Dict:
    """
    Calculate final confidence score.
    
    Formula:
        confidence = calibrated_confidence(probability)
                   - market_disagreement_penalty
                   - odds_gap_penalty
        clamped to 0-1
    """
    # Step 1: Calibrated base from probability band
    calibrated = get_calibrated_confidence(model_prob)
    
    # Step 2: Market disagreement penalty
    market_penalty, alignment = calculate_market_penalty(model_prob, market_prob)
    
    # Step 3: Odds gap penalty
    odds_penalty = calculate_odds_gap_penalty(market_odds_a, market_odds_b)
    
    # Step 4: Final confidence
    raw = calibrated - market_penalty - odds_penalty
    final = max(0.0, min(1.0, raw))
    
    return {
        "calibrated_base": round(calibrated, 3),
        "market_penalty": round(market_penalty, 3),
        "odds_penalty": round(odds_penalty, 3),
        "final_confidence": round(final, 3),
        "market_alignment": alignment,
        "probability_band": get_probability_band(model_prob)
    }


def calculate_edge_score(model_prob: float, market_prob: float) -> float:
    """
    Calculate edge score (0-10 scale).
    Completely separate from confidence.
    """
    edge = model_prob - market_prob
    score = 5 + (edge * EDGE_SCALE_FACTOR)
    return max(0, min(10, score))


def get_edge_tier(edge_score: float) -> str:
    """Convert edge score to tier."""
    if edge_score >= 7.5:
        return "strong"
    elif edge_score >= 6.0:
        return "medium"
    elif edge_score >= 4.0:
        return "weak"
    return "negative"


# ============================================================================
# MAIN API
# ============================================================================

def calculate_prediction(
    model_prob: float,
    market_prob: Optional[float] = None,
    market_odds_a: Optional[float] = None,
    market_odds_b: Optional[float] = None
) -> Dict:
    """
    Main API function. Returns complete prediction metrics.
    
    Output:
    {
        "probability": 0.63,
        "confidence": 0.75,
        "edge_score": 7.9,
        "edge_tier": "strong", 
        "market_alignment": "against_market"
    }
    """
    # Calculate confidence with market adjustments
    conf_result = calculate_confidence(
        model_prob=model_prob,
        market_prob=market_prob,
        market_odds_a=market_odds_a,
        market_odds_b=market_odds_b
    )
    
    # Calculate edge (separate)
    edge_score = 5.0
    if market_prob is not None:
        edge_score = calculate_edge_score(model_prob, market_prob)
    
    return {
        "probability": round(model_prob, 3),
        "confidence": conf_result["final_confidence"],
        "edge_score": round(edge_score, 1),
        "edge_tier": get_edge_tier(edge_score),
        "market_alignment": conf_result["market_alignment"],
        "confidence_breakdown": {
            "calibrated_base": conf_result["calibrated_base"],
            "market_penalty": conf_result["market_penalty"],
            "odds_penalty": conf_result["odds_penalty"],
            "probability_band": conf_result["probability_band"]
        }
    }


# ============================================================================
# ODDS UTILITIES
# ============================================================================

def decimal_to_implied(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability."""
    return 1 / decimal_odds if decimal_odds > 0 else 0


def remove_vig(implied_a: float, implied_b: float) -> Tuple[float, float]:
    """Remove vig by normalizing implied probabilities."""
    total = implied_a + implied_b
    if total == 0:
        return 0.5, 0.5
    return implied_a / total, implied_b / total


def decimal_to_american(decimal: float) -> int:
    """Convert decimal odds to American format."""
    if decimal >= 2.0:
        return int((decimal - 1) * 100)
    return int(-100 / (decimal - 1))


def format_odds(decimal: float) -> str:
    """Format odds for display."""
    if decimal <= 0:
        return "N/A"
    american = decimal_to_american(decimal)
    if american > 0:
        return f"+{american} ({decimal:.2f})"
    return f"{american} ({decimal:.2f})"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("UFC Prediction System - Production Ready")
    print("=" * 60)
    
    # Example 1: Model and market agree
    print("\n1. Model & Market Aligned")
    print("-" * 40)
    result = calculate_prediction(
        model_prob=0.63,
        market_prob=0.60,
        market_odds_a=1.67,
        market_odds_b=2.50
    )
    print(f"Probability: {result['probability']:.0%}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Edge: {result['edge_score']}/10 ({result['edge_tier']})")
    print(f"Alignment: {result['market_alignment']}")
    
    # Example 2: Model vs Market (Jack vs Carlos scenario)
    print("\n2. Model vs Market (Model favors Jack, Market Carlos)")
    print("-" * 40)
    
    # Model: Jack 63%, Carlos 37%
    # Market: Jack 45%, Carlos 55% (market favors Carlos)
    market_odds_dec = 2.20  # Jack
    market_prob = decimal_to_implied(market_odds_dec)
    market_prob_a, market_prob_b = remove_vig(market_prob, 1 - market_prob)
    
    result = calculate_prediction(
        model_prob=0.63,
        market_prob=market_prob_a,
        market_odds_a=2.20,
        market_odds_b=1.80
    )
    print(f"Probability: {result['probability']:.0%}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"  - Base: {result['confidence_breakdown']['calibrated_base']:.0%}")
    print(f"  - Market Penalty: -{result['confidence_breakdown']['market_penalty']:.0%}")
    print(f"  - Odds Penalty: -{result['confidence_breakdown']['odds_penalty']:.0%}")
    print(f"Edge: {result['edge_score']}/10 ({result['edge_tier']})")
    print(f"Alignment: {result['market_alignment']}")
    
    # Example 3: High probability
    print("\n3. High Probability (72%)")
    print("-" * 40)
    result = calculate_prediction(
        model_prob=0.72,
        market_prob=0.70,
        market_odds_a=1.43,
        market_odds_b=3.00
    )
    print(f"Probability: {result['probability']:.0%}")
    print(f"Confidence: {result['confidence']:.0%}")
    print(f"Band: {result['confidence_breakdown']['probability_band']}")
    print(f"Edge: {result['edge_score']}/10 ({result['edge_tier']})")
