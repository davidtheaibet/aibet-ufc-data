#!/usr/bin/env python3
"""
Export UFC database to JSON files for AIbet analysis engine
"""
import sqlite3
import json
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path("/Users/zacharyreid/.openclaw/workspace/theaibet-sports-build/data/ufc.db")
OUTPUT_DIR = Path(__file__).parent

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def export_fighters():
    """Export fighters to JSON with comprehensive stats"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id, ufc_id, name, nickname, weight_class,
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
        
        # Win method breakdown (will be populated from fight history)
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

def export_events():
    """Export events to JSON"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            e.id, e.ufc_id, e.name, e.date, e.location, e.venue,
            e.is_ppv, e.is_fight_night, e.status, e.url,
            COUNT(f.id) as fight_count
        FROM events e
        LEFT JOIN fights f ON e.id = f.event_id
        GROUP BY e.id
        ORDER BY e.date DESC
    """)
    
    events = []
    for row in cursor.fetchall():
        event = dict(row)
        events.append(event)
    
    conn.close()
    return events

def export_fight_history():
    """Export fight history with detailed stats"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            f.id, f.ufc_id, f.event_id, f.fighter_a_id, f.fighter_b_id,
            f.winner_id, f.method, f.method_details, f.end_round, f.end_time,
            f.weight_class, f.is_title_fight, f.is_main_event, f.card_position,
            fa.name as fighter_a_name, fb.name as fighter_b_name,
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
        
        # Calculate finish rate
        total_wins = fighter['record_wins']
        if total_wins > 0:
            fighter['finish_rate'] = round((ko_tko + submissions) / total_wins * 100, 2)
        else:
            fighter['finish_rate'] = 0

def main():
    print("🥊 Exporting UFC Data to JSON...")
    
    # Export fighters
    print("📊 Exporting fighters...")
    fighters = export_fighters()
    
    # Export fight history
    print("📊 Exporting fight history...")
    fight_history = export_fight_history()
    
    # Update fighter win methods
    print("📊 Calculating win methods...")
    update_fighter_win_methods(fighters, fight_history)
    
    # Export events
    print("📊 Exporting events...")
    events = export_events()
    
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
                'source': 'ufcstats.com'
            },
            'fighters': fighters
        }, f, indent=2, cls=DateTimeEncoder)
    
    with open(output_path / 'events.json', 'w') as f:
        json.dump({
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'count': len(events),
                'source': 'ufcstats.com'
            },
            'events': events
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
    
    with open(output_path / 'fighter-histories.json', 'w') as f:
        json.dump({
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'count': len(fighter_histories),
                'source': 'ufcstats.com'
            },
            'fighter_histories': fighter_histories
        }, f, indent=2, cls=DateTimeEncoder)
    
    print(f"✅ Exported {len(fighters)} fighters")
    print(f"✅ Exported {len(events)} events")
    print(f"✅ Exported {len(fight_history)} fights")
    print(f"✅ Exported {len(fighter_histories)} fighter histories")
    print(f"\n📁 Files saved to: {output_path}")

if __name__ == '__main__':
    main()
