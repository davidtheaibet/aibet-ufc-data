"""
Calibrated Confidence Calculator for UFC Predictions

New Logic:
- Probability = raw model output (e.g., 63%)
- Confidence = calibrated accuracy at that probability band, adjusted for market conditions
- Edge = separate metric (0-10 scale), NOT mixed into confidence
"""
import json
import math
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


# Probability → Calibrated Confidence mapping (from historical data)
# Based on 292 analyzed fights
CALIBRATION_BINS = {
    (0.50, 0.55): 0.68,  # 50-55% prob → 68% actual accuracy
    (0.55, 0.58): 0.72,  # 55-58% prob → 72% actual accuracy
    (0.58, 1.00): 0.84,  # 58%+ prob → 84% actual accuracy (benchmark)
}

# Market alignment thresholds
MARKET_AGREEMENT_THRESHOLD = 0.05  # 5% difference = agreement


def get_calibrated_confidence(probability: float) -> float:
    """
    Map model probability to calibrated confidence based on historical accuracy.
    
    Args:
        probability: Model output probability (0-1)
    
    Returns:
        Calibrated confidence (0-1) based on historical performance at this band
    """
    for (min_p, max_p), calibrated in CALIBRATION_BINS.items():
        if min_p <= probability < max_p:
            return calibrated
    
    # Default to highest band if probability >= 58%
    return 0.84


def calculate_market_disagreement_penalty(
    model_prob: float,
    market_prob: float
) -> Tuple[float, str]:
    """
    Calculate penalty when market disagrees with model.
    
    Args:
        model_prob: Model probability (0-1)
        market_prob: Market probability (0-1, vig-free)
    
    Returns:
        Tuple of (penalty_amount, alignment_status)
    """
    diff = abs(model_prob - market_prob)
    
    # Determine alignment
    if diff <= MARKET_AGREEMENT_THRESHOLD:
        alignment = "aligned"
        penalty = 0.0
    elif model_prob > market_prob:
        # Model favors fighter more than market (positive edge)
        alignment = "against_market"
        penalty = 0.05  # 5% penalty for betting against market
    else:
        # Market favors fighter more than model (negative edge)
        alignment = "against_model"
        penalty = 0.08  # 8% penalty when market disagrees with us
    
    return penalty, alignment


def calculate_odds_gap_penalty(odds_a: float, odds_b: float) -> float:
    """
    Calculate penalty based on odds gap.
    Rule: Every $0.10 gap = -1% confidence
    
    Args:
        odds_a: Decimal odds for fighter A
        odds_b: Decimal odds for fighter B
    
    Returns:
        Penalty as decimal (0-1)
    """
    if not odds_a or not odds_b or odds_a <= 0 or odds_b <= 0:
        return 0.0
    
    gap = abs(odds_a - odds_b)
    
    # Every $0.10 = -1% confidence
    penalty = (gap / 0.10) * 0.01
    
    # Cap at 10% max penalty
    return min(penalty, 0.10)


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
        clamped to 0-100%
    
    Args:
        model_prob: Model output probability (0-1)
        market_prob: Market implied probability (0-1), optional
        market_odds_a: Decimal odds for fighter A, optional
        market_odds_b: Decimal odds for fighter B, optional
    
    Returns:
        Dictionary with confidence breakdown
    """
    # Step 1: Get calibrated confidence from probability band
    calibrated = get_calibrated_confidence(model_prob)
    
    # Step 2: Apply market disagreement penalty
    market_penalty = 0.0
    alignment = "neutral"
    
    if market_prob is not None:
        market_penalty, alignment = calculate_market_disagreement_penalty(
            model_prob, market_prob
        )
    
    # Step 3: Apply odds gap penalty
    odds_penalty = 0.0
    if market_odds_a and market_odds_b:
        odds_penalty = calculate_odds_gap_penalty(market_odds_a, market_odds_b)
    
    # Step 4: Calculate final confidence
    raw_confidence = calibrated - market_penalty - odds_penalty
    final_confidence = max(0.0, min(1.0, raw_confidence))
    
    return {
        "calibrated_base": round(calibrated, 3),
        "market_penalty": round(market_penalty, 3),
        "odds_penalty": round(odds_penalty, 3),
        "final_confidence": round(final_confidence, 3),
        "market_alignment": alignment,
        "probability_band": get_probability_band(model_prob)
    }


def get_probability_band(probability: float) -> str:
    """Get the probability band for display"""
    if probability < 0.55:
        return "50-55%"
    elif probability < 0.58:
        return "55-58%"
    else:
        return "58%+"


def get_confidence_tier(confidence: float) -> str:
    """Convert confidence to tier for UI"""
    if confidence >= 0.80:
        return "high"
    elif confidence >= 0.65:
        return "medium"
    elif confidence >= 0.50:
        return "low"
    else:
        return "very_low"


# Edge calculation (separate from confidence)
def calculate_edge_score(model_prob: float, market_prob: float) -> float:
    """
    Calculate edge score (0-10 scale).
    Completely separate from confidence calculation.
    
    Args:
        model_prob: Model probability (0-1)
        market_prob: Market probability (0-1)
    
    Returns:
        Edge score 0-10
    """
    edge = model_prob - market_prob  # -1 to +1
    
    # Scale to 0-10
    # edge of 0 = score 5 (neutral)
    # edge of +0.20 = score 7 (positive)
    # edge of -0.20 = score 3 (negative)
    score = 5 + (edge * 25)  # Scale: 0.20 edge = +5 points
    
    return max(0, min(10, score))


def get_edge_tier(edge_score: float) -> str:
    """Get edge tier for UI"""
    if edge_score >= 7.5:
        return "strong"
    elif edge_score >= 6:
        return "medium"
    elif edge_score >= 4:
        return "weak"
    else:
        return "negative"


# Main API function
def calculate_prediction_metrics(
    model_prob: float,
    market_prob: Optional[float] = None,
    market_odds_a: Optional[float] = None,
    market_odds_b: Optional[float] = None
) -> Dict:
    """
    Calculate all prediction metrics for the UI.
    
    Returns clean output matching spec:
    {
        "probability": 0.63,
        "confidence": 0.82,
        "edge_score": 6.5,
        "edge_tier": "medium",
        "market_alignment": "against"
    }
    """
    # Calculate confidence (with market adjustments)
    confidence_result = calculate_confidence(
        model_prob=model_prob,
        market_prob=market_prob,
        market_odds_a=market_odds_a,
        market_odds_b=market_odds_b
    )
    
    # Calculate edge (separate)
    edge_score = 5.0  # Neutral default
    if market_prob is not None:
        edge_score = calculate_edge_score(model_prob, market_prob)
    
    return {
        "probability": round(model_prob, 3),
        "confidence": confidence_result["final_confidence"],
        "confidence_breakdown": {
            "calibrated_base": confidence_result["calibrated_base"],
            "market_penalty": confidence_result["market_penalty"],
            "odds_penalty": confidence_result["odds_penalty"],
            "probability_band": confidence_result["probability_band"]
        },
        "edge_score": round(edge_score, 1),
        "edge_tier": get_edge_tier(edge_score),
        "market_alignment": confidence_result["market_alignment"]
    }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Calibrated Confidence Calculator")
    print("=" * 60)
    
    # Example 1: Model agrees with market
    print("\nExample 1: Model 63%, Market 60% (aligned)")
    result = calculate_prediction_metrics(
        model_prob=0.63,
        market_prob=0.60,
        market_odds_a=1.67,
        market_odds_b=2.50
    )
    print(f"  Probability: {result['probability']:.1%}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Edge Score: {result['edge_score']}")
    print(f"  Edge Tier: {result['edge_tier']}")
    print(f"  Market Alignment: {result['market_alignment']}")
    
    # Example 2: Model disagrees with market (Jack vs Carlos scenario)
    print("\nExample 2: Model favors Jack (63%), Market favors Carlos (55%)")
    # Model: Jack 63%, Carlos 37%
    # Market: Jack 45%, Carlos 55%
    result = calculate_prediction_metrics(
        model_prob=0.63,  # Model says Jack wins 63%
        market_prob=0.45,  # Market says Jack wins 45% (favors Carlos)
        market_odds_a=2.20,  # Jack odds
        market_odds_b=1.80   # Carlos odds
    )
    print(f"  Probability: {result['probability']:.1%}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Confidence Breakdown:")
    print(f"    - Calibrated Base: {result['confidence_breakdown']['calibrated_base']:.1%}")
    print(f"    - Market Penalty: -{result['confidence_breakdown']['market_penalty']:.1%}")
    print(f"    - Odds Penalty: -{result['confidence_breakdown']['odds_penalty']:.1%}")
    print(f"  Edge Score: {result['edge_score']}")
    print(f"  Edge Tier: {result['edge_tier']}")
    print(f"  Market Alignment: {result['market_alignment']}")
    
    # Example 3: High probability, market agrees
    print("\nExample 3: High confidence prediction (72%)")
    result = calculate_prediction_metrics(
        model_prob=0.72,
        market_prob=0.70,
        market_odds_a=1.43,
        market_odds_b=3.00
    )
    print(f"  Probability: {result['probability']:.1%}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Edge Score: {result['edge_score']}")
    print(f"  Edge Tier: {result['edge_tier']}")
    print(f"  Market Alignment: {result['market_alignment']}")
