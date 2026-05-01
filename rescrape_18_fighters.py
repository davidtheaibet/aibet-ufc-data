#!/usr/bin/env python3
"""
Rescrape all 18 fighters with complete accurate data from UFCStats.com
"""
import sys
sys.path.insert(0, '/Users/zacharyreid/Documents/GitHub/aibet-ufc-data')

from ufcstats_scraper import UFCStatsScraper
import json
from datetime import datetime

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
    results = {
        'scraped_at': datetime.now().isoformat(),
        'fighters': [],
        'failed': []
    }
    
    print("Rescraping all 18 fighters from UFCStats.com...")
    print("="*70)
    
    for i, name in enumerate(FIGHTERS, 1):
        print(f"\n[{i}/18] {name}")
        
        try:
            # Search for fighter
            url = scraper.search_fighter(name)
            if not url:
                print(f"  ❌ Not found")
                results['failed'].append(name)
                continue
            
            # Get full data
            data = scraper.get_fighter_data(url)
            if data:
                results['fighters'].append(data)
                record = data.get('record', 'N/A')
                print(f"  ✅ Record: {record}")
            else:
                print(f"  ❌ Failed to get data")
                results['failed'].append(name)
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results['failed'].append(name)
        
        # Delay between requests
        import time
        time.sleep(3)
    
    # Save results
    print("\n" + "="*70)
    print(f"Complete: {len(results['fighters'])}/18")
    
    with open('18_fighters_rescraped.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Saved to: 18_fighters_rescraped.json")

if __name__ == '__main__':
    main()
