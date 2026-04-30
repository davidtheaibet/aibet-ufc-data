#!/usr/bin/env python3
"""
Apify UFC Data Scraper
Fetches comprehensive fighter data to fill gaps in existing dataset
"""
import json
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime

# Apify API configuration
APIFY_API_BASE = "https://api.apify.com/v2"
ACTOR_ID = "PXKaP7ujdwAL2F443"  # The UFC API actor (lemur/ufc-api)

class ApifyUFCCollector:
    """Collect UFC data from Apify actor"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def run_actor(self, input_data: Dict) -> str:
        """Run the UFC API actor and return run ID"""
        url = f"{APIFY_API_BASE}/acts/{ACTOR_ID}/runs"
        
        response = requests.post(
            url,
            headers=self.headers,
            json=input_data
        )
        response.raise_for_status()
        
        run_data = response.json()
        run_id = run_data['data']['id']
        print(f"Started actor run: {run_id}")
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
            
            print(f"Run status: {status}")
            
            if status == "SUCCEEDED":
                return run_data
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Run failed with status: {status}")
            
            time.sleep(5)
        
        raise TimeoutError("Run did not complete within timeout")
    
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
            
            print(f"Fetched {len(all_items)} items so far...")
        
        return all_items
    
    def fetch_all_fighters(self) -> List[Dict]:
        """Fetch all fighters with detailed data"""
        print("Fetching all fighters...")
        
        input_data = {
            "endpoint": "fighters",
            "params": {
                "limit": 5000  # Get all fighters
            }
        }
        
        run_id = self.run_actor(input_data)
        run_data = self.wait_for_run(run_id)
        
        dataset_id = run_data['defaultDatasetId']
        fighters = self.get_dataset_items(dataset_id)
        
        print(f"Fetched {len(fighters)} fighters")
        return fighters
    
    def fetch_fighter_details(self, fighter_id: str) -> Dict:
        """Fetch detailed data for a specific fighter"""
        input_data = {
            "endpoint": "fighter/details",
            "params": {
                "id": fighter_id
            }
        }
        
        run_id = self.run_actor(input_data)
        run_data = self.wait_for_run(run_id)
        
        dataset_id = run_data['defaultDatasetId']
        items = self.get_dataset_items(dataset_id)
        
        return items[0] if items else None
    
    def fetch_fighter_fights(self, fighter_id: str) -> List[Dict]:
        """Fetch fight history for a fighter"""
        input_data = {
            "endpoint": "fighter/previousFights",
            "params": {
                "id": fighter_id,
                "limit": 100
            }
        }
        
        run_id = self.run_actor(input_data)
        run_data = self.wait_for_run(run_id)
        
        dataset_id = run_data['defaultDatasetId']
        fights = self.get_dataset_items(dataset_id)
        
        return fights
    
    def fetch_all_events(self) -> List[Dict]:
        """Fetch all UFC events"""
        print("Fetching all events...")
        
        input_data = {
            "endpoint": "events",
            "params": {
                "limit": 1000
            }
        }
        
        run_id = self.run_actor(input_data)
        run_data = self.wait_for_run(run_id)
        
        dataset_id = run_data['defaultDatasetId']
        events = self.get_dataset_items(dataset_id)
        
        print(f"Fetched {len(events)} events")
        return events
    
    def fetch_rankings(self) -> Dict:
        """Fetch current UFC rankings"""
        print("Fetching rankings...")
        
        input_data = {
            "endpoint": "rankings"
        }
        
        run_id = self.run_actor(input_data)
        run_data = self.wait_for_run(run_id)
        
        dataset_id = run_data['defaultDatasetId']
        rankings = self.get_dataset_items(dataset_id)
        
        return rankings[0] if rankings else None


def merge_with_existing(
    apify_fighters: List[Dict],
    existing_fighters_path: str
) -> List[Dict]:
    """Merge Apify data with existing fighters"""
    
    # Load existing fighters
    with open(existing_fighters_path) as f:
        existing_data = json.load(f)
        existing_fighters = {f['name']: f for f in existing_data.get('fighters', [])}
    
    print(f"Existing fighters: {len(existing_fighters)}")
    print(f"Apify fighters: {len(apify_fighters)}")
    
    merged = []
    updated_count = 0
    new_count = 0
    
    for apify_fighter in apify_fighters:
        name = apify_fighter.get('name')
        
        if name in existing_fighters:
            # Update existing fighter
            existing = existing_fighters[name]
            existing.update({
                'slpm': apify_fighter.get('strikesPerMinute'),
                'sig_strike_acc': apify_fighter.get('significantStrikeAccuracy'),
                'sapm': apify_fighter.get('strikesAbsorbedPerMinute'),
                'sig_strike_def': apify_fighter.get('significantStrikeDefense'),
                'td_avg': apify_fighter.get('takedownAverage'),
                'td_acc': apify_fighter.get('takedownAccuracy'),
                'td_def': apify_fighter.get('takedownDefense'),
                'sub_avg': apify_fighter.get('submissionAverage'),
                'record_wins': apify_fighter.get('wins'),
                'record_losses': apify_fighter.get('losses'),
                'record_draws': apify_fighter.get('draws'),
                'weight_class': apify_fighter.get('weightClass'),
                'ufc_id': apify_fighter.get('id'),
                'apify_data': True,
                'last_updated': datetime.now().isoformat()
            })
            merged.append(existing)
            updated_count += 1
        else:
            # Add new fighter
            new_fighter = {
                'name': name,
                'slpm': apify_fighter.get('strikesPerMinute'),
                'sig_strike_acc': apify_fighter.get('significantStrikeAccuracy'),
                'sapm': apify_fighter.get('strikesAbsorbedPerMinute'),
                'sig_strike_def': apify_fighter.get('significantStrikeDefense'),
                'td_avg': apify_fighter.get('takedownAverage'),
                'td_acc': apify_fighter.get('takedownAccuracy'),
                'td_def': apify_fighter.get('takedownDefense'),
                'sub_avg': apify_fighter.get('submissionAverage'),
                'record_wins': apify_fighter.get('wins'),
                'record_losses': apify_fighter.get('losses'),
                'record_draws': apify_fighter.get('draws'),
                'weight_class': apify_fighter.get('weightClass'),
                'ufc_id': apify_fighter.get('id'),
                'apify_data': True,
                'source': 'apify_ufc_api',
                'added_date': datetime.now().isoformat()
            }
            merged.append(new_fighter)
            new_count += 1
    
    print(f"Updated: {updated_count}, New: {new_count}")
    return merged


def main():
    """Main execution"""
    import os
    
    # Get API token from environment
    api_token = os.getenv('APIFY_API_TOKEN')
    if not api_token:
        print("Error: Set APIFY_API_TOKEN environment variable")
        return
    
    collector = ApifyUFCCollector(api_token)
    
    # Fetch all fighters
    fighters = collector.fetch_all_fighters()
    
    # Save raw data
    with open('apify_fighters_raw.json', 'w') as f:
        json.dump(fighters, f, indent=2)
    
    print(f"Saved raw data: {len(fighters)} fighters")
    
    # Merge with existing
    merged = merge_with_existing(
        fighters,
        '/Users/zacharyreid/Documents/GitHub/aibet-ufc-data/fighters.json'
    )
    
    # Save merged data
    output = {
        'metadata': {
            'count': len(merged),
            'source': 'ufcstats.com + apify_ufc_api',
            'last_updated': datetime.now().isoformat(),
            'apify_fighters': len(fighters)
        },
        'fighters': merged
    }
    
    with open('fighters_enriched.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Saved enriched data: {len(merged)} fighters")


if __name__ == "__main__":
    main()
