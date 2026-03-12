#!/usr/bin/env python3
"""
Enhanced UFC Fight Analysis Engine
Analyzes fighter matchups using comprehensive statistics from the UFC database
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class FighterProfile:
    """Comprehensive fighter profile for analysis"""
    id: int
    name: str
    weight_class: str
    record_wins: int
    record_losses: int
    record_draws: int
    height: str
    reach: str
    stance: str
    slpm: float  # Significant strikes landed per minute
    sig_strike_acc: float
    sapm: float  # Significant strikes absorbed per minute
    sig_strike_def: float
    td_avg: float  # Takedown average
    td_acc: float
    td_def: float
    sub_avg: float  # Submission average
    win_methods: Dict[str, int]
    finish_rate: float
    win_rate: float
    recent_fights: List[Dict]
    
    @property
    def total_fights(self) -> int:
        return self.record_wins + self.record_losses + self.record_draws
    
    @property
    def striking_defense_ratio(self) -> float:
        """Ratio of strikes landed vs absorbed"""
        if self.sapm == 0:
            return self.slpm
        return self.slpm / self.sapm if self.sapm > 0 else 0

class UFCAnalysisEngine:
    """
    Enhanced UFC Fight Analysis Engine
    
    Uses comprehensive fighter statistics to predict fight outcomes
    and provide detailed matchup analysis.
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent
        else:
            data_dir = Path(data_dir)
        
        self.fighters = {}
        self.events = []
        self.fight_history = []
        self.upcoming_events = []
        
        self._load_data(data_dir)
    
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
        """
        Calculate striking effectiveness score (0-100)
        Based on: volume, accuracy, defense, and power
        """
        slpm = fighter.get('slpm', 0) or 0
        accuracy = fighter.get('sig_strike_acc', 0) or 0
        defense = fighter.get('sig_strike_def', 0) or 0
        sapm = fighter.get('sapm', 0) or 0
        
        # Volume score (normalized to ~5 SLpM being elite)
        volume_score = min(slpm / 5.0 * 25, 25)
        
        # Accuracy score (normalized to ~60% being elite)
        accuracy_score = min(accuracy / 0.6 * 25, 25)
        
        # Defense score (normalized to ~60% being elite)
        defense_score = min(defense / 0.6 * 25, 25)
        
        # Chin/durability score (inverse of strikes absorbed)
        chin_score = max(0, 25 - (sapm / 5.0 * 25))
        
        return volume_score + accuracy_score + defense_score + chin_score
    
    def calculate_grappling_score(self, fighter: Dict) -> float:
        """
        Calculate grappling effectiveness score (0-100)
        Based on: takedown offense/defense and submission threat
        """
        td_avg = fighter.get('td_avg', 0) or 0
        td_acc = fighter.get('td_acc', 0) or 0
        td_def = fighter.get('td_def', 0) or 0
        sub_avg = fighter.get('sub_avg', 0) or 0
        
        # Takedown offense (normalized to ~3 TD avg being elite)
        td_offense = min(td_avg / 3.0 * 25, 25)
        
        # Takedown accuracy (normalized to ~50% being elite)
        td_accuracy = min(td_acc / 0.5 * 25, 25)
        
        # Takedown defense (normalized to ~70% being elite)
        td_defense = min(td_def / 0.7 * 25, 25) if td_def else 15
        
        # Submission threat (normalized to ~1.5 sub avg being elite)
        sub_threat = min(sub_avg / 1.5 * 25, 25)
        
        return td_offense + td_accuracy + td_defense + sub_threat
    
    def calculate_experience_score(self, fighter: Dict) -> float:
        """
        Calculate experience score (0-100)
        Based on: total fights, win rate, and quality of competition
        """
        wins = fighter.get('record_wins', 0) or 0
        losses = fighter.get('record_losses', 0) or 0
        total = wins + losses + (fighter.get('record_draws', 0) or 0)
        
        if total == 0:
            return 0
        
        win_rate = wins / total
        
        # Experience points (normalized to ~30 fights being veteran)
        exp_score = min(total / 30.0 * 50, 50)
        
        # Win rate score (normalized to ~80% being elite)
        win_rate_score = min(win_rate / 0.8 * 50, 50)
        
        return exp_score + win_rate_score
    
    def calculate_form_score(self, fighter: Dict) -> float:
        """
        Calculate recent form score (0-100)
        Based on last 5 fights
        """
        recent = fighter.get('recent_fights', [])
        if not recent:
            return 50  # Neutral if no data
        
        score = 0
        weights = [0.35, 0.25, 0.20, 0.12, 0.08]  # More weight on recent fights
        
        for i, fight in enumerate(recent[:5]):
            weight = weights[i] if i < len(weights) else 0
            result = fight.get('result', '')
            
            if result == 'Win':
                score += 100 * weight
            elif result == 'Draw':
                score += 50 * weight
            # Loss = 0
        
        return score
    
    def calculate_finish_threat(self, fighter: Dict) -> float:
        """
        Calculate finish threat score (0-100)
        Based on KO/TKO and submission rates
        """
        win_methods = fighter.get('win_methods', {})
        wins = fighter.get('record_wins', 0) or 0
        
        if wins == 0:
            return 0
        
        ko_tko = win_methods.get('ko_tko', 0)
        subs = win_methods.get('submissions', 0)
        
        ko_rate = ko_tko / wins
        sub_rate = subs / wins
        
        # KO threat (normalized to ~50% KO rate being elite)
        ko_score = min(ko_rate / 0.5 * 50, 50)
        
        # Sub threat (normalized to ~40% sub rate being elite)
        sub_score = min(sub_rate / 0.4 * 50, 50)
        
        return ko_score + sub_score
    
    def analyze_matchup(self, fighter_a_name: str, fighter_b_name: str) -> Dict:
        """
        Comprehensive matchup analysis between two fighters
        
        Returns detailed breakdown with prediction confidence
        """
        fighter_a = self.get_fighter(fighter_a_name)
        fighter_b = self.get_fighter(fighter_b_name)
        
        if not fighter_a or not fighter_b:
            return {
                'error': 'One or both fighters not found in database',
                'fighter_a_found': fighter_a is not None,
                'fighter_b_found': fighter_b is not None
            }
        
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
        
        # Calculate win probability using sigmoid function
        diff = a_total - b_total
        prob_a = 1 / (1 + math.exp(-diff / 15))
        prob_b = 1 - prob_a
        
        # Determine confidence level
        confidence = self._calculate_confidence(abs(diff), fighter_a, fighter_b)
        
        # Determine likely finish method
        likely_method = self._predict_finish_method(fighter_a, fighter_b, a_finish, b_finish)
        
        return {
            'fighter_a': {
                'name': fighter_a['name'],
                'record': f"{fighter_a.get('record_wins', 0)}-{fighter_a.get('record_losses', 0)}-{fighter_a.get('record_draws', 0)}",
                'scores': {
                    'striking': round(a_striking, 1),
                    'grappling': round(a_grappling, 1),
                    'experience': round(a_experience, 1),
                    'form': round(a_form, 1),
                    'finish_threat': round(a_finish, 1),
                    'overall': round(a_total, 1)
                }
            },
            'fighter_b': {
                'name': fighter_b['name'],
                'record': f"{fighter_b.get('record_wins', 0)}-{fighter_b.get('record_losses', 0)}-{fighter_b.get('record_draws', 0)}",
                'scores': {
                    'striking': round(b_striking, 1),
                    'grappling': round(b_grappling, 1),
                    'experience': round(b_experience, 1),
                    'form': round(b_form, 1),
                    'finish_threat': round(b_finish, 1),
                    'overall': round(b_total, 1)
                }
            },
            'prediction': {
                'winner': fighter_a['name'] if prob_a > 0.5 else fighter_b['name'],
                'confidence': confidence,
                'probability_a': round(prob_a * 100, 1),
                'probability_b': round(prob_b * 100, 1),
                'likely_method': likely_method
            },
            'advantages': self._identify_advantages(fighter_a, fighter_b, {
                'striking': a_striking - b_striking,
                'grappling': a_grappling - b_grappling,
                'experience': a_experience - b_experience,
                'form': a_form - b_form,
                'finish': a_finish - b_finish
            })
        }
    
    def _calculate_confidence(self, score_diff: float, fighter_a: Dict, fighter_b: Dict) -> str:
        """Calculate prediction confidence level"""
        # Check data quality
        a_data_quality = self._assess_data_quality(fighter_a)
        b_data_quality = self._assess_data_quality(fighter_b)
        
        avg_quality = (a_data_quality + b_data_quality) / 2
        
        # Adjust confidence based on score difference and data quality
        if score_diff > 20 and avg_quality > 0.7:
            return 'High'
        elif score_diff > 10 and avg_quality > 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _assess_data_quality(self, fighter: Dict) -> float:
        """Assess the quality/quantity of fighter data"""
        score = 0
        total = 0
        
        # Check for key stats
        checks = [
            (fighter.get('slpm'), 'slpm'),
            (fighter.get('sig_strike_acc'), 'accuracy'),
            (fighter.get('td_avg'), 'takedowns'),
            (fighter.get('recent_fights'), 'recent fights')
        ]
        
        for value, _ in checks:
            total += 1
            if value and (isinstance(value, list) or value > 0):
                score += 1
        
        # Check fight record depth
        total_fights = fighter.get('record_wins', 0) + fighter.get('record_losses', 0)
        if total_fights >= 10:
            score += 1
        total += 1
        
        return score / total if total > 0 else 0
    
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
        
        # Sort by margin
        advantages.sort(key=lambda x: x['margin'], reverse=True)
        return advantages[:5]  # Top 5 advantages
    
    def analyze_upcoming_event(self, event_id: str) -> Dict:
        """Analyze all fights in an upcoming event"""
        event = None
        for e in self.upcoming_events:
            if e['id'] == event_id:
                event = e
                break
        
        if not event:
            return {'error': f'Event {event_id} not found'}
        
        predictions = []
        
        for fight in event.get('main_card', []):
            fighter_a = fight['fighter_a']['name']
            fighter_b = fight['fighter_b']['name']
            
            analysis = self.analyze_matchup(fighter_a, fighter_b)
            predictions.append({
                'fight': f"{fighter_a} vs {fighter_b}",
                'weight_class': fight['weight_class'],
                'analysis': analysis
            })
        
        return {
            'event': event['name'],
            'date': event['date'],
            'location': event['location'],
            'predictions': predictions
        }
    
    def get_fighter_profile(self, name: str) -> Dict:
        """Get detailed fighter profile with analysis"""
        fighter = self.get_fighter(name)
        
        if not fighter:
            return {'error': f'Fighter {name} not found'}
        
        return {
            'profile': fighter,
            'analysis': {
                'striking_score': round(self.calculate_striking_score(fighter), 1),
                'grappling_score': round(self.calculate_grappling_score(fighter), 1),
                'experience_score': round(self.calculate_experience_score(fighter), 1),
                'form_score': round(self.calculate_form_score(fighter), 1),
                'finish_threat': round(self.calculate_finish_threat(fighter), 1)
            },
            'strengths': self._identify_strengths(fighter),
            'weaknesses': self._identify_weaknesses(fighter)
        }
    
    def _identify_strengths(self, fighter: Dict) -> List[str]:
        """Identify fighter strengths"""
        strengths = []
        
        if fighter.get('slpm', 0) > 4:
            strengths.append('High volume striking')
        if fighter.get('sig_strike_acc', 0) > 0.5:
            strengths.append('Accurate striker')
        if fighter.get('sig_strike_def', 0) > 0.6:
            strengths.append('Good striking defense')
        if fighter.get('td_avg', 0) > 2:
            strengths.append('Strong takedown game')
        if fighter.get('td_def', 0) > 0.7:
            strengths.append('Good takedown defense')
        if fighter.get('sub_avg', 0) > 1:
            strengths.append('Submission threat')
        if fighter.get('finish_rate', 0) > 70:
            strengths.append('High finish rate')
        
        return strengths
    
    def _identify_weaknesses(self, fighter: Dict) -> List[str]:
        """Identify fighter weaknesses"""
        weaknesses = []
        
        if fighter.get('sapm', 0) > 4:
            weaknesses.append('Absorbs many strikes')
        if fighter.get('sig_strike_def', 0) < 0.45:
            weaknesses.append('Poor striking defense')
        if fighter.get('td_def', 0) < 0.4:
            weaknesses.append('Vulnerable to takedowns')
        if fighter.get('record_losses', 0) > fighter.get('record_wins', 0):
            weaknesses.append('Losing record')
        
        return weaknesses


def main():
    """Demo the analysis engine"""
    print("🥊 UFC Analysis Engine Demo\n")
    
    engine = UFCAnalysisEngine()
    
    # Example matchup analysis
    print("=" * 60)
    print("Example: Josh Emmett vs Kevin Vallejos")
    print("=" * 60)
    
    result = engine.analyze_matchup("Josh Emmett", "Kevin Vallejos")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['fighter_a']['name']} ({result['fighter_a']['record']})")
        print(f"  Striking: {result['fighter_a']['scores']['striking']}")
        print(f"  Grappling: {result['fighter_a']['scores']['grappling']}")
        print(f"  Experience: {result['fighter_a']['scores']['experience']}")
        print(f"  Form: {result['fighter_a']['scores']['form']}")
        print(f"  Overall: {result['fighter_a']['scores']['overall']}")
        
        print(f"\n{result['fighter_b']['name']} ({result['fighter_b']['record']})")
        print(f"  Striking: {result['fighter_b']['scores']['striking']}")
        print(f"  Grappling: {result['fighter_b']['scores']['grappling']}")
        print(f"  Experience: {result['fighter_b']['scores']['experience']}")
        print(f"  Form: {result['fighter_b']['scores']['form']}")
        print(f"  Overall: {result['fighter_b']['scores']['overall']}")
        
        pred = result['prediction']
        print(f"\n🏆 Prediction: {pred['winner']} wins")
        print(f"📊 Confidence: {pred['confidence']}")
        print(f"📈 Probability: {pred['probability_a']}% - {pred['probability_b']}%")
        print(f"🎯 Likely Method: {pred['likely_method']}")
        
        if result['advantages']:
            print("\n📋 Key Advantages:")
            for adv in result['advantages']:
                print(f"  • {adv['category']}: {adv['advantage_to']} (+{adv['margin']})")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")


if __name__ == '__main__':
    main()
