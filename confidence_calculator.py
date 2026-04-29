"""
Enhanced Confidence Calculator for UFC Predictions

Separates Confidence (prediction reliability) from Probability (win chance).
Confidence is based on data quality, model calibration, and uncertainty —
NOT just the win probability.
"""
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ConfidenceFactors:
    """Individual factors contributing to confidence score"""
    data_quality: float      # 0-100: completeness of fighter data
    sample_size: float       # 0-100: fight history depth
    recency: float           # 0-100: how recent the data is
    model_calibration: float # 0-100: historical accuracy at this probability
    prediction_certainty: float  # 0-100: model's internal certainty
    
    @property
    def overall(self) -> float:
        """Weighted overall confidence score"""
        weights = {
            'data_quality': 0.25,
            'sample_size': 0.20,
            'recency': 0.15,
            'model_calibration': 0.25,
            'prediction_certainty': 0.15
        }
        
        score = (
            self.data_quality * weights['data_quality'] +
            self.sample_size * weights['sample_size'] +
            self.recency * weights['recency'] +
            self.model_calibration * weights['model_calibration'] +
            self.prediction_certainty * weights['prediction_certainty']
        )
        
        return min(100, max(0, score))
    
    def to_dict(self) -> Dict:
        return {
            'data_quality': round(self.data_quality, 1),
            'sample_size': round(self.sample_size, 1),
            'recency': round(self.recency, 1),
            'model_calibration': round(self.model_calibration, 1),
            'prediction_certainty': round(self.prediction_certainty, 1),
            'overall': round(self.overall, 1)
        }


class ConfidenceCalculator:
    """
    Calculate prediction confidence independent of win probability.
    
    Confidence answers: "How reliable is this prediction?"
    NOT: "How likely is this fighter to win?"
    """
    
    def __init__(self, calibration_data: Dict = None):
        """
        Args:
            calibration_data: Historical model performance data
                Format: {predicted_prob: actual_accuracy}
                Example: {0.60: 0.58, 0.70: 0.72, ...}
        """
        self.calibration_data = calibration_data or {}
    
    def calculate_data_quality(self, fighter: Dict) -> float:
        """
        Assess completeness of fighter data (0-100).
        Higher score = more complete stats available.
        """
        if not fighter:
            return 0
        
        # Key stats that should be present
        key_stats = [
            'slpm', 'sig_strike_acc', 'sapm', 'sig_strike_def',
            'td_avg', 'td_acc', 'td_def', 'sub_avg',
            'record_wins', 'record_losses'
        ]
        
        present = sum(1 for stat in key_stats if fighter.get(stat) not in [None, 0, ''])
        base_score = (present / len(key_stats)) * 100
        
        # Bonus for recent fights data
        recent_fights = fighter.get('recent_fights', [])
        if len(recent_fights) >= 3:
            base_score += 10
        if len(recent_fights) >= 5:
            base_score += 5
        
        # Bonus for win methods data
        win_methods = fighter.get('win_methods', {})
        if win_methods:
            base_score += 5
        
        return min(100, base_score)
    
    def calculate_sample_size(self, fighter: Dict) -> float:
        """
        Assess fight history depth (0-100).
        More fights = more reliable data.
        """
        if not fighter:
            return 0
        
        wins = fighter.get('record_wins', 0) or 0
        losses = fighter.get('record_losses', 0) or 0
        total = wins + losses
        
        # Score based on total fights (UFC + pre-UFC)
        if total >= 20:
            return 100  # Veteran
        elif total >= 15:
            return 85
        elif total >= 10:
            return 70
        elif total >= 7:
            return 55
        elif total >= 4:
            return 40
        elif total >= 2:
            return 25
        else:
            return 10  # Debut or very limited data
    
    def calculate_recency(self, fighter: Dict) -> float:
        """
        Assess how recent the fighter's data is (0-100).
        Recent activity = more relevant data.
        """
        recent_fights = fighter.get('recent_fights', [])
        
        if not recent_fights:
            return 30  # No recent fight data
        
        # Check most recent fight
        most_recent = recent_fights[0]
        fight_date = most_recent.get('date', '')
        
        if not fight_date:
            return 50
        
        try:
            from datetime import datetime
            fight_dt = datetime.strptime(fight_date, '%Y-%m-%d')
            days_since = (datetime.now() - fight_dt).days
            
            # Score based on recency
            if days_since <= 90:    # Within 3 months
                return 100
            elif days_since <= 180: # Within 6 months
                return 90
            elif days_since <= 365: # Within 1 year
                return 80
            elif days_since <= 545: # Within 18 months
                return 65
            elif days_since <= 730: # Within 2 years
                return 50
            else:
                return max(20, 70 - (days_since - 730) / 30)  # Decline gradually
        except:
            return 50
    
    def calculate_model_calibration(self, predicted_prob: float) -> float:
        """
        Get historical accuracy for predictions at this probability level.
        
        If model says 60%, how often does it actually win at 60%?
        Perfect calibration = predicted_prob matches actual accuracy.
        """
        if not self.calibration_data:
            # No calibration data available - use default
            return 70
        
        # Find closest probability bucket
        closest_prob = min(self.calibration_data.keys(), 
                          key=lambda p: abs(p - predicted_prob))
        actual_accuracy = self.calibration_data[closest_prob]
        
        # Calibration score: how close is actual to predicted?
        calibration_error = abs(predicted_prob - actual_accuracy)
        
        # Convert to score (lower error = higher score)
        if calibration_error <= 0.02:
            return 100
        elif calibration_error <= 0.05:
            return 90
        elif calibration_error <= 0.10:
            return 75
        elif calibration_error <= 0.15:
            return 60
        else:
            return max(30, 100 - calibration_error * 200)
    
    def calculate_prediction_certainty(self, score_diff: float,
                                       fighter_a: Dict, fighter_b: Dict) -> float:
        """
        Calculate model's internal certainty based on score differential
        and data consistency.
        
        Higher score differential = more certain prediction
        """
        # Base certainty on score difference
        if score_diff >= 25:
            base_certainty = 95
        elif score_diff >= 20:
            base_certainty = 85
        elif score_diff >= 15:
            base_certainty = 75
        elif score_diff >= 10:
            base_certainty = 65
        elif score_diff >= 5:
            base_certainty = 55
        else:
            base_certainty = 45
        
        # Adjust for data quality balance
        quality_a = self.calculate_data_quality(fighter_a)
        quality_b = self.calculate_data_quality(fighter_b)
        quality_diff = abs(quality_a - quality_b)
        
        # If one fighter has much better data, reduce certainty
        if quality_diff > 30:
            base_certainty -= 10
        elif quality_diff > 20:
            base_certainty -= 5
        
        return max(20, min(100, base_certainty))
    
    def calculate_confidence(self, fighter_a: Dict, fighter_b: Dict,
                            predicted_prob: float, score_diff: float) -> ConfidenceFactors:
        """
        Calculate complete confidence breakdown for a prediction.
        
        Args:
            fighter_a: Fighter A data
            fighter_b: Fighter B data
            predicted_prob: Model's win probability (0-1)
            score_diff: Absolute difference in fighter scores
        
        Returns:
            ConfidenceFactors with all components and overall score
        """
        # Average data quality across both fighters
        quality_a = self.calculate_data_quality(fighter_a)
        quality_b = self.calculate_data_quality(fighter_b)
        avg_quality = (quality_a + quality_b) / 2
        
        # Average sample size
        sample_a = self.calculate_sample_size(fighter_a)
        sample_b = self.calculate_sample_size(fighter_b)
        avg_sample = (sample_a + sample_b) / 2
        
        # Average recency
        recency_a = self.calculate_recency(fighter_a)
        recency_b = self.calculate_recency(fighter_b)
        avg_recency = (recency_a + recency_b) / 2
        
        # Model calibration at this probability level
        calibration = self.calculate_model_calibration(predicted_prob)
        
        # Prediction certainty
        certainty = self.calculate_prediction_certainty(score_diff, fighter_a, fighter_b)
        
        return ConfidenceFactors(
            data_quality=avg_quality,
            sample_size=avg_sample,
            recency=avg_recency,
            model_calibration=calibration,
            prediction_certainty=certainty
        )
    
    def get_confidence_band(self, confidence_score: float) -> str:
        """Convert numeric confidence to qualitative band"""
        if confidence_score >= 80:
            return "High"
        elif confidence_score >= 60:
            return "Moderate"
        elif confidence_score >= 40:
            return "Low-Moderate"
        else:
            return "Low"


# Example calibration data (would be populated from historical results)
DEFAULT_CALIBRATION = {
    0.50: 0.48,  # Coin flip fights
    0.55: 0.52,
    0.60: 0.58,
    0.65: 0.63,
    0.70: 0.68,
    0.75: 0.74,
    0.80: 0.79,
    0.85: 0.84,
    0.90: 0.89,
}


if __name__ == "__main__":
    # Demo
    calculator = ConfidenceCalculator(DEFAULT_CALIBRATION)
    
    # Example fighter data
    fighter_a = {
        'name': 'Josh Emmett',
        'record_wins': 19,
        'record_losses': 4,
        'slpm': 4.23,
        'sig_strike_acc': 0.48,
        'sapm': 3.5,
        'sig_strike_def': 0.55,
        'td_avg': 1.2,
        'td_acc': 0.45,
        'td_def': 0.70,
        'sub_avg': 0.3,
        'recent_fights': [
            {'date': '2024-06-15', 'result': 'Win'},
            {'date': '2023-12-10', 'result': 'Loss'},
            {'date': '2023-08-20', 'result': 'Win'},
        ],
        'win_methods': {'ko_tko': 8, 'submissions': 2, 'decisions': 9}
    }
    
    fighter_b = {
        'name': 'Kevin Vallejos',
        'record_wins': 12,
        'record_losses': 3,
        'slpm': 3.8,
        'sig_strike_acc': 0.42,
        'sapm': 4.2,
        'sig_strike_def': 0.48,
        'td_avg': 0.8,
        'td_acc': 0.35,
        'td_def': 0.55,
        'sub_avg': 0.5,
        'recent_fights': [
            {'date': '2024-09-20', 'result': 'Win'},
            {'date': '2024-04-12', 'result': 'Win'},
        ],
        'win_methods': {'ko_tko': 5, 'submissions': 4, 'decisions': 3}
    }
    
    # Calculate confidence for a prediction
    predicted_prob = 0.63
    score_diff = 12.5
    
    confidence = calculator.calculate_confidence(
        fighter_a, fighter_b, predicted_prob, score_diff
    )
    
    print("=" * 60)
    print("Confidence Calculation Demo")
    print("=" * 60)
    print(f"\nPrediction: {fighter_a['name']} vs {fighter_b['name']}")
    print(f"Model Probability: {predicted_prob:.1%}")
    print(f"Score Differential: {score_diff:.1f}")
    
    print(f"\nConfidence Factors:")
    for factor, value in confidence.to_dict().items():
        if factor != 'overall':
            print(f"  {factor.replace('_', ' ').title()}: {value}%")
    
    print(f"\nOverall Confidence: {confidence.overall:.1f}%")
    print(f"Confidence Band: {calculator.get_confidence_band(confidence.overall)}")
