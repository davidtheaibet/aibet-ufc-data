#!/usr/bin/env python3
"""
Enhanced UFC Fight Analysis Engine v2.0
Addresses UFC 326 lessons: weight class accuracy, power differentials, transformation impact
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class WeightClassContext:
    """Weight class context for matchup analysis"""
    natural_weight_class: str
    current_weight_class: str
    has_moved_weight: bool
    weight_trend: str
    weight_cut_risk: str
    is_at_natural_weight: bool

class UFCAnalysisEngine:
    """
    Enhanced UFC Fight Analysis Engine v2.0
    
    Addresses UFC 326 Holloway vs Oliveira analysis failures:
    1. Weight class accuracy (fighter's natural vs current weight class)
    2. Strength/power differential when fighters move up/down weight
    3. Physical transformation impact on performance
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
    
    def calculate_weight_class_penalty(self, fighter: Dict) -> float:
        """
        Calculate performance penalty for weight class changes
        Addresses UFC 326 Lesson #1: Weight class accuracy
        """
        weight_analysis = fighter.get('weight_class_analysis', {})
        
        if not weight_analysis:
            return 0
        
        penalty = 0
        
        # If not at natural weight class, apply penalty
        if not weight_analysis.get('is_at_natural_weight', True):
            weight_trend = weight_analysis.get('weight_trend', 'Stable')
            
            if weight_trend == 'Moving Down':
                # Moving down - potential weight cut issues
                weight_cut_risk = weight_analysis.get('weight_cut_risk', 'Low')
                if weight_cut_risk == 'High':
                    penalty = -15  # Significant penalty for risky weight cut
                elif weight_cut_risk == 'Medium':
                    penalty = -8
                else:
                    penalty = -3
            
            elif weight_trend == 'Moving Up':
                # Moving up - may lack power at higher weight
                # Less penalty than moving down, but still significant
                penalty = -5
        
        return penalty
    
    def calculate_power_differential(self, fighter_a: Dict, fighter_b: Dict) -> Dict:
        """
        Calculate power differential between fighters
        Addresses UFC 326 Lesson #2: Strength/power differential
        """
        power_a = fighter_a.get('power_indicators', {})
        power_b = fighter_b.get('power_indicators', {})
        
        # Get power ratings
        rating_a = power_a.get('overall_power_rating', 50)
        rating_b = power_b.get('overall_power_rating', 50)
        
        # Get KO rates
        ko_rate_a = power_a.get('ko_rate', 0)
        ko_rate_b = power_b.get('ko_rate', 0)
        
        # Get physical presence scores
        physical_a = power_a.get('physical_presence_score', 50)
        physical_b = power_b.get('physical_presence_score', 50)
        
        # Calculate differentials
        power_diff = rating_a - rating_b
        ko_diff = ko_rate_a - ko_rate_b
        physical_diff = physical_a - physical_b
        
        return {
            'power_differential': round(power_diff, 1),
            'ko_rate_differential': round(ko_diff, 1),
            'physical_presence_differential': round(physical_diff, 1),
            'advantage': fighter_a['name'] if power_diff > 0 else fighter_b['name'],
            'advantage_margin': abs(round(power_diff, 1))
        }
    
    def assess_transformation_impact(self, fighter: Dict) -> Dict:
        """
        Assess physical transformation impact on performance
        Addresses UFC 326 Lesson #3: Physical transformation impact
        """
        weight_analysis = fighter.get('weight_class_analysis', {})
        power = fighter.get('power_indicators', {})
        
        impact_score = 0
        concerns = []
        advantages = []
        
        if not weight_analysis.get('is_at_natural_weight', True):
            weight_trend = weight_analysis.get('weight_trend', 'Stable')
            
            if weight_trend == 'Moving Up':
                # Moving up in weight
                if power.get('ko_power_score', 0) > 70:
                    advantages.append('Power carries well to higher weight')
                    impact_score += 5
                else:
                    concerns.append('Power may not translate to higher weight')
                    impact_score -= 10
                    
                # Check if they have the frame for it
                physical_score = power.get('physical_presence_score', 50)
                if physical_score > 60:
                    advantages.append('Good physical frame for higher weight')
                    impact_score += 3
            
            elif weight_trend == 'Moving Down':
                # Moving down in weight
                weight_cut_risk = weight_analysis.get('weight_cut_risk', 'Low')
                
                if weight_cut_risk == 'High':
                    concerns.append('High weight cut risk - may gas out')
                    impact_score -= 15
                elif weight_cut_risk == 'Medium':
                    concerns.append('Moderate weight cut concerns')
                    impact_score -= 7
                else:
                    advantages.append('Clean weight cut expected')
                    impact_score += 2
        
        return {
            'impact_score': impact_score,
            'concerns': concerns,
            'advantages': advantages,
            'assessment': 'Positive' if impact_score > 0 else 'Negative' if impact_score < 0 else 'Neutral'
        }
    
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
    
    def analyze_matchup(self, fighter_a_name: str, fighter_b_name: str) -> Dict:
        """
        Comprehensive matchup analysis with weight class considerations
        Addresses all UFC 326 lessons
        """
        fighter_a = self.get_fighter(fighter_a_name)
        fighter_b = self.get_fighter(fighter_b_name)
        
        if not fighter_a or not fighter_b:
            return {
                'error': 'One or both fighters not found in database',
                'fighter_a_found': fighter_a is not None,
                'fighter_b_found': fighter_b is not None
            }
        
        # Calculate base scores
        a_striking = self.calculate_striking_score(fighter_a)
        b_striking = self.calculate_striking_score(fighter_b)
        
        a_grappling = self.calculate_grappling_score(fighter_a)
        b_grappling = self.calculate_grappling_score(fighter_b)
        
        a_experience = self.calculate_experience_score(fighter_a)
        b_experience = self.calculate_experience_score(fighter_b)
        
        a_form = self.calculate_form_score(fighter_a)
        b_form = self.calculate_form_score(fighter_b)
        
        # Calculate power indicators
        power_a = fighter_a.get('power_indicators', {})
        power_b = fighter_b.get('power_indicators', {})
        a_power = power_a.get('overall_power_rating', 50)
        b_power = power_b.get('overall_power_rating', 50)
        
        # Calculate weight class penalties
        a_weight_penalty = self.calculate_weight_class_penalty(fighter_a)
        b_weight_penalty = self.calculate_weight_class_penalty(fighter_b)
        
        # Calculate power differential
        power_diff = self.calculate_power_differential(fighter_a, fighter_b)
        
        # Assess transformation impact
        a_transformation = self.assess_transformation_impact(fighter_a)
        b_transformation = self.assess_transformation_impact(fighter_b)
        
        # Calculate overall scores with weights and adjustments
        weights = {
            'striking': 0.22,
            'grappling': 0.22,
            'experience': 0.18,
            'form': 0.18,
            'power': 0.10,
            'weight_class': 0.10
        }
        
        a_total = (
            a_striking * weights['striking'] +
            a_grappling * weights['grappling'] +
            a_experience * weights['experience'] +
            a_form * weights['form'] +
            a_power * weights['power'] +
            (50 + a_weight_penalty) * weights['weight_class'] +
            a_transformation['impact_score']
        )
        
        b_total = (
            b_striking * weights['striking'] +
            b_grappling * weights['grappling'] +
            b_experience * weights['experience'] +
            b_form * weights['form'] +
            b_power * weights['power'] +
            (50 + b_weight_penalty) * weights['weight_class'] +
            b_transformation['impact_score']
        )
        
        # Calculate win probability
        diff = a_total - b_total
        prob_a = 1 / (1 + math.exp(-diff / 15))
        prob_b = 1 - prob_a
        
        # Determine confidence level
        confidence = self._calculate_confidence(abs(diff), fighter_a, fighter_b)
        
        # Determine likely finish method
        likely_method = self._predict_finish_method(fighter_a, fighter_b)
        
        return {
            'fighter_a': {
                'name': fighter_a['name'],
                'record': f"{fighter_a.get('record_wins', 0)}-{fighter_a.get('record_losses', 0)}-{fighter_a.get('record_draws', 0)}",
                'weight_class': fighter_a.get('weight_class_analysis', {}).get('current_weight_class', 'Unknown'),
                'natural_weight_class': fighter_a.get('weight_class_analysis', {}).get('natural_weight_class', 'Unknown'),
                'scores': {
                    'striking': round(a_striking, 1),
                    'grappling': round(a_grappling, 1),
                    'experience': round(a_experience, 1),
                    'form': round(a_form, 1),
                    'power': round(a_power, 1),
                    'overall': round(a_total, 1)
                },
                'power_indicators': power_a,
                'weight_penalty': a_weight_penalty,
                'transformation_impact': a_transformation
            },
            'fighter_b': {
                'name': fighter_b['name'],
                'record': f"{fighter_b.get('record_wins', 0)}-{fighter_b.get('record_losses', 0)}-{fighter_b.get('record_draws', 0)}",
                'weight_class': fighter_b.get('weight_class_analysis', {}).get('current_weight_class', 'Unknown'),
                'natural_weight_class': fighter_b.get('weight_class_analysis', {}).get('natural_weight_class', 'Unknown'),
                'scores': {
                    'striking': round(b_striking, 1),
                    'grappling': round(b_grappling, 1),
                    'experience': round(b_experience, 1),
                    'form': round(b_form, 1),
                    'power': round(b_power, 1),
                    'overall': round(b_total, 1)
                },
                'power_indicators': power_b,
                'weight_penalty': b_weight_penalty,
                'transformation_impact': b_transformation
            },
            'power_differential': power_diff,
            'prediction': {
                'winner': fighter_a['name'] if prob_a > 0.5 else fighter_b['name'],
                'confidence': confidence,
                'probability_a': round(prob_a * 100, 1),
                'probability_b': round(prob_b * 100, 1),
                'likely_method': likely_method
            },
            'key_factors': self._identify_key_factors(fighter_a, fighter_b, {
                'striking': a_striking - b_striking,
                'grappling': a_grappling - b_grappling,
                'experience': a_experience - b_experience,
                'form': a_form - b_form,
                'power': a_power - b_power,
                'weight_penalty': a_weight_penalty - b_weight_penalty
            })
        }
    
    def _calculate_confidence(self, score_diff: float, fighter_a: Dict, fighter_b: Dict) -> str:
        """Calculate prediction confidence level"""
        a_data_quality = self._assess_data_quality(fighter_a)
        b_data_quality = self._assess_data_quality(fighter_b)
        avg_quality = (a_data_quality + b_data_quality) / 2
        
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
        
        checks = [
            (fighter.get('slpm'), 'slpm'),
            (fighter.get('sig_strike_acc'), 'accuracy'),
            (fighter.get('td_avg'), 'takedowns'),
            (fighter.get('recent_fights'), 'recent fights'),
            (fighter.get('weight_class_analysis'), 'weight analysis')
        ]
        
        for value, _ in checks:
            total += 1
            if value and (isinstance(value, list) or isinstance(value, dict) or value > 0):
                score += 1
        
        total_fights = fighter.get('record_wins', 0) + fighter.get('record_losses', 0)
        if total_fights >= 10:
            score += 1
        total += 1
        
        return score / total if total > 0 else 0
    
    def _predict_finish_method(self, fighter_a: Dict, fighter_b: Dict) -> str:
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
    
    def _identify_key_factors(self, fighter_a: Dict, fighter_b: Dict, diffs: Dict) -> List[Dict]:
        """Identify key factors that will decide the fight"""
        factors = []
        
        # Weight class concerns
        a_weight = fighter_a.get('weight_class_analysis', {})
        b_weight = fighter_b.get('weight_class_analysis', {})
        
        if not a_weight.get('is_at_natural_weight', True):
            factors.append({
                'factor': 'weight_class',
                'description': f"{fighter_a['name']} not at natural weight class",
                'impact': 'negative' if a_weight.get('weight_cut_risk') == 'High' else 'neutral'
            })
        
        if not b_weight.get('is_at_natural_weight', True):
            factors.append({
                'factor': 'weight_class',
                'description': f"{fighter_b['name']} not at natural weight class",
                'impact': 'negative' if b_weight.get('weight_cut_risk') == 'High' else 'neutral'
            })
        
        # Power differential
        power_diff = diffs.get('power', 0)
        if abs(power_diff) > 15:
            factors.append({
                'factor': 'power',
                'description': f"Significant power advantage to {fighter_a['name'] if power_diff > 0 else fighter_b['name']}",
                'impact': 'positive'
            })
        
        # Skill differentials
        for category, diff in diffs.items():
            if category in ['weight_penalty']:
                continue
            if abs(diff) > 15:
                factors.append({
                    'factor': category,
                    'description': f"{category.title()} advantage to {fighter_a['name'] if diff > 0 else fighter_b['name']}",
                    'impact': 'positive'
                })
        
        return factors[:5]
    
    def get_fighter_profile(self, name: str) -> Dict:
        """Get detailed fighter profile with weight class analysis"""
        fighter = self.get_fighter(name)
        
        if not fighter:
            return {'error': f'Fighter {name} not found'}
        
        return {
            'profile': fighter,
            'analysis': {
                'striking_score': round(self.calculate_striking_score(fighter), 1),
                'grappling_score': round(self.calculate_grappling_score(fighter), 1),
                'experience_score': round(self.calculate_experience_score(fighter), 1),
                'form_score': round(self.calculate_form_score(fighter), 1)
            },
            'weight_class_analysis': fighter.get('weight_class_analysis', {}),
            'power_indicators': fighter.get('power_indicators', {}),
            'transformation_impact': self.assess_transformation_impact(fighter)
        }


def main():
    """Demo the enhanced analysis engine"""
    print("🥊 UFC Analysis Engine v2.0 Demo")
    print("📊 Now with weight class and power differential analysis\n")
    
    engine = UFCAnalysisEngine()
    
    # Example matchup analysis
    print("=" * 70)
    print("Example: Josh Emmett vs Kevin Vallejos")
    print("=" * 70)
    
    result = engine.analyze_matchup("Josh Emmett", "Kevin Vallejos")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['fighter_a']['name']} ({result['fighter_a']['record']})")
        print(f"  Current Weight: {result['fighter_a']['weight_class']}")
        print(f"  Natural Weight: {result['fighter_a']['natural_weight_class']}")
        print(f"  Striking: {result['fighter_a']['scores']['striking']}")
        print(f"  Grappling: {result['fighter_a']['scores']['grappling']}")
        print(f"  Power Rating: {result['fighter_a']['power_indicators'].get('overall_power_rating', 'N/A')}")
        print(f"  Weight Penalty: {result['fighter_a']['weight_penalty']}")
        
        print(f"\n{result['fighter_b']['name']} ({result['fighter_b']['record']})")
        print(f"  Current Weight: {result['fighter_b']['weight_class']}")
        print(f"  Natural Weight: {result['fighter_b']['natural_weight_class']}")
        print(f"  Striking: {result['fighter_b']['scores']['striking']}")
        print(f"  Grappling: {result['fighter_b']['scores']['grappling']}")
        print(f"  Power Rating: {result['fighter_b']['power_indicators'].get('overall_power_rating', 'N/A')}")
        print(f"  Weight Penalty: {result['fighter_b']['weight_penalty']}")
        
        pred = result['prediction']
        print(f"\n🏆 Prediction: {pred['winner']} wins")
        print(f"📊 Confidence: {pred['confidence']}")
        print(f"📈 Probability: {pred['probability_a']}% - {pred['probability_b']}%")
        print(f"🎯 Likely Method: {pred['likely_method']}")
        
        if result['key_factors']:
            print("\n📋 Key Factors:")
            for factor in result['key_factors']:
                print(f"  • {factor['description']}")
    
    print("\n" + "=" * 70)
    print("Analysis complete!")


if __name__ == '__main__':
    main()
