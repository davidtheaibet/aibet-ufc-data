#!/usr/bin/env python3
"""
Enhanced UFC Fight Analysis Engine v2.0

Now includes:
- Market odds integration
- Vig-free implied probabilities
- Edge calculation (Model vs Market)
- Separate Confidence metric (reliability, not probability)

For Sean's system requirements.
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Import our new modules
from odds_integration import (
    MarketOdds, OddsManager, calculate_edge, 
    get_edge_rating, format_odds_for_display
)
from calibrated_confidence import (
    calculate_prediction_metrics,
    get_confidence_tier,
    calculate_edge_score,
    get_edge_tier as get_calibrated_edge_tier
)


@dataclass
class FightPrediction:
    """Complete prediction output for Sean's system"""
    # Fighter info
    fighter_a_name: str
    fighter_b_name: str
    fighter_a_record: str
    fighter_b_record: str
    
    # Model predictions
    model_prob_a: float  # 0-1
    model_prob_b: float  # 0-1
    predicted_winner: str
    
    # Confidence (reliability metric)
    confidence_score: float  # 0-100
    confidence_band: str  # Low/Moderate/High
    confidence_factors: Dict
    
    # Market data
    market_odds_a: Optional[float]
    market_odds_b: Optional[float]
    market_prob_a: Optional[float]  # Vig-free
    market_prob_b: Optional[float]  # Vig-free
    odds_source: Optional[str]
    
    # Edge calculation
    edge_a: Optional[float]  # Model - Market
    edge_b: Optional[float]
    edge_rating_a: Optional[str]
    edge_rating_b: Optional[str]
    
    # Fight analysis
    likely_method: str
    advantages: List[Dict]
    fighter_a_scores: Dict
    fighter_b_scores: Dict
    ai_reason: str  # Text explanation


class UFCAnalysisEngineV2:
    """
    Enhanced UFC Analysis Engine with Odds Integration
    
    Key changes for Sean's system:
    1. Probability = Model's win chance prediction
    2. Confidence = Prediction reliability (separate metric)
    3. Edge = Model vs Market comparison
    """
    
    def __init__(self, data_dir: str = None, calibration_data: Dict = None):
        if data_dir is None:
            data_dir = Path(__file__).parent
        else:
            data_dir = Path(data_dir)
        
        self.fighters = {}
        self.events = []
        self.fight_history = []
        self.upcoming_events = []
        
        # Initialize new components
        self.odds_manager = OddsManager()
        
        # Load calibration data from file if not provided
        if calibration_data is None:
            calibration_data = self._load_calibration_data(data_dir)
        
        self.confidence_calculator = ConfidenceCalculator(calibration_data)
        
        self._load_data(data_dir)
    
    def _load_calibration_data(self, data_dir: Path) -> Dict:
        """Load calibration data from JSON file"""
        calibration_file = data_dir / 'calibration_data.json'
        try:
            with open(calibration_file) as f:
                data = json.load(f)
                # Convert string keys to floats (JSON keys are always strings)
                calibration = data.get('calibration', {})
                return {float(k): v for k, v in calibration.items()}
        except FileNotFoundError:
            # Return empty dict - will use defaults from ConfidenceCalculator
            return {}
    
    def _load_data(self, data_dir: Path):
        """Load all JSON data files"""
        # Load fighters
        fighters_file = data_dir / 'fighters.json'
        if fighters_file.exists():
            with open(fighters_file) as f:
                data = json.load(f)
                for fighter in data.get('fighters', []):
                    self.fighters[fighter['name']] = fighter
        
        # Load upcoming events
        upcoming_file = data_dir / 'upcoming-events.json'
        if upcoming_file.exists():
            with open(upcoming_file) as f:
                data = json.load(f)
                self.upcoming_events = data.get('upcoming_events', [])
        
        # Load fight history
        history_file = data_dir / 'fight-history.json'
        if history_file.exists():
            with open(history_file) as f:
                data = json.load(f)
                self.fight_history = data.get('fights', [])
    
    def get_fighter(self, name: str) -> Optional[Dict]:
        """Get fighter by name (fuzzy match)"""
        # Exact match
        if name in self.fighters:
            return self.fighters[name]
        
        # Case-insensitive match
        name_lower = name.lower()
        for fighter_name, fighter in self.fighters.items():
            if fighter_name.lower() == name_lower:
                return fighter
        
        # Partial match
        for fighter_name, fighter in self.fighters.items():
            if name_lower in fighter_name.lower() or fighter_name.lower() in name_lower:
                return fighter
        
        return None
    
    def calculate_striking_score(self, fighter: Dict) -> float:
        """Calculate striking effectiveness score (0-100)"""
        slpm = fighter.get('slpm', 0) or 0
        accuracy = fighter.get('sig_strike_acc', 0) or 0
        defense = fighter.get('sig_strike_def', 0) or 0
        sapm = fighter.get('sapm', 0) or 0
        
        volume_score = min(slpm / 5.0 * 25, 25)
        accuracy_score = min(accuracy / 0.6 * 25, 25)
        defense_score = min(defense / 0.6 * 25, 25)
        chin_score = max(0, 25 - (sapm / 5.0 * 25))
        
        return volume_score + accuracy_score + defense_score + chin_score
    
    def calculate_grappling_score(self, fighter: Dict) -> float:
        """Calculate grappling effectiveness score (0-100)"""
        td_avg = fighter.get('td_avg', 0) or 0
        td_acc = fighter.get('td_acc', 0) or 0
        td_def = fighter.get('td_def', 0) or 0
        sub_avg = fighter.get('sub_avg', 0) or 0
        
        td_offense = min(td_avg / 3.0 * 25, 25)
        td_accuracy = min(td_acc / 0.5 * 25, 25)
        td_defense = min(td_def / 0.7 * 25, 25) if td_def else 15
        sub_threat = min(sub_avg / 1.5 * 25, 25)
        
        return td_offense + td_accuracy + td_defense + sub_threat
    
    def calculate_experience_score(self, fighter: Dict) -> float:
        """Calculate experience score (0-100)"""
        wins = fighter.get('record_wins', 0) or 0
        losses = fighter.get('record_losses', 0) or 0
        total = wins + losses + (fighter.get('record_draws', 0) or 0)
        
        if total == 0:
            return 0
        
        win_rate = wins / total
        exp_score = min(total / 30.0 * 50, 50)
        win_rate_score = min(win_rate / 0.8 * 50, 50)
        
        return exp_score + win_rate_score
    
    def calculate_form_score(self, fighter: Dict) -> float:
        """Calculate recent form score (0-100)"""
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
        """Calculate finish threat score (0-100)"""
        win_methods = fighter.get('win_methods', {})
        wins = fighter.get('record_wins', 0) or 0
        
        if wins == 0:
            return 0
        
        ko_tko = win_methods.get('ko_tko', 0)
        subs = win_methods.get('submissions', 0)
        
        ko_rate = ko_tko / wins
        sub_rate = subs / wins
        
        ko_score = min(ko_rate / 0.5 * 50, 50)
        sub_score = min(sub_rate / 0.4 * 50, 50)
        
        return ko_score + sub_score
    
    def _predict_finish_method(self, fighter_a: Dict, fighter_b: Dict,
                               a_finish: float, b_finish: float) -> str:
        """Predict likely finish method"""
        a_ko = fighter_a.get('win_methods', {}).get('ko_tko', 0)
        a_sub = fighter_a.get('win_methods', {}).get('submissions', 0)
        b_ko = fighter_b.get('win_methods', {}).get('ko_tko', 0)
        b_sub = fighter_b.get('win_methods', {}).get('submissions', 0)
        
        total_ko = a_ko + b_ko
        total_sub = a_sub + b_sub
        
        if total_ko > total_sub * 1.5:
            return 'KO/TKO'
        elif total_sub > total_ko * 1.5:
            return 'Submission'
        else:
            return 'Decision'
    
    def _identify_advantages(self, fighter_a: Dict, fighter_b: Dict,
                             diffs: Dict[str, float]) -> List[Dict]:
        """Identify key advantages for each fighter"""
        advantages = []
        
        for category, diff in diffs.items():
            if abs(diff) > 10:
                winner = fighter_a['name'] if diff > 0 else fighter_b['name']
                advantages.append({
                    'category': category,
                    'advantage_to': winner,
                    'margin': round(abs(diff), 1)
                })
        
        advantages.sort(key=lambda x: x['margin'], reverse=True)
        return advantages[:5]
    
    def _generate_ai_reason(self, fighter_a: Dict, fighter_b: Dict,
                           prediction: Dict, advantages: List[Dict]) -> str:
        """Generate text explanation for the prediction"""
        winner = prediction['winner']
        winner_data = fighter_a if winner == fighter_a['name'] else fighter_b
        loser_data = fighter_b if winner == fighter_a['name'] else fighter_a
        
        reasons = []
        
        # Add reasons based on advantages
        for adv in advantages[:3]:
            if adv['advantage_to'] == winner:
                reasons.append(f"{adv['category'].title()} advantage (+{adv['margin']:.0f})")
        
        # Add finish threat context
        finish_rate = winner_data.get('finish_rate', 0)
        if finish_rate > 70:
            reasons.append(f"High finish rate ({finish_rate:.0f}%)")
        
        # Add experience context
        winner_fights = winner_data.get('record_wins', 0) + winner_data.get('record_losses', 0)
        loser_fights = loser_data.get('record_wins', 0) + loser_data.get('record_losses', 0)
        if winner_fights > loser_fights + 5:
            reasons.append(f"Experience edge ({winner_fights} vs {loser_fights} fights)")
        
        if reasons:
            return f"{winner} favored due to: " + ", ".join(reasons)
        else:
            return f"Close matchup with slight edge to {winner}"
    
    def analyze_matchup(self, fighter_a_name: str, fighter_b_name: str,
                       market_odds: MarketOdds = None) -> FightPrediction:
        """
        Comprehensive matchup analysis with odds integration.
        
        Args:
            fighter_a_name: Name of first fighter
            fighter_b_name: Name of second fighter
            market_odds: Optional MarketOdds object with bookmaker odds
        
        Returns:
            FightPrediction with all metrics for Sean's system
        """
        fighter_a = self.get_fighter(fighter_a_name)
        fighter_b = self.get_fighter(fighter_b_name)
        
        if not fighter_a or not fighter_b:
            raise ValueError(f"Fighter not found: {fighter_a_name} or {fighter_b_name}")
        
        # Calculate all scores
        a_striking = self.calculate_striking_score(fighter_a)
        b_striking = self.calculate_striking_score(fighter_b)
        
        a_grappling = self.calculate_grappling_score(fighter_a)
        b_grappling = self.calculate_grappling_score(fighter_b)
        
        a_experience = self.calculate_experience_score(fighter_a)
        b_experience = self.calculate_experience_score(fighter_b)
        
        a_form = self.calculate_form_score(fighter_a)
        b_form = self.calculate_form_score(fighter_b)
        
        a_finish = self.calculate_finish_threat(fighter_a)
        b_finish = self.calculate_finish_threat(fighter_b)
        
        # Calculate overall scores with weights
        weights = {
            'striking': 0.25,
            'grappling': 0.25,
            'experience': 0.20,
            'form': 0.20,
            'finish': 0.10
        }
        
        a_total = (
            a_striking * weights['striking'] +
            a_grappling * weights['grappling'] +
            a_experience * weights['experience'] +
            a_form * weights['form'] +
            a_finish * weights['finish']
        )
        
        b_total = (
            b_striking * weights['striking'] +
            b_grappling * weights['grappling'] +
            b_experience * weights['experience'] +
            b_form * weights['form'] +
            b_finish * weights['finish']
        )
        
        # Calculate win probability using sigmoid
        diff = a_total - b_total
        prob_a = 1 / (1 + math.exp(-diff / 15))
        prob_b = 1 - prob_a
        
        # Calculate CONFIDENCE (reliability, not probability)
        confidence = self.confidence_calculator.calculate_confidence(
            fighter_a, fighter_b, prob_a, abs(diff)
        )
        
        # Determine winner
        winner = fighter_a['name'] if prob_a > 0.5 else fighter_b['name']
        
        # Get market data and calculate edge
        market_prob_a = None
        market_prob_b = None
        edge_a = None
        edge_b = None
        edge_rating_a = None
        edge_rating_b = None
        
        if market_odds:
            market_prob_a, market_prob_b = market_odds.get_vig_free_probabilities()
            edge_a = calculate_edge(prob_a, market_prob_a)
            edge_b = calculate_edge(prob_b, market_prob_b)
            edge_rating_a = get_edge_rating(edge_a)
            edge_rating_b = get_edge_rating(edge_b)
        
        # Identify advantages
        advantages = self._identify_advantages(fighter_a, fighter_b, {
            'striking': a_striking - b_striking,
            'grappling': a_grappling - b_grappling,
            'experience': a_experience - b_experience,
            'form': a_form - b_form,
            'finish': a_finish - b_finish
        })
        
        # Predict finish method
        likely_method = self._predict_finish_method(fighter_a, fighter_b, a_finish, b_finish)
        
        # Generate AI reason
        ai_reason = self._generate_ai_reason(fighter_a, fighter_b, 
                                            {'winner': winner}, advantages)
        
        return FightPrediction(
            fighter_a_name=fighter_a['name'],
            fighter_b_name=fighter_b['name'],
            fighter_a_record=f"{fighter_a.get('record_wins', 0)}-{fighter_a.get('record_losses', 0)}-{fighter_a.get('record_draws', 0)}",
            fighter_b_record=f"{fighter_b.get('record_wins', 0)}-{fighter_b.get('record_losses', 0)}-{fighter_b.get('record_draws', 0)}",
            model_prob_a=round(prob_a, 3),
            model_prob_b=round(prob_b, 3),
            predicted_winner=winner,
            confidence_score=round(confidence.overall, 1),
            confidence_band=self.confidence_calculator.get_confidence_band(confidence.overall),
            confidence_factors=confidence.to_dict(),
            market_odds_a=market_odds.odds_a if market_odds else None,
            market_odds_b=market_odds.odds_b if market_odds else None,
            market_prob_a=round(market_prob_a, 3) if market_prob_a else None,
            market_prob_b=round(market_prob_b, 3) if market_prob_b else None,
            odds_source=market_odds.source if market_odds else None,
            edge_a=round(edge_a, 3) if edge_a is not None else None,
            edge_b=round(edge_b, 3) if edge_b is not None else None,
            edge_rating_a=edge_rating_a,
            edge_rating_b=edge_rating_b,
            likely_method=likely_method,
            advantages=advantages,
            fighter_a_scores={
                'striking': round(a_striking, 1),
                'grappling': round(a_grappling, 1),
                'experience': round(a_experience, 1),
                'form': round(a_form, 1),
                'finish_threat': round(a_finish, 1),
                'overall': round(a_total, 1)
            },
            fighter_b_scores={
                'striking': round(b_striking, 1),
                'grappling': round(b_grappling, 1),
                'experience': round(b_experience, 1),
                'form': round(b_form, 1),
                'finish_threat': round(b_finish, 1),
                'overall': round(b_total, 1)
            },
            ai_reason=ai_reason
        )
    
    def analyze_matchup_to_dict(self, fighter_a: str, fighter_b: str,
                                market_odds: MarketOdds = None) -> Dict:
        """Analyze matchup and return as dictionary for JSON serialization"""
        prediction = self.analyze_matchup(fighter_a, fighter_b, market_odds)
        return {
            'fighter_a': {
                'name': prediction.fighter_a_name,
                'record': prediction.fighter_a_record,
                'scores': prediction.fighter_a_scores
            },
            'fighter_b': {
                'name': prediction.fighter_b_name,
                'record': prediction.fighter_b_record,
                'scores': prediction.fighter_b_scores
            },
            'prediction': {
                'winner': prediction.predicted_winner,
                'model_probability': {
                    'fighter_a': f"{prediction.model_prob_a:.1%}",
                    'fighter_b': f"{prediction.model_prob_b:.1%}"
                },
                'confidence': {
                    'score': prediction.confidence_score,
                    'band': prediction.confidence_band,
                    'factors': prediction.confidence_factors
                },
                'likely_method': prediction.likely_method,
                'ai_reason': prediction.ai_reason
            },
            'market': {
                'odds': {
                    'fighter_a': format_odds_for_display(prediction.market_odds_a) if prediction.market_odds_a else None,
                    'fighter_b': format_odds_for_display(prediction.market_odds_b) if prediction.market_odds_b else None,
                    'source': prediction.odds_source
                },
                'implied_probability': {
                    'fighter_a': f"{prediction.market_prob_a:.1%}" if prediction.market_prob_a else None,
                    'fighter_b': f"{prediction.market_prob_b:.1%}" if prediction.market_prob_b else None
                }
            },
            'edge': {
                'fighter_a': {
                    'value': f"{prediction.edge_a:+.1%}" if prediction.edge_a is not None else None,
                    'rating': prediction.edge_rating_a
                },
                'fighter_b': {
                    'value': f"{prediction.edge_b:+.1%}" if prediction.edge_b is not None else None,
                    'rating': prediction.edge_rating_b
                }
            },
            'advantages': prediction.advantages
        }


def main():
    """Demo the enhanced analysis engine"""
    print("🥊 UFC Analysis Engine v2.0 - Demo\n")
    
    engine = UFCAnalysisEngineV2()
    
    # Example with market odds
    market_odds = MarketOdds(
        fighter_a="Josh Emmett",
        fighter_b="Kevin Vallejos",
        odds_a=1.80,
        odds_b=2.20,
        source="Ladbrokes",
        timestamp="2026-03-15T10:00:00"
    )
    
    print("=" * 70)
    print("Example: Josh Emmett vs Kevin Vallejos")
    print("=" * 70)
    
    result = engine.analyze_matchup("Josh Emmett", "Kevin Vallejos", market_odds)
    output = engine.analyze_matchup_to_dict("Josh Emmett", "Kevin Vallejos", market_odds)
    
    # Pretty print the result
    print(json.dumps(output, indent=2))
    
    print("\n" + "=" * 70)
    print("Key Metrics Summary:")
    print("=" * 70)
    print(f"Predicted Winner: {result.predicted_winner}")
    print(f"Model Probability: {result.model_prob_a:.1%} - {result.model_prob_b:.1%}")
    print(f"Confidence: {result.confidence_score:.1f}% ({result.confidence_band})")
    print(f"Market Probability: {result.market_prob_a:.1%} - {result.market_prob_b:.1%}")
    print(f"Edge: {result.edge_a:+.1%} ({result.edge_rating_a})")
    print(f"Likely Method: {result.likely_method}")


if __name__ == '__main__':
    main()
