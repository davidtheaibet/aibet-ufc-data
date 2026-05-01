#!/usr/bin/env python3
"""
Add upcoming UFC events with complete fight cards
Based on screenshots provided
"""
import json
from datetime import datetime

# Events data from screenshots
events_to_add = [
    {
        "name": "UFC Fight Night: Della Maddalena vs Prates",
        "date": "2026-05-02",
        "location": "RAC Arena, Perth, Australia",
        "main_card": [
            {"fighter_a": "Jack Della Maddalena", "fighter_b": "Carlos Prates"},
            {"fighter_a": "Beneil Dariush", "fighter_b": "Quillan Salkilld"},
            {"fighter_a": "Tim Elliott", "fighter_b": "Steve Erceg"},
            {"fighter_a": "Marwan Rahiki", "fighter_b": "Ollie Schmid"},
            {"fighter_a": "Shamil Gaziev", "fighter_b": "Brando Pericic"},
            {"fighter_a": "Tai Tuivasa", "fighter_b": "Louie Sutherland"}
        ],
        "prelims": [
            {"fighter_a": "Cam Rowston", "fighter_b": "Robert Bryczek"},
            {"fighter_a": "Junior Tafa", "fighter_b": "Kevin Christian"},
            {"fighter_a": "Jacob Malkoun", "fighter_b": "Gerald Meerschaert"},
            {"fighter_a": "Colby Thicknesse", "fighter_b": "Vince Morales"},
            {"fighter_a": "Ben Johnston", "fighter_b": "Wes Schultz"},
            {"fighter_a": "Jonathan Micallef", "fighter_b": "Themba Gorimbo"},
            {"fighter_a": "Dom Mar Fan", "fighter_b": "Kody Steele"}
        ]
    },
    {
        "name": "UFC 328: Chimaev vs Strickland",
        "date": "2026-05-10",
        "location": "Prudential Center, Newark, NJ",
        "main_card": [
            {"fighter_a": "Khamzat Chimaev", "fighter_b": "Sean Strickland", "title_fight": True},
            {"fighter_a": "Joshua Van", "fighter_b": "Tatsuro Taira", "title_fight": True},
            {"fighter_a": "Alexander Volkov", "fighter_b": "Waldo Cortes-Acosta"},
            {"fighter_a": "Sean Brady", "fighter_b": "Joaquin Buckley"},
            {"fighter_a": "King Green", "fighter_b": "Jeremy Stephens"}
        ],
        "prelims": [
            {"fighter_a": "Ateba Gautier", "fighter_b": "Ozzy Diaz"},
            {"fighter_a": "Grant Dawson", "fighter_b": "Mateusz Rebecki"},
            {"fighter_a": "Yaroslav Amosov", "fighter_b": "Joel Alvarez"},
            {"fighter_a": "Roman Kopylov", "fighter_b": "Marco Tulio"},
            {"fighter_a": "Pat Sabatini", "fighter_b": "William Gomis"},
            {"fighter_a": "Baisangur Susurkaev", "fighter_b": "Djorden Santos"},
            {"fighter_a": "Clayton Carpenter", "fighter_b": "Jose Ochoa"},
            {"fighter_a": "Jim Miller", "fighter_b": "Jared Gordon"}
        ]
    },
    {
        "name": "UFC Macau: Song vs Figueiredo",
        "date": "2026-05-30",
        "location": "Galaxy Arena, Macao",
        "main_card": [
            {"fighter_a": "Song Yadong", "fighter_b": "Deiveson Figueiredo"},
            {"fighter_a": "Zhang Mingyang", "fighter_b": "Alonzo Menifield"},
            {"fighter_a": "Sergei Pavlovich", "fighter_b": "Tallison Teixeira"}
        ],
        "prelims": []
    }
]

# Collect all unique fighters
all_fighters = set()
for event in events_to_add:
    for card_type in ['main_card', 'prelims']:
        for fight in event.get(card_type, []):
            all_fighters.add(fight['fighter_a'])
            all_fighters.add(fight['fighter_b'])

print("="*70)
print("UPCOMING EVENTS TO ADD")
print("="*70)

for event in events_to_add:
    total_fights = len(event.get('main_card', [])) + len(event.get('prelims', []))
    print(f"\n📅 {event['name']}")
    print(f"   Date: {event['date']}")
    print(f"   Location: {event['location']}")
    print(f"   Total fights: {total_fights}")

print(f"\n" + "="*70)
print(f"👥 Total unique fighters needed: {len(all_fighters)}")
print("="*70)

# Check which fighters exist in database
with open('fighters.json', 'r') as f:
    fighters_data = json.load(f)

fighters = fighters_data.get('fighters', [])
found = []
missing = []

for name in sorted(all_fighters):
    # Search for fighter
    found_fighter = None
    for f in fighters:
        if name.lower() in f.get('name', '').lower():
            found_fighter = f
            break
    
    if found_fighter:
        found.append({
            'name': name,
            'record': f"{found_fighter.get('record_wins', 0)}-{found_fighter.get('record_losses', 0)}-{found_fighter.get('record_draws', 0)}",
            'has_stats': found_fighter.get('slpm') is not None
        })
    else:
        missing.append(name)

print(f"\n✅ Fighters found: {len(found)}/{len(all_fighters)}")
print(f"❌ Fighters missing: {len(missing)}")

if missing:
    print(f"\n   Missing fighters:")
    for name in missing:
        print(f"   - {name}")

# Save events data
output = {
    "created_at": datetime.now().isoformat(),
    "total_events": len(events_to_add),
    "total_fighters_needed": len(all_fighters),
    "fighters_found": len(found),
    "fighters_missing": len(missing),
    "missing_fighters": missing,
    "events": events_to_add
}

with open('upcoming_events_new.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n💾 Saved to: upcoming_events_new.json")
print(f"\nNext step: Scrape {len(missing)} missing fighters" if missing else "\n✅ All fighters found! Ready to add to database.")
