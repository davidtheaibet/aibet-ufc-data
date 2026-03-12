#!/usr/bin/env python3
"""
Export UFC database to JSON with enhanced weight class tracking
Addresses UFC 326 lessons: weight class accuracy, power differentials, transformation impact
"""
import sqlite3
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List

DB_PATH = Path("/Users/zacharyreid/.openclaw/workspace/theaibet-sports-build/data/ufc.db")
OUTPUT_DIR = Path(__file__).parent

# Weight class mapping
WEIGHT_CLASSES = {
    115: "Strawweight",
    125: "Flyweight",
    135: "Bantamweight",
    145: "Featherweight",
    155: "Lightweight",
    170: "Welterweight",
    185: "Middleweight",
    205: "Light Heavyweight",
    265: "Heavyweight"
}

def get_weight_class_name(weight_lbs: int) -> str:
    """Get weight class name from weight in lbs"""
    if not weight_lbs:
        return "Unknown"
    # Find closest weight class
    for max_weight, name in sorted(WEIGHT_CLASSES.items()):
        if weight_lbs <= max_weight:
            return name
    return "Heavyweight"

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def get_fighter_weight_class_history(conn, fighter_id: int) -> List[Dict]:
    """Get all weight classes a fighter has competed at"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT f.weight_lbs, e.date, ft.weight_class as fight_weight_class
        FROM fights ft
        JOIN events e ON ft.event_id = e.id
        LEFT JOIN fighters f ON ft.fighter_a_id = f.id OR ft.fighter_b_id = f.id
        WHERE (ft.fighter_a_id = ? OR ft.fighter_b_id = ?) AND f.id != ?
        ORDER BY e.date DESC
    """, (fighter_id, fighter_id, fighter_id))
    
    weight_classes = set()
    for row in cursor.fetchall():
        if row[0]:
            weight_classes.add(row[0])
    
    return sorted(list(weight_classes))

def calculate_power_indicators(fighter: Dict, fight_history: List[Dict]) -> Dict:
    """
    Calculate power/strength indicators for a fighter
    Addresses UFC 326 lesson: power differential when moving weight classes
    """
    wins = fighter.get('record_wins', 0) or 0
    total_fights = wins + (fighter.get('record_losses', 0) or 0) + (fighter.get('record_draws', 0) or 0)
    
    # KO Power Score (0-100)
    win_methods = fighter.get('win_methods', {})
    ko_wins = win_methods.get('ko_tko', 0)
    ko_rate = (ko_wins / wins * 100) if wins > 0 else 0
    
    # KO Power Score based on KO rate and volume
    if wins >= 10:
        ko_power_score = min(ko_rate * 1.2, 100)  # Cap at 100
    else:
        ko_power_score = min(ko_rate * 0.8, 100)  # Less reliable with small sample
    
    # Takedown Power Score (0-100)
    td_avg = fighter.get('td_avg', 0) or 0
    td_acc = fighter.get('td_acc', 0) or 0
    td_power_score = min((td_avg * 10) + (td_acc * 50), 100)
    
    # Physical Presence Score (based on height/reach for weight class)
    height_str = fighter.get('height', '')
    reach_str = fighter.get('reach', '')
    weight_lbs = fighter.get('weight_lbs', 0) or 0
    
    physical_score = 50  # Base score
    
    # Parse height to inches
    try:
        if height_str and "'" in height_str:
            parts = height_str.replace('"', '').split("'")
            height_inches = int(parts[0]) * 12 + int(parts[1].strip() or 0)
            
            # Compare to average for weight class
            if weight_lbs:
                if weight_lbs <= 135:  # Bantamweight and below
                    avg_height = 65  # 5'5"
                elif weight_lbs <= 155:  # Featherweight/Lightweight
                    avg_height = 68  # 5'8"
                elif weight_lbs <= 185:  # Welterweight/Middleweight
                    avg_height = 71  # 5'11"
                else:
                    avg_height = 74  # 6'2"
                
                height_diff = height_inches - avg_height
                physical_score += height_diff * 3  # 3 points per inch
    except:
        pass
    
    # Overall Power Rating
    power_rating = (ko_power_score * 0.4) + (td_power_score * 0.3) + (physical_score * 0.3)
    
    return {
        'ko_power_score': round(ko_power_score, 1),
        'ko_rate': round(ko_rate, 1),
        'takedown_power_score': round(td_power_score, 1),
        'physical_presence_score': round(max(0, min(100, physical_score)), 1),
        'overall_power_rating': round(max(0, min(100, power_rating)), 1),
        'finish_rate': fighter.get('finish_rate', 0)
    }

def analyze_weight_cut_risk(fighter: Dict, weight_class_history: List[int]) -> Dict:
    """
    Analyze weight cut history and potential issues
    Addresses UFC 326 lesson: weight cut impact on performance
    """
    current_weight = fighter.get('weight_lbs', 0) or 0
    
    if not current_weight or not weight_class_history:
        return {
            'weight_cut_risk': 'Unknown',
            'weight_class_history': [],
            'natural_weight_class': get_weight_class_name(current_weight) if current_weight else 'Unknown',
            'has_moved_weight': False,
            'weight_trend': 'Unknown'
        }
    
    # Determine if fighter has moved weight classes
    has_moved_weight = len(weight_class_history) > 1
    
    # Determine weight trend
    if len(weight_class_history) >= 2:
        if weight_class_history[0] > weight_class_history[-1]:
            weight_trend = 'Moving Up'
        elif weight_class_history[0] < weight_class_history[-1]:
            weight_trend = 'Moving Down'
        else:
            weight_trend = 'Stable'
    else:
        weight_trend = 'Stable'
    
    # Assess weight cut risk
    # Higher risk if moving down significantly or if already at lowest weight
    weight_cut_risk = 'Low'
    if has_moved_weight:
        weight_diff = max(weight_class_history) - min(weight_class_history)
        if weight_diff >= 20:
            weight_cut_risk = 'High'
        elif weight_diff >= 10:
            weight_cut_risk = 'Medium'
    
    # Determine natural weight class (most common or heaviest if stable)
    if weight_class_history:
        natural_weight = max(set(weight_class_history), key=weight_class_history.count)
        natural_weight_class = get_weight_class_name(natural_weight)
    else:
        natural_weight_class = get_weight_class_name(current_weight)
    
    return {
        'weight_cut_risk': weight_cut_risk,
        'weight_class_history': [get_weight_class_name(w) for w in weight_class_history],
        'weight_class_history_lbs': weight_class_history,
        'natural_weight_class': natural_weight_class,
        'current_weight_class': get_weight_class_name(current_weight),
        'has_moved_weight': has_moved_weight,
        'weight_trend': weight_trend,
        'is_at_natural_weight': natural_weight_class == get_weight_class_name(current_weight)
    }

def export_fighters_enhanced():
    """Export fighters to JSON with enhanced weight class tracking"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id, ufc_id, name, nickname,
            record_wins, record_losses, record_draws, record_no_contests,
            height, reach, stance, date_of_birth, nationality, team,
            slpm, sig_strike_acc, sapm, sig_strike_def,
            td_avg, td_acc, td_def, sub_avg, weight_lbs
        FROM fighters 
        WHERE record_wins + record_losses + record_draws > 0
        ORDER BY record_wins DESC
    """)
    
    fighters = []
    for row in cursor.fetchall():
        fighter = dict(row)
        
        # Calculate derived metrics
        total_fights = fighter['record_wins'] + fighter['record_losses'] + fighter['record_draws']
        fighter['total_fights'] = total_fights
        fighter['win_rate'] = round(fighter['record_wins'] / total_fights * 100, 2) if total_fights > 0 else 0
        
        # Get weight class history
        weight_history = get_fighter_weight_class_history(conn, fighter['id'])
        
        # Add weight class analysis
        fighter['weight_class_analysis'] = analyze_weight_cut_risk(fighter, weight_history)
        
        # Add power indicators
        fighter['power_indicators'] = calculate_power_indicators(fighter, [])
        
        # Win methods
        fighter['win_methods'] = {
            'ko_tko': 0,
            'submissions': 0,
            'decisions': 0
        }
        
        # Recent fight history placeholder
        fighter['recent_fights'] = []
        
        fighters.append(fighter)
    
    conn.close()
    return fighters

def export_fight_history():
    """Export fight history with weight class context"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            f.id, f.ufc_id, f.event_id, f.fighter_a_id, f.fighter_b_id,
            f.winner_id, f.method, f.method_details, f.end_round, f.end_time,
            f.weight_class, f.is_title_fight, f.is_main_event, f.card_position,
            fa.name as fighter_a_name, fb.name as fighter_b_name,
            fa.weight_lbs as fighter_a_weight, fb.weight_lbs as fighter_b_weight,
            fw.name as winner_name,
            e.name as event_name, e.date as event_date
        FROM fights f
        JOIN fighters fa ON f.fighter_a_id = fa.id
        JOIN fighters fb ON f.fighter_b_id = fb.id
        LEFT JOIN fighters fw ON f.winner_id = fw.id
        JOIN events e ON f.event_id = e.id
        ORDER BY e.date DESC
    """)
    
    fights = []
    for row in cursor.fetchall():
        fight = dict(row)
        
        # Add weight class context
        fight['weight_class_context'] = {
            'fighter_a_weight_class': get_weight_class_name(fight.get('fighter_a_weight', 0)),
            'fighter_b_weight_class': get_weight_class_name(fight.get('fighter_b_weight', 0)),
            'was_weight_class_change': fight.get('fighter_a_weight') != fight.get('fighter_b_weight')
        }
        
        # Determine result for fighter_a
        if fight['winner_id'] is None:
            fight['result'] = 'Draw'
        elif fight['winner_id'] == fight['fighter_a_id']:
            fight['result'] = 'Win'
        else:
            fight['result'] = 'Loss'
        
        fights.append(fight)
    
    conn.close()
    return fights

def update_fighter_win_methods(fighters, fight_history):
    """Update fighters with win method breakdowns"""
    for fighter in fighters:
        fighter_id = fighter['id']
        ko_tko = 0
        submissions = 0
        decisions = 0
        
        # Get fights where this fighter won
        for fight in fight_history:
            if fight['winner_id'] == fighter_id and fight['method']:
                method = fight['method'].lower()
                if 'ko' in method or 'tko' in method or 'knockout' in method:
                    ko_tko += 1
                elif 'sub' in method or 'submission' in method:
                    submissions += 1
                elif 'decision' in method:
                    decisions += 1
        
        fighter['win_methods'] = {
            'ko_tko': ko_tko,
            'submissions': submissions,
            'decisions': decisions
        }
        
        # Update finish rate
        total_wins = fighter['record_wins']
        if total_wins > 0:
            fighter['finish_rate'] = round((ko_tko + submissions) / total_wins * 100, 2)
        else:
            fighter['finish_rate'] = 0
        
        # Recalculate power indicators with updated finish rate
        fighter['power_indicators'] = calculate_power_indicators(fighter, [])

def export_fighter_fight_history():
    """Export recent fight history for each fighter"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all fighters
    cursor.execute("SELECT id, name FROM fighters")
    fighters = {row['id']: row['name'] for row in cursor.fetchall()}
    
    fighter_histories = {}
    
    for fighter_id, fighter_name in fighters.items():
        cursor.execute("""
            SELECT 
                f.id, f.ufc_id, f.method, f.method_details, f.end_round, f.end_time,
                f.weight_class, f.is_title_fight, f.is_main_event,
                f.fighter_a_id, f.fighter_b_id, f.winner_id,
                e.name as event_name, e.date as event_date,
                fa.name as opponent_name,
                fs.sig_strikes_landed, fs.sig_strikes_attempted,
                fs.takedowns_landed, fs.takedowns_attempted,
                fs.knockdowns_scored, fs.submissions_attempted
            FROM fights f
            JOIN events e ON f.event_id = e.id
            JOIN fighters fa ON (CASE WHEN f.fighter_a_id = ? THEN f.fighter_b_id ELSE f.fighter_a_id END) = fa.id
            LEFT JOIN fight_stats fs ON f.id = fs.fight_id AND fs.fighter_id = ?
            WHERE f.fighter_a_id = ? OR f.fighter_b_id = ?
            ORDER BY e.date DESC
            LIMIT 10
        """, (fighter_id, fighter_id, fighter_id, fighter_id))
        
        fights = []
        for row in cursor.fetchall():
            fight = dict(row)
            
            # Determine result
            if fight['winner_id'] is None:
                fight['result'] = 'Draw'
            elif fight['winner_id'] == fighter_id:
                fight['result'] = 'Win'
            else:
                fight['result'] = 'Loss'
            
            fights.append(fight)
        
        if fights:
            fighter_histories[fighter_id] = {
                'fighter_id': fighter_id,
                'fighter_name': fighter_name,
                'fights': fights
            }
    
    conn.close()
    return fighter_histories

def main():
    print("🥊 Exporting Enhanced UFC Data to JSON...")
    print("📊 Including weight class history and power indicators...")
    
    # Export fighters with enhanced data
    print("📊 Exporting fighters...")
    fighters = export_fighters_enhanced()
    
    # Export fight history
    print("📊 Exporting fight history...")
    fight_history = export_fight_history()
    
    # Update fighter win methods
    print("📊 Calculating win methods...")
    update_fighter_win_methods(fighters, fight_history)
    
    # Export fighter-specific fight histories
    print("📊 Exporting fighter histories...")
    fighter_histories = export_fighter_fight_history()
    
    # Add recent fights to fighters
    for fighter in fighters:
        fighter_id = fighter['id']
        if fighter_id in fighter_histories:
            fighter['recent_fights'] = fighter_histories[fighter_id]['fights'][:5]
    
    # Write JSON files
    output_path = Path(__file__).parent
    
    with open(output_path / 'fighters.json', 'w') as f:
        json.dump({
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'count': len(fighters),
                'source': 'ufcstats.com',
                'enhancements': [
                    'weight_class_history',
                    'power_indicators',
                    'weight_cut_risk_analysis'
                ]
            },
            'fighters': fighters
        }, f, indent=2, cls=DateTimeEncoder)
    
    with open(output_path / 'fight-history.json', 'w') as f:
        json.dump({
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'count': len(fight_history),
                'source': 'ufcstats.com'
            },
            'fights': fight_history
        }, f, indent=2, cls=DateTimeEncoder)
    
    print(f"✅ Exported {len(fighters)} fighters with enhanced data")
    print(f"✅ Exported {len(fight_history)} fights")
    print(f"\n📁 Files saved to: {output_path}")
    print("\n🎯 New data points added:")
    print("  • Fighter's natural/primary weight class")
    print("  • Weight class history (all classes fought at)")
    print("  • Power indicators (KO rate, takedown power, physical presence)")
    print("  • Weight cut risk assessment")
    print("  • Weight trend analysis (moving up/down/stable)")

if __name__ == '__main__':
    main()
