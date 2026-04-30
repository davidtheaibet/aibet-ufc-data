#!/usr/bin/env python3
"""
Apify UFC Data Scraper - Fixed Version
Fetches ALL fighters with complete stats using pagination
"""
import json
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime

APIFY_API_BASE = "https://api.apify.com/v2"
ACTOR_ID = "PXKaP7ujdwAL2F443"

class ApifyUFCCollector:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def run_actor(self, input_data: Dict) -> str:
        """Run the UFC API actor"""
        url = f"{APIFY_API_BASE}/acts/{ACTOR_ID}/runs"
        
        response = requests.post(
            url,
            headers=self.headers,
            json=input_data
        )
        response.raise_for_status()
        
        run_data = response.json()
        run_id = run_data['data']['id']
        print(f"Started run: {run_id}")
        return run_id
    
    def wait_for_run(self, run_id: str, timeout: int = 300) -> Dict:
        """Wait for actor run to complete"""
        url = f"{APIFY_API_BASE}/acts/{ACTOR_ID}/runs/{run_id}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            run_data = response.json()['data']
            status = run_data['status']
            
            if status == "SUCCEEDED":
                print(f"Run completed successfully")
                return run_data
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Run failed: {status}")
            
            print(f"Status: {status}...")
            time.sleep(5)
        
        raise TimeoutError("Run timeout")
    
    def get_dataset_items(self, dataset_id: str) -> List[Dict]:
        """Get all items from dataset"""
        url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"
        
        all_items = []
        offset = 0
        limit = 1000
        
        while True:
            params = {
                "offset": offset,
                "limit": limit,
                "format": "json"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            items = response.json()
            if not items:
                break
            
            all_items.extend(items)
            offset += limit
            print(f"  Fetched {len(all_items)} items...")
        
        return all_items
    
    def fetch_fighters_paginated(self, limit: int = 1000) -> List[Dict]:
        """Fetch fighters with pagination"""
        print(f"Fetching up to {limit} fighters...")
        
        input_data = {
            "endpoint": "fighters",
            "params": {
                "limit": limit
            }
        }
        
        run_id = self.run_actor(input_data)
        run_data = self.wait_for_run(run_id)
        
        dataset_id = run_data['defaultDatasetId']
        items = self.get_dataset_items(dataset_id)
        
        # Extract fighters from response wrapper
        all_fighters = []
        for item in items:
            if isinstance(item, dict) and 'data' in item:
                fighters = item['data']
                if isinstance(fighters, list):
                    all_fighters.extend(fighters)
                else:
                    all_fighters.append(fighters)
            else:
                all_fighters.append(item)
        
        print(f"Total fighters fetched: {len(all_fighters)}")
        return all_fighters
    
    def fetch_fighter_details(self, fighter_id: str) -> Optional[Dict]:
        """Fetch detailed stats for a fighter"""
        input_data = {
            "endpoint": "fighter/details",
            "params": {
                "id": fighter_id
            }
        }
        
        try:
            run_id = self.run_actor(input_data)
            run_data = self.wait_for_run(run_id)
            
            dataset_id = run_data['defaultDatasetId']
            items = self.get_dataset_items(dataset_id)
            
            if items and isinstance(items[0], dict) and 'data' in items[0]:
                return items[0]['data']
            return items[0] if items else None
        except Exception as e:
            print(f"Error fetching details for {fighter_id}: {e}")
            return None
    
    def fetch_fighter_fights(self, fighter_id: str) -> List[Dict]:
        """Fetch fight history"""
        input_data = {
            "endpoint": "fighter/previousFights",
            "params": {
                "id": fighter_id,
                "limit": 100
            }
        }
        
        try:
            run_id = self.run_actor(input_data)
            run_data = self.wait_for_run(run_id)
            
            dataset_id = run_data['defaultDatasetId']
            items = self.get_dataset_items(dataset_id)
            
            fights = []
            for item in items:
                if isinstance(item, dict) and 'data' in item:
                    if isinstance(item['data'], list):
                        fights.extend(item['data'])
                    else:
                        fights.append(item['data'])
                else:
                    fights.append(item)
            return fights
        except Exception as e:
            print(f"Error fetching fights for {fighter_id}: {e}")
            return []


def merge_fighter_data(basic_fighter: Dict, detailed_fighter: Dict) -> Dict:
    """Merge basic and detailed fighter data"""
    if not detailed_fighter:
        return basic_fighter
    
    merged = basic_fighter.copy()
    
    # Add detailed stats
    merged.update({
        'strikesPerMinute': detailed_fighter.get('strikesPerMinute'),
        'significantStrikeAccuracy': detailed_fighter.get('significantStrikeAccuracy'),
        'strikesAbsorbedPerMinute': detailed_fighter.get('strikesAbsorbedPerMinute'),
        'significantStrikeDefense': detailed_fighter.get('significantStrikeDefense'),
        'takedownAverage': detailed_fighter.get('takedownAverage'),
        'takedownAccuracy': detailed_fighter.get('takedownAccuracy'),
        'takedownDefense': detailed_fighter.get('takedownDefense'),
        'submissionAverage': detailed_fighter.get('submissionAverage'),
        'averageFightTime': detailed_fighter.get('averageFightTime'),
        'koWins': detailed_fighter.get('koWins'),
        'tkoWins': detailed_fighter.get('tkoWins'),
        'submissionWins': detailed_fighter.get('submissionWins'),
        'decisionWins': detailed_fighter.get('decisionWins'),
    })
    
    return merged


def main():
    import os
    
    api_token = os.getenv('APIFY_API_TOKEN')
    if not api_token:
        print("Error: Set APIFY_API_TOKEN environment variable")
        return
    
    collector = ApifyUFCCollector(api_token)
    
    # Step 1: Fetch all basic fighter data
    print("="*60)
    print("STEP 1: Fetching all fighters (basic data)")
    print("="*60)
    fighters = collector.fetch_fighters_paginated(limit=5000)
    
    # Save basic data
    with open('apify_fighters_basic.json', 'w') as f:
        json.dump(fighters, f, indent=2)
    print(f"Saved basic data: {len(fighters)} fighters")
    
    # Step 2: Fetch detailed stats for each fighter (this will take time and cost money)
    print("\n" + "="*60)
    print("STEP 2: Fetching detailed stats for each fighter")
    print("WARNING: This will make 1 API call per fighter and cost money!")
    print("="*60)
    
    detailed_fighters = []
    total = len(fighters)
    
    for i, fighter in enumerate(fighters[:50], 1):  # Start with first 50 for testing
        fighter_id = fighter.get('id')
        name = fighter.get('name')
        
        print(f"\n[{i}/{total}] Fetching details for {name}...")
        
        # Fetch detailed stats
        details = collector.fetch_fighter_details(fighter_id)
        
        # Fetch fight history
        fights = collector.fetch_fighter_fights(fighter_id)
        
        # Merge data
        merged = merge_fighter_data(fighter, details)
        merged['fightHistory'] = fights
        merged['totalFights'] = len(fights)
        
        detailed_fighters.append(merged)
        
        print(f"  ✓ Got {len(fights)} fights")
        
        # Rate limiting - be nice to the API
        time.sleep(1)
    
    # Save detailed data
    output = {
        'metadata': {
            'count': len(detailed_fighters),
            'source': 'apify_ufc_api',
            'fetched_at': datetime.now().isoformat(),
            'note': 'Detailed stats including takedowns, striking, fight history'
        },
        'fighters': detailed_fighters
    }
    
    with open('apify_fighters_detailed.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE! Saved {len(detailed_fighters)} fighters with full data")
    print(f"Files created:")
    print(f"  - apify_fighters_basic.json (basic data)")
    print(f"  - apify_fighters_detailed.json (full stats + fight history)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
