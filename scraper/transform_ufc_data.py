#!/usr/bin/env python3
"""
Transform upcoming-events.json to include ufc_id and proper API structure
"""
import json
import re
from datetime import datetime
from pathlib import Path

def normalize_event_name(name):
    """Normalize event name for matching"""
    # Remove UFC prefixes, colons, and standardize
    name = re.sub(r'^(UFC\s+)?(Fight\s+Night:\s*)?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.lower()

def load_json(filepath):
    """Load JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None

def transform_event(event, ufc_id_mapping=None):
    """Transform single event to API format"""
    
    # Generate or use provided ufc_id
    event_id = event.get('id', '')
    ufc_id = None
    
    if ufc_id_mapping and event_id in ufc_id_mapping:
        ufc_id = ufc_id_mapping[event_id]
    
    # Extract fighters from main_card and prelims
    all_fighters = []
    
    for fight in event.get('main_card', []):
        if 'fighter_a' in fight:
            all_fighters.append({
                'name': fight['fighter_a'].get('name'),
                'rank': fight['fighter_a'].get('rank'),
                'country': fight['fighter_a'].get('country'),
                'opponent': fight['fighter_b'].get('name') if 'fighter_b' in fight else None,
                'weight_class': fight.get('weight_class'),
                'is_main_event': fight.get('is_main_event', False),
                'card': 'main'
            })
        if 'fighter_b' in fight:
            all_fighters.append({
                'name': fight['fighter_b'].get('name'),
                'rank': fight['fighter_b'].get('rank'),
                'country': fight['fighter_b'].get('country'),
                'opponent': fight['fighter_a'].get('name') if 'fighter_a' in fight else None,
                'weight_class': fight.get('weight_class'),
                'is_main_event': fight.get('is_main_event', False),
                'card': 'main'
            })
    
    for fight in event.get('prelims', []):
        if 'fighter_a' in fight:
            all_fighters.append({
                'name': fight['fighter_a'].get('name'),
                'rank': fight['fighter_a'].get('rank'),
                'country': fight['fighter_a'].get('country'),
                'opponent': fight['fighter_b'].get('name') if 'fighter_b' in fight else None,
                'weight_class': fight.get('weight_class'),
                'card': 'prelim'
            })
        if 'fighter_b' in fight:
            all_fighters.append({
                'name': fight['fighter_b'].get('name'),
                'rank': fight['fighter_b'].get('rank'),
                'country': fight['fighter_b'].get('country'),
                'opponent': fight['fighter_a'].get('name') if 'fighter_a' in fight else None,
                'weight_class': fight.get('weight_class'),
                'card': 'prelim'
            })
    
    return {
        'id': event_id,
        'ufc_id': ufc_id,  # Will be populated by scraper
        'name': event.get('name'),
        'date': event.get('date'),
        'time': event.get('time'),
        'venue': event.get('venue'),
        'location': event.get('location'),
        'is_ppv': event.get('is_ppv', False),
        'is_fight_night': event.get('is_fight_night', True),
        'status': 'upcoming',
        'url': f"http://www.ufcstats.com/event-details/{ufc_id}" if ufc_id else None,
        'fight_count': len(event.get('main_card', [])) + len(event.get('prelims', [])),
        'main_card': event.get('main_card', []),
        'prelims': event.get('prelims', []),
        'fighters': all_fighters
    }

def create_api_response(upcoming_events, fighters_db=None):
    """Create full API response structure"""
    
    transformed_events = []
    for event in upcoming_events.get('upcoming_events', []):
        transformed = transform_event(event)
        
        # Enrich with fighter profiles if available
        if fighters_db and transformed['fighters']:
            for fighter in transformed['fighters']:
                # Match by name
                profile = find_fighter_profile(fighter['name'], fighters_db)
                if profile:
                    fighter['ufc_id'] = profile.get('ufc_id')
                    fighter['record'] = f"{profile.get('record_wins', 0)}-{profile.get('record_losses', 0)}-{profile.get('record_draws', 0)}"
                    fighter['stats'] = {
                        'slpm': profile.get('slpm'),
                        'sig_strike_acc': profile.get('sig_strike_acc'),
                        'td_avg': profile.get('td_avg')
                    }
        
        transformed_events.append(transformed)
    
    return {
        'metadata': {
            'api_version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'source': 'aibet-ufc-data',
            'count': len(transformed_events),
            'notes': 'ufc_id will be populated by UFCStats scraper'
        },
        'events': transformed_events
    }

def find_fighter_profile(name, fighters_db):
    """Find fighter profile by name"""
    if not name or not fighters_db:
        return None
    
    name_lower = name.lower().strip()
    
    for fighter in fighters_db.get('fighters', []):
        if fighter.get('name', '').lower().strip() == name_lower:
            return fighter
    
    # Try partial match
    for fighter in fighters_db.get('fighters', []):
        fighter_name = fighter.get('name', '').lower().strip()
        if name_lower in fighter_name or fighter_name in name_lower:
            return fighter
    
    return None

def main():
    print("=" * 60)
    print("UFC Data Transformer")
    print("=" * 60)
    
    # Load source files
    repo_path = Path.home() / 'Documents/GitHub/aibet-ufc-data'
    
    print("\n📂 Loading data files...")
    upcoming = load_json(repo_path / 'upcoming-events.json')
    fighters = load_json(repo_path / 'fighters.json')
    
    if not upcoming:
        print("❌ Failed to load upcoming-events.json")
        return
    
    print(f"✅ Loaded {len(upcoming.get('upcoming_events', []))} upcoming events")
    print(f"✅ Loaded {len(fighters.get('fighters', [])) if fighters else 0} fighter profiles")
    
    # Transform data
    print("\n🔄 Transforming data...")
    api_response = create_api_response(upcoming, fighters)
    
    # Save output
    output_file = 'ufc-upcoming-api.json'
    with open(output_file, 'w') as f:
        json.dump(api_response, f, indent=2)
    
    print(f"\n✅ Saved API response to {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for evt in api_response['events']:
        print(f"\n🥊 {evt['name']}")
        print(f"   Date: {evt['date']}")
        print(f"   ufc_id: {evt['ufc_id'] or 'PENDING - needs scraper'}")
        print(f"   Location: {evt['location']}")
        print(f"   Fights: {evt['fight_count']}")
        print(f"   Fighters with profiles: {sum(1 for f in evt['fighters'] if f.get('ufc_id'))}/{len(evt['fighters'])}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Run upcoming_events_scraper.py to get ufc_id from UFCStats")
    print("2. Merge scraper output with this data")
    print("3. Deploy API endpoint")
    print("=" * 60)

if __name__ == '__main__':
    main()
