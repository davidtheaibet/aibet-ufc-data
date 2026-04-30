#!/usr/bin/env python3
"""
UFC Fight Analysis Engine v3.0 — Calibrated Confidence

New Logic:
- Probability = raw model output (e.g., 63%)
- Confidence = calibrated accuracy at probability band, adjusted for market
- Edge = separate 0-10 score, NOT mixed into confidence

Output format:
{
    "probability": 0.63,
    "confidence": 0.82,
    "edge_score": 6.5,
    "edge_tier": "medium",
    "market_alignment": "against"
}
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from odds_integration import MarketOdds, OddsManager, format_odds_for_display
from calibrated_confidence import calculate_prediction_metrics


class UFCAnalysisEngineV3:
    """
    UFC Analysis Engine with Calibrated Confidence
    
    Key changes:
    1. Probability = raw model output
    2. Confidence = calibrated accuracy (probability band → historical accuracy)
    3. Confidence adjusted for market disagreement and odds gap
    4. Edge = separate 0-10 score, completely independent
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent
        else:
            data_dir = Path(data_dir)
        
        self.fighters = {}
        self.events = []
        self._load_data(data_dir)
    
    def _load_data(self, data_dir: Path):
        """Load fighter data"""
        fighters_file = data_dir / 'fighters.json'
        if fighters_file.exists():
            with open(fighters_file) as f:
                data = json.load(f)
                for fighter in data.get('fighters', []):
                    self.fighters[fighter['name']] = fighter
    
    def get_fighter(self, name: str) -> Optional[Dict]:
        """Get fighter by name (fuzzy match)"""
        if name in self.fighters:
            return self.fighters[name]
        
        name_lower = name.lower()
        for fighter_name, fighter in self.fighters.items():
            if fighter_name.lower() == name_lower:
                return fighter
            if name_lower in fighter_name.lower() or fighter_name.lower() in name_lower:
                return fighter
        
        return None
    
    def calculate_striking_score(self, fighter: Dict) -> float:
        """Striking effectiveness (0-100)"""
        slpm = fighter.get('slpm', 0) or 0
        accuracy = fighter.get('sig_strike_acc', 0) or 0
        defense = fighter.get('sig_strike_def', 0) or 0
        sapm = fighter.get('sapm', 0) or 0
        
        volume = min(slpm / 5.0 * 25, 25)
        acc = min(accuracy / 0.6 * 25, 25)
        def_score = min(defense / 0.6 * 25, 25)
        chin = max(0, 25 - (sapm / 5.0 * 25))
        
        return volume + acc + def_score + chin
    
    def calculate_grappling_score(self, fighter: Dict) -> float:
        """Grappling effectiveness (0-100)"""
        td_avg = fighter.get('td_avg', 0) or 0
        td_acc = fighter.get('td_acc', 0) or 0
        td_def = fighter.get('td_def', 0) or 0
        sub_avg = fighter.get('sub_avg', 0) or 0
        
        td_off = min(td_avg / 3.0 * 25, 25)
        td_acc_score = min(td_acc / 0.5 * 25, 25)
        td_def_score = min(td_def / 0.7 * 25, 25) if td_def else 15
        sub_threat = min(sub_avg / 1.5 * 25, 25)
        
        return td_off + td_acc_score + td_def_score + sub_threat
    
    def calculate_experience_score(self, fighter: Dict) -> float:
        """Experience score (0-100)"""
        wins = fighter.get('record_wins', 0) or 0
        losses = fighter.get('record_losses', 0) or 0
        total = wins + losses
        
        if total == 0:
            return 0
        
        win_rate = wins / total
        exp = min(total / 30.0 * 50, 50)
        win_rate_score = min(win_rate / 0.8 * 50, 50)
        
        return exp + win_rate_score
    
    def calculate_form_score(self, fighter: Dict) -> float:
        """Recent form score (0-100)"""
        recent = fighter.get('recent_fights', [])
        if not recent:
            return 50
        
        score = 0
        weights = [0.35, 0.25, 0.20, 0.12, 0.08]
        
        for i, fight in enumerate(recent[:5]):
            weight = weights[i] if i < len(weights) else 0
            result = fight.get('result', '')
            
            if result == 'Win':
                score += 100 * weight
            elif result == 'Draw':
                score += 50 * weight
        
        return score
    
    def calculate_finish_threat(self, fighter: Dict) -> float:
        """Finish threat score (0-100)"""
        win_methods = fighter.get('win_methods', {})
        wins = fighter.get('record_wins', 0) or 0
        
        if wins == 0:
            return 0
        
        ko_rate = win_methods.get('ko_tko', 0) / wins
        sub_rate = win_methods.get('submissions', 0) / wins
        
        ko_score = min(ko_rate / 0.5 * 50, 50)
        sub_score = min(sub_rate / 0.4 * 50, 50)
        
        return ko_score + sub_score
    
    def analyze_matchup(self, fighter_a_name: str, fighter_b_name: str,
                       market_odds: MarketOdds = None) -> Dict:
        """
        Analyze fight with calibrated confidence.
        
        Returns output matching spec:
        {
            "probability": 0.63,
            "confidence": 0.82,
            "edge_score": 6.5,
            "edge_tier": "medium",
            "market_alignment": "against"
        }
        """
        fighter_a = self.get_fighter(fighter_a_name)
        fighter_b = self.get_fighter(fighter_b_name)
        
        if not fighter_a or not fighter_b:
            raise ValueError(f"Fighter not found: {fighter_a_name} or {fighter_b_name}")
        
        # Calculate fighter scores
        weights = {'striking': 0.25, 'grappling': 0.25, 'experience': 0.20, 'form': 0.20, 'finish': 0.10}
        
        a_scores = {
            'striking': self.calculate_striking_score(fighter_a),
            'grappling': self.calculate_grappling_score(fighter_a),
            'experience': self.calculate_experience_score(fighter_a),
            'form': self.calculate_form_score(fighter_a),
            'finish': self.calculate_finish_threat(fighter_a)
        }
        
        b_scores = {
            'striking': self.calculate_striking_score(fighter_b),
            'grappling': self.calculate_grappling_score(fighter_b),
            'experience': self.calculate_experience_score(fighter_b),
            'form': self.calculate_form_score(fighter_b),
            'finish': self.calculate_finish_threat(fighter_b)
        }
        
        a_total = sum(a_scores[k] * weights[k] for k in weights)
        b_total = sum(b_scores[k] * weights[k] for k in weights)
        
        # Calculate probability using sigmoid
        diff = a_total - b_total
        prob_a = 1 / (1 + math.exp(-diff / 15))
        prob_b = 1 - prob_a
        
        # Determine winner
        winner = fighter_a['name'] if prob_a > 0.5 else fighter_b['name']
        winner_prob = prob_a if prob_a > 0.5 else prob_b
        
        # Get market data
        market_prob_a = None
        market_prob_b = None
        market_odds_a = None
        market_odds_b = None
        
        if market_odds:
            market_prob_a, market_prob_b = market_odds.get_vig_free_probabilities()
            market_odds_a = market_odds.odds_a
            market_odds_b = market_odds.odds_b
            # Use winner's market prob for confidence calc
            market_prob_for_winner = market_prob_a if winner == fighter_a['name'] else market_prob_b
        else:
            market_prob_for_winner = None
        
        # Calculate calibrated confidence and edge
        metrics = calculate_prediction_metrics(
            model_prob=winner_prob,
            market_prob=market_prob_for_winner,
            market_odds_a=market_odds_a,
            market_odds_b=market_odds_b
        )
        
        return {
            # Core output
            "probability": metrics['probability'],
            "confidence": metrics['confidence'],
            "edge_score": metrics['edge_score'],
            "edge_tier": metrics['edge_tier'],
            "market_alignment": metrics['market_alignment'],
            
            # Extended info
            "predicted_winner": winner,
            "confidence_breakdown": metrics['confidence_breakdown'],
            
            # Fighter details
            "fighter_a": {
                "name": fighter_a['name'],
                "record": f"{fighter_a.get('record_wins', 0)}-{fighter_a.get('record_losses', 0)}-{fighter_a.get('record_draws', 0)}",
                "probability": round(prob_a, 3),
                "scores": {k: round(v, 1) for k, v in a_scores.items()}
            },
            "fighter_b": {
                "name": fighter_b['name'],
                "record": f"{fighter_b.get('record_wins', 0)}-{fighter_b.get('record_losses', 0)}-{fighter_b.get('record_draws', 0)}",
                "probability": round(prob_b, 3),
                "scores": {k: round(v, 1) for k, v in b_scores.items()}
            },
            
            # Market data
            "market": {
                "odds_a": format_odds_for_display(market_odds_a) if market_odds else None,
                "odds_b": format_odds_for_display(market_odds_b) if market_odds else None,
                "implied_prob_a": f"{market_prob_a:.1%}" if market_prob_a else None,
                "implied_prob_b": f"{market_prob_b:.1%}" if market_prob_b else None
            } if market_odds else None
        }


def main():
    """Demo the calibrated confidence system"""
    print("=" * 70)
    print("UFC Analysis Engine v3.0 — Calibrated Confidence Demo")
    print("=" * 70)
    
    engine = UFCAnalysisEngineV3()
    
    # Example: Jack vs Carlos scenario
    # Model favors Jack, Market favors Carlos
    print("\nScenario: Model favors Jack (63%), Market favors Carlos")
    print("-" * 70)
    
    market_odds = MarketOdds(
        fighter_a="Josh Emmett",  # Stand-in for Jack
        fighter_b="Kevin Vallejos",  # Stand-in for Carlos
        odds_a=2.20,  # Jack odds (underdog)
        odds_b=1.80,  # Carlos odds (favorite)
        source="Ladbrokes",
        timestamp="2026-04-30T10:00:00"
    )
    
    result = engine.analyze_matchup("Josh Emmett", "Kevin Vallejos", market_odds)
    
    print(f"\nPredicted Winner: {result['predicted_winner']}")
    print(f"\nCore Output:")
    print(f"  Probability: {result['probability']:.1%}")
    print(f"  Confidence: {result['confidence']:.1%}")
    print(f"  Edge Score: {result['edge_score']}")
    print(f"  Edge Tier: {result['edge_tier']}")
    print(f"  Market Alignment: {result['market_alignment']}")
    
    print(f"\nConfidence Breakdown:")
    cb = result['confidence_breakdown']
    print(f"  Calibrated Base: {cb['calibrated_base']:.1%}")
    print(f"  Market Penalty: -{cb['market_penalty']:.1%}")
    print(f"  Odds Penalty: -{cb['odds_penalty']:.1%}")
    print(f"  Probability Band: {cb['probability_band']}")
    
    print(f"\nFighter Probabilities:")
    print(f"  {result['fighter_a']['name']}: {result['fighter_a']['probability']:.1%}")
    print(f"  {result['fighter_b']['name']}: {result['fighter_b']['probability']:.1%}")
    
    print("\n" + "=" * 70)
    print("UI Display:")
    print("=" * 70)
    print(f"Probability: {result['probability']:.0%}")
    print(f"Confidence: ~{result['confidence']:.0%}")
    print(f"Edge: {result['edge_score']}/10 ({result['edge_tier']})")


if __name__ == '__main__':
    main()
