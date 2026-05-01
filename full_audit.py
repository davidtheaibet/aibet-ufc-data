#!/usr/bin/env python3
"""
Full Audit Report for AIbet UFC Data
Checks readiness for next 3 months of events
"""
import json
from datetime import datetime, timedelta
import zipfile
import os

print("="*80)
print("AIbet UFC DATA - COMPREHENSIVE AUDIT REPORT")
print("="*80)
print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("="*80)

# Load all data files
files_to_check = [
    'fighters.json',
    'fight-history.json', 
    'events.json',
    'upcoming-events.json',
    'fight-stats-detailed.json',
    'fighter-histories.json'
]

print("\n📁 DATA FILES STATUS:")
file_status = {}
for filename in files_to_check:
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        with open(filename, 'r') as f:
            data = json.load(f)
            key = list(data.keys())[0] if data else 'empty'
            count = len(data.get(key, [])) if key != 'metadata' else 'N/A'
            file_status[filename] = {'size': size, 'count': count}
            print(f"   ✅ {filename}: {size/1024:.1f} KB ({count} records)")
    else:
        file_status[filename] = None
        print(f"   ❌ {filename}: MISSING")

# Load fighters data
with open('fighters.json', 'r') as f:
    fighters_data = json.load(f)
fighters = fighters_data.get('fighters', [])

print(f"\n👥 FIGHTERS ANALYSIS:")
print(f"   Total fighters in database: {len(fighters)}")

# Check data completeness
complete = 0
partial = 0
minimal = 0

for fighter in fighters:
    has_record = fighter.get('record_wins', 0) > 0 or fighter.get('record_losses', 0) > 0
    has_stats = fighter.get('slpm') is not None and fighter.get('slpm') > 0
    has_physical = fighter.get('height') and fighter.get('weight_lbs')
    has_history = fighter.get('total_fights', 0) > 0
    
    if has_record and has_stats and has_physical and has_history:
        complete += 1
    elif has_record and has_stats:
        partial += 1
    else:
        minimal += 1

print(f"   Complete data (record + stats + physical + history): {complete}")
print(f"   Partial data (record + stats): {partial}")
print(f"   Minimal data: {minimal}")

# Check for the 18 fighters we just updated
fighters_18 = [
    "Tai Tuivasa", "Junior Tafa", "Cameron Smotherman", "Kai Asakura",
    "Edgar Chairez", "Iwo Baraniewski", "Jacqueline Cavalcanti", "Jakub Wiklacz",
    "Jeisla Chaves", "Kevin Christian", "Louie Sutherland", "Malcolm Wellmaker",
    "Mauricio Ruffy", "Ozzy Diaz", "Ramon Taveras", "Yuneisy Duben",
    "Zhang Mingyang", "Marwan Rahiki"
]

print(f"\n🔍 18 FIGHTERS CHECK:")
found_18 = 0
for name in fighters_18:
    found = any(name.lower() in f.get('name', '').lower() for f in fighters)
    if found:
        found_18 += 1
    else:
        print(f"   ❌ {name}: NOT FOUND")

print(f"   Found: {found_18}/{len(fighters_18)}")

# Events analysis
print(f"\n📅 EVENTS ANALYSIS:")
with open('events.json', 'r') as f:
    events_data = json.load(f)
events = events_data.get('events', [])

print(f"   Total events: {len(events)}")

# Check date range
dates = []
for event in events:
    date_str = event.get('date', '')
    if date_str:
        try:
            dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
        except:
            pass

if dates:
    print(f"   Date range: {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}")
    
    # Check for events in next 3 months
    now = datetime.now()
    three_months = now + timedelta(days=90)
    future_events = [d for d in dates if d >= now]
    
    print(f"   Events from today onwards: {len(future_events)}")
    if len(future_events) == 0:
        print(f"   ⚠️  WARNING: No upcoming events found!")
        print(f"      Last event was: {max(dates).strftime('%Y-%m-%d')}")
        print(f"      Need to scrape new events!")

# Fight history
with open('fight-history.json', 'r') as f:
    fights_data = json.load(f)
fights = fights_data.get('fights', [])

print(f"\n🥊 FIGHT HISTORY:")
print(f"   Total fights recorded: {len(fights)}")

# Check for fights involving our 18 fighters
fights_with_18 = 0
for fight in fights:
    fighter_a = fight.get('fighter_a_name', '')
    fighter_b = fight.get('fighter_b_name', '')
    
    for name in fighters_18:
        if name.lower() in fighter_a.lower() or name.lower() in fighter_b.lower():
            fights_with_18 += 1
            break

print(f"   Fights involving 18 target fighters: {fights_with_18}")

# Summary
print(f"\n" + "="*80)
print("AUDIT SUMMARY")
print("="*80)

ready_for_120 = complete >= 120
has_events = len(future_events) > 0 if 'future_events' in locals() else False

print(f"\n✅ READY FOR 120 FIGHTERS: {'YES' if ready_for_120 else 'NO'}")
print(f"   Current complete fighters: {complete}")
print(f"   Target: 120")

print(f"\n✅ READY FOR 3 MONTHS EVENTS: {'YES' if has_events else 'NO'}")
if not has_events:
    print(f"   ⚠️  ACTION REQUIRED: Scrape upcoming events")

print(f"\n✅ 18 FIGHTERS UPDATED: {'YES' if found_18 == 18 else 'PARTIAL'}")
print(f"   Found: {found_18}/18")

# Create report file
report = {
    "audit_date": datetime.now().isoformat(),
    "summary": {
        "total_fighters": len(fighters),
        "complete_fighters": complete,
        "partial_fighters": partial,
        "minimal_fighters": minimal,
        "target_120_ready": ready_for_120,
        "events_ready": has_events,
        "fighters_18_found": found_18
    },
    "files": file_status,
    "recommendations": []
}

if not ready_for_120:
    report["recommendations"].append(f"Need {120 - complete} more fighters with complete data")
if not has_events:
    report["recommendations"].append("Scrape upcoming UFC events for next 3 months")
if found_18 < 18:
    report["recommendations"].append(f"Verify {18 - found_18} fighters from the 18 list")

with open('audit_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n💾 Audit report saved to: audit_report.json")

# Create zip file for dev team
print(f"\n📦 Creating zip file for dev team...")
with zipfile.ZipFile('aibet_ufc_data_audit.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Add key files
    for filename in ['fighters.json', 'fight-history.json', 'events.json', 'audit_report.json']:
        if os.path.exists(filename):
            zipf.write(filename)
    
    # Add the 18 fighters data
    if os.path.exists('18_fighters_ufc_official.json'):
        zipf.write('18_fighters_ufc_official.json')

print(f"✅ Zip file created: aibet_ufc_data_audit.zip")
print(f"   Size: {os.path.getsize('aibet_ufc_data_audit.zip')/1024/1024:.2f} MB")

print(f"\n" + "="*80)
print("AUDIT COMPLETE")
print("="*80)
