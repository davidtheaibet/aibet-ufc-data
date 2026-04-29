"""
Model Calibration Tracker for UFC Predictions

Analyzes historical predictions vs actual outcomes to build
calibration data for confidence scoring.

Calibration answers: When the model predicts X%, how often does it actually win?
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from dataclasses import dataclass

# Import the analysis engine
from analysis_engine_v2 import UFCAnalysisEngineV2


@dataclass
class CalibrationBucket:
    """Tracks predictions within a probability range"""
    min_prob: float
    max_prob: float
    predictions: int = 0
    correct: int = 0
    
    @property
    def actual_accuracy(self) -> float:
        if self.predictions == 0:
            return (self.min_prob + self.max_prob) / 2
        return self.correct / self.predictions
    
    @property
    def expected_prob(self) -> float:
        return (self.min_prob + self.max_prob) / 2
    
    def to_dict(self) -> Dict:
        return {
            'range': f"{self.min_prob:.0%}-{self.max_prob:.0%}",
            'expected': round(self.expected_prob, 3),
            'actual': round(self.actual_accuracy, 3),
            'predictions': self.predictions,
            'correct': self.correct,
            'calibration_error': round(abs(self.expected_prob - self.actual_accuracy), 3)
        }


class CalibrationTracker:
    """
    Track model calibration over time.
    
    Bins predictions into buckets and tracks actual win rates.
    """
    
    def __init__(self, bucket_size: float = 0.05):
        """
        Args:
            bucket_size: Size of probability buckets (default 5%)
        """
        self.bucket_size = bucket_size
        self.buckets: Dict[int, CalibrationBucket] = {}
        self._initialize_buckets()
        self.history: List[Dict] = []
    
    def _initialize_buckets(self):
        """Create probability buckets from 50% to 100%"""
        num_buckets = int(0.5 / self.bucket_size)  # 50% to 100%
        for i in range(num_buckets):
            min_p = 0.5 + (i * self.bucket_size)
            max_p = min_p + self.bucket_size
            self.buckets[i] = CalibrationBucket(min_p, max_p)
    
    def _get_bucket_index(self, probability: float) -> int:
        """Get bucket index for a probability"""
        if probability < 0.5:
            probability = 1 - probability  # Mirror for underdogs
        
        idx = int((probability - 0.5) / self.bucket_size)
        return min(idx, len(self.buckets) - 1)
    
    def record_prediction(self, predicted_prob: float, actual_result: bool,
                         fight_id: str = None, fighter_name: str = None):
        """
        Record a prediction outcome.
        
        Args:
            predicted_prob: Model's predicted probability (0-1)
            actual_result: True if prediction was correct
            fight_id: Optional fight identifier
            fighter_name: Optional fighter name
        """
        bucket_idx = self._get_bucket_index(predicted_prob)
        bucket = self.buckets[bucket_idx]
        
        bucket.predictions += 1
        if actual_result:
            bucket.correct += 1
        
        # Record in history
        self.history.append({
            'fight_id': fight_id,
            'fighter': fighter_name,
            'predicted_prob': round(predicted_prob, 3),
            'actual_result': actual_result,
            'bucket': bucket.range
        })
    
    def get_calibration_data(self) -> Dict[float, float]:
        """
        Get calibration data as {predicted_prob: actual_accuracy}
        
        Returns:
            Dictionary mapping probability levels to actual accuracy
        """
        calibration = {}
        for bucket in self.buckets.values():
            if bucket.predictions >= 5:  # Minimum sample size
                calibration[round(bucket.expected_prob, 2)] = round(bucket.actual_accuracy, 3)
        
        return calibration
    
    def get_calibration_report(self) -> Dict:
        """Get full calibration report"""
        buckets_report = [b.to_dict() for b in self.buckets.values() if b.predictions > 0]
        
        # Calculate overall calibration error
        total_error = sum(b['calibration_error'] for b in buckets_report)
        avg_error = total_error / len(buckets_report) if buckets_report else 0
        
        return {
            'summary': {
                'total_predictions': len(self.history),
                'overall_accuracy': sum(1 for h in self.history if h['actual_result']) / len(self.history) if self.history else 0,
                'average_calibration_error': round(avg_error, 3),
                'buckets_with_data': len(buckets_report)
            },
            'buckets': buckets_report,
            'calibration_data': self.get_calibration_data()
        }
    
    def save(self, filepath: str):
        """Save calibration data to file"""
        data = {
            'buckets': {k: {
                'min': v.min_prob,
                'max': v.max_prob,
                'predictions': v.predictions,
                'correct': v.correct
            } for k, v in self.buckets.items()},
            'history': self.history
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str):
        """Load calibration data from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Restore buckets
            for k, v in data['buckets'].items():
                idx = int(k)
                self.buckets[idx] = CalibrationBucket(
                    min_prob=v['min'],
                    max_prob=v['max'],
                    predictions=v['predictions'],
                    correct=v['correct']
                )
            
            # Restore history
            self.history = data.get('history', [])
        except FileNotFoundError:
            pass


def build_calibration_from_history(data_dir: str = None) -> CalibrationTracker:
    """
    Build calibration data from historical fights.
    
    This runs the model on past fights and compares predictions to actual outcomes.
    """
    if data_dir is None:
        data_dir = Path(__file__).parent
    else:
        data_dir = Path(data_dir)
    
    # Initialize
    engine = UFCAnalysisEngineV2(data_dir)
    tracker = CalibrationTracker(bucket_size=0.05)
    
    # Load fight history
    history_file = data_dir / 'fight-history.json'
    if not history_file.exists():
        print(f"Fight history not found: {history_file}")
        return tracker
    
    with open(history_file) as f:
        data = json.load(f)
        fights = data.get('fights', [])
    
    print(f"Building calibration from {len(fights)} historical fights...")
    
    processed = 0
    skipped = 0
    
    for fight in fights:
        fighter_a_name = fight.get('fighter_a_name')
        fighter_b_name = fight.get('fighter_b_name')
        winner_name = fight.get('winner_name')
        
        if not all([fighter_a_name, fighter_b_name, winner_name]):
            skipped += 1
            continue
        
        # Get fighters from database
        fighter_a = engine.get_fighter(fighter_a_name)
        fighter_b = engine.get_fighter(fighter_b_name)
        
        if not fighter_a or not fighter_b:
            skipped += 1
            continue
        
        try:
            # Run prediction (without market odds for historical)
            prediction = engine.analyze_matchup(fighter_a_name, fighter_b_name)
            
            # Determine if prediction was correct
            predicted_winner = prediction.predicted_winner
            was_correct = (predicted_winner == winner_name)
            
            # Get the predicted probability for the predicted winner
            if predicted_winner == fighter_a_name:
                predicted_prob = prediction.model_prob_a
            else:
                predicted_prob = prediction.model_prob_b
            
            # Record the outcome
            tracker.record_prediction(
                predicted_prob=predicted_prob,
                actual_result=was_correct,
                fight_id=fight.get('ufc_id'),
                fighter_name=predicted_winner
            )
            
            processed += 1
            
            if processed % 50 == 0:
                print(f"  Processed {processed} fights...")
                
        except Exception as e:
            skipped += 1
            continue
    
    print(f"\nComplete: {processed} fights processed, {skipped} skipped")
    
    return tracker


def generate_default_calibration() -> Dict[float, float]:
    """
    Generate conservative default calibration data.
    
    Used when insufficient historical data exists.
    Slightly regressed toward 50% to account for model uncertainty.
    """
    return {
        0.50: 0.50,  # Coin flip - no edge
        0.55: 0.53,  # Slight favorite
        0.60: 0.57,  # Moderate favorite
        0.65: 0.62,  # Solid favorite
        0.70: 0.67,  # Strong favorite
        0.75: 0.72,  # Heavy favorite
        0.80: 0.77,  # Dominant favorite
        0.85: 0.82,  # Overwhelming favorite
        0.90: 0.87,  # Near-certain
        0.95: 0.92,  # Almost guaranteed
    }


def main():
    """Build calibration data from historical fights"""
    print("=" * 60)
    print("UFC Model Calibration Builder")
    print("=" * 60)
    
    # Build from history
    tracker = build_calibration_from_history()
    
    # Get report
    report = tracker.get_calibration_report()
    
    print("\n" + "=" * 60)
    print("Calibration Report")
    print("=" * 60)
    
    summary = report['summary']
    print(f"\nTotal Predictions Analyzed: {summary['total_predictions']}")
    print(f"Overall Model Accuracy: {summary['overall_accuracy']:.1%}")
    print(f"Average Calibration Error: {summary['average_calibration_error']:.1%}")
    print(f"Buckets with Data: {summary['buckets_with_data']}")
    
    print("\nCalibration by Probability Bucket:")
    print("-" * 60)
    print(f"{'Range':<12} {'Expected':<10} {'Actual':<10} {'Error':<10} {'Samples':<10}")
    print("-" * 60)
    
    for bucket in report['buckets']:
        print(f"{bucket['range']:<12} {bucket['expected']:<10.1%} {bucket['actual']:<10.1%} {bucket['calibration_error']:<10.1%} {bucket['predictions']:<10}")
    
    # Save calibration data
    calibration_data = report['calibration_data']
    
    # If insufficient data, use defaults
    if len(calibration_data) < 5:
        print("\n⚠️  Insufficient historical data. Using conservative defaults.")
        calibration_data = generate_default_calibration()
    
    # Save to file
    output_file = Path(__file__).parent / 'calibration_data.json'
    with open(output_file, 'w') as f:
        json.dump({
            'calibration': calibration_data,
            'generated_from': 'historical_fights',
            'total_fights_analyzed': summary['total_predictions'],
            'timestamp': str(__import__('datetime').datetime.now())
        }, f, indent=2)
    
    print(f"\n✅ Calibration data saved to: {output_file}")
    
    # Print calibration data for copy-paste
    print("\n" + "=" * 60)
    print("Calibration Data (for confidence_calculator.py)")
    print("=" * 60)
    print("\nDEFAULT_CALIBRATION = {")
    for prob, actual in sorted(calibration_data.items()):
        print(f"    {prob:.2f}: {actual:.2f},  # Model predicts {prob:.0%}, actual {actual:.0%}")
    print("}")


if __name__ == "__main__":
    main()
