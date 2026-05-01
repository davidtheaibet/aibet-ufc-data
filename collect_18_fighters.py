#!/usr/bin/env python3
"""
Collect detailed data for 18 specific UFC fighters
Uses UFCStats.com scraper
"""
import json
import sys
sys.path.insert(0, '/Users/zacharyreid/Documents/GitHub/aibet-ufc-data')

from ufcstats_scraper import UFCStatsScraper

# List of 18 fighters to collect
FIGHTERS = [
    "Cameron Smotherman",
    "Edgar Chairez", 
    "Iwo Baraniewski",
    "Jacqueline Cavalcanti",
    "Jakub Wiklacz",
    "Jeisla Chaves",
    "Junior Tafa",
    "Kai Asakura",
    "Kevin Christian",
    "Louie Sutherland",
    "Malcolm Wellmaker",
    "Marwan Rahiki",
    "Mauricio Ruffy",
    "Ozzy Diaz",
    "Ramon Taveras",
    "Tai Tuivasa",
    "Yuneisy Duben",
    "Zhang Mingyang"
]

def main():
    scraper = UFCStatsScraper()
    collected = []
    failed = []
    
    print(f"Collecting data for {len(FIGHTERS)} fighters...")
    print("=" * 60)
    
    for i, name in enumerate(FIGHTERS, 1):
        print(f"\n[{i}/{len(FIGHTERS)}] Searching: {name}")
        
        try:
            # Search for fighter
            profile_url = scraper.search_fighter(name)
            
            if not profile_url:
                print(f"  ❌ Not found: {name}")
                failed.append(name)
                continue
            
            print(f"  ✅ Found: {profile_url}")
            
            # Get detailed data
            fighter_data = scraper.get_fighter_data(profile_url)
            
            if fighter_data:
                collected.append(fighter_data)
                print(f"  ✅ Collected: {fighter_data.get('name')} ({fighter_data.get('record', 'N/A')})")
            else:
                print(f"  ❌ Failed to get data for: {name}")
                failed.append(name)
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed.append(name)
        
        # Be nice to the server
        import time
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print(f"Collection complete!")
    print(f"  ✅ Success: {len(collected)}")
    print(f"  ❌ Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed fighters:")
        for name in failed:
            print(f"  - {name}")
    
    # Save results
    output = {
        'collected_at': datetime.now().isoformat(),
        'total_requested': len(FIGHTERS),
        'total_collected': len(collected),
        'total_failed': len(failed),
        'failed_fighters': failed,
        'fighters': collected
    }
    
    with open('fighter_collection_18.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved to: fighter_collection_18.json")
    
    return collected, failed

if __name__ == '__main__':
    from datetime import datetime
    collected, failed = main()
