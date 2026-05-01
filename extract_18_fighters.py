#!/usr/bin/env python3
"""
Extract complete data for 18 UFC fighters
Creates enriched profiles with fight histories
"""
import json
from datetime import datetime

# List of 18 fighters
FIGHTERS = [
    "Cameron Smotherman", "Edgar Chairez", "Iwo Baraniewski",
    "Jacqueline Cavalcanti", "Jakub Wiklacz", "Jeisla Chaves",
    "Junior Tafa", "Kai Asakura", "Kevin Christian",
    "Louie Sutherland", "Malcolm Wellmaker", "Marwan Rahiki",
    "Mauricio Ruffy", "Ozzy Diaz", "Ramon Taveras",
    "Tai Tuivasa", "Yuneisy Duben", "Zhang Mingyang"
]

def find_fighter(fighters_list, search_name):
    """Find fighter by name (case insensitive partial match)"""
    for fighter in fighters_list:
        name = fighter.get('name', '')
        if search_name.lower() in name.lower():
            return fighter
    return None

def find_fights_for_fighter(fights_list, fighter_name):
    """Find all fights for a fighter"""
    fighter_fights = []
    for fight in fights_list:
        fighter_a = fight.get('fighter_a_name', '')
        fighter_b = fight.get('fighter_b_name', '')
        if fighter_name.lower() in fighter_a.lower() or fighter_name.lower() in fighter_b.lower():
            fighter_fights.append(fight)
    return fighter_fights

def main():
    print("Loading UFC data...")
    
    # Load all data files
    with open('fighters.json', 'r') as f:
        fighters_data = json.load(f)
    
    with open('fight-history.json', 'r') as f:
        history_data = json.load(f)
    
    with open('fight-stats-detailed.json', 'r') as f:
        stats_data = json.load(f)
    
    fighters_list = fighters_data.get('fighters', [])
    fights_list = history_data.get('fights', [])
    
    print(f"Loaded {len(fighters_list)} fighters, {len(fights_list)} fights")
    print("=" * 60)
    
    # Collect all 18 fighters
    collection = {
        'collected_at': datetime.now().isoformat(),
        'total_fighters': len(FIGHTERS),
        'fighters': []
    }
    
    found_count = 0
    missing = []
    
    for name in FIGHTERS:
        print(f"\nSearching: {name}")
        
        fighter = find_fighter(fighters_list, name)
        
        if not fighter:
            print(f"  ❌ Not found in database")
            missing.append(name)
            continue
        
        # Get fights for this fighter
        fighter_fights = find_fights_for_fighter(fights_list, name)
        
        # Create enriched profile
        profile = {
            'profile': fighter,
            'fights': fighter_fights,
            'fight_count': len(fighter_fights),
            'stats': {
                'record': f"{fighter.get('record_wins', 0)}-{fighter.get('record_losses', 0)}-{fighter.get('record_draws', 0)}",
                'slpm': fighter.get('slpm'),
                'sig_strike_acc': fighter.get('sig_strike_acc'),
                'td_avg': fighter.get('td_avg'),
                'sub_avg': fighter.get('sub_avg'),
                'weight_class': fighter.get('weight_class_analysis', {}).get('current_weight_class'),
            }
        }
        
        collection['fighters'].append(profile)
        found_count += 1
        
        print(f"  ✅ Found: {fighter.get('name')}")
        print(f"     Record: {profile['stats']['record']}")
        print(f"     Fights in DB: {len(fighter_fights)}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Collection Summary:")
    print(f"  Found: {found_count}/{len(FIGHTERS)}")
    print(f"  Missing: {len(missing)}")
    
    if missing:
        print(f"\nMissing fighters:")
        for name in missing:
            print(f"  - {name}")
    
    # Save collection
    output_file = '18_fighters_collection.json'
    with open(output_file, 'w') as f:
        json.dump(collection, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Also create individual fighter files
    import os
    os.makedirs('fighters_18', exist_ok=True)
    
    for fighter_profile in collection['fighters']:
        name = fighter_profile['profile']['name'].replace(' ', '_').lower()
        filename = f"fighters_18/{name}.json"
        with open(filename, 'w') as f:
            json.dump(fighter_profile, f, indent=2)
    
    print(f"💾 Individual files saved to: fighters_18/")
    
    return collection

if __name__ == '__main__':
    collection = main()
