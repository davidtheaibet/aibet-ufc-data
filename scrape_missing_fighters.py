#!/usr/bin/env python3
"""
Scraper to fetch missing fighter data from UFCStats.com
"""
import json
import time
from pathlib import Path
from typing import Dict, Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'requests', 'beautifulsoup4', '-q'])
    import requests
    from bs4 import BeautifulSoup


class FighterScraper:
    """Scrape fighter data from UFCStats.com"""
    
    BASE_URL = "http://www.ufcstats.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_fighter(self, name: str) -> Optional[str]:
        """Search for fighter and return their UFCStats URL"""
        search_url = f"{self.BASE_URL}/statistics/fighters/search"
        
        try:
            # UFCStats uses a query parameter for search
            response = self.session.get(
                f"{self.BASE_URL}/statistics/fighters",
                params={'query': name},
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for fighter links in results
            fighter_links = soup.find_all('a', class_='b-link')
            
            for link in fighter_links:
                if name.lower() in link.text.lower():
                    href = link.get('href')
                    if href:
                        return href if href.startswith('http') else f"{self.BASE_URL}{href}"
            
            return None
            
        except Exception as e:
            print(f"  Error searching for {name}: {e}")
            return None
    
    def parse_fighter_profile(self, url: str) -> Optional[Dict]:
        """Parse fighter profile page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            profile = {
                'url': url,
                'slpm': None,
                'sig_strike_acc': None,
                'sapm': None,
                'sig_strike_def': None,
                'td_avg': None,
                'td_acc': None,
                'td_def': None,
                'sub_avg': None,
            }
            
            # Parse record
            record_elem = soup.find('span', class_='b-content__title-record')
            if record_elem:
                record_text = record_elem.text.strip()
                # Format: "Record: 19-4-0"
                import re
                match = re.search(r'(\d+)-(\d+)-(\d+)', record_text)
                if match:
                    profile['record_wins'] = int(match.group(1))
                    profile['record_losses'] = int(match.group(2))
                    profile['record_draws'] = int(match.group(3))
            
            # Parse stats from the stats table
            stats_table = soup.find('div', class_='b-list__info-box')
            if stats_table:
                # Find all stat rows
                stat_rows = stats_table.find_all('li', class_='b-list__box-list-item')
                
                for row in stat_rows:
                    text = row.get_text(strip=True)
                    
                    # Striking stats
                    if 'SLpM' in text:
                        val = self._extract_number(text)
                        if val:
                            profile['slpm'] = val
                    elif 'Str. Acc.' in text:
                        val = self._extract_percentage(text)
                        if val:
                            profile['sig_strike_acc'] = val
                    elif 'SApM' in text:
                        val = self._extract_number(text)
                        if val:
                            profile['sapm'] = val
                    elif 'Str. Def' in text:
                        val = self._extract_percentage(text)
                        if val:
                            profile['sig_strike_def'] = val
                    
                    # Grappling stats
                    elif 'TD Avg.' in text:
                        val = self._extract_number(text)
                        if val:
                            profile['td_avg'] = val
                    elif 'TD Acc.' in text:
                        val = self._extract_percentage(text)
                        if val:
                            profile['td_acc'] = val
                    elif 'TD Def.' in text:
                        val = self._extract_percentage(text)
                        if val:
                            profile['td_def'] = val
                    elif 'Sub. Avg.' in text:
                        val = self._extract_number(text)
                        if val:
                            profile['sub_avg'] = val
            
            return profile
            
        except Exception as e:
            print(f"  Error parsing profile: {e}")
            return None
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        import re
        match = re.search(r'[\d.]+', text.replace(',', ''))
        return float(match.group()) if match else None
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage and convert to decimal"""
        import re
        match = re.search(r'(\d+)%', text)
        if match:
            return float(match.group(1)) / 100
        return None


def main():
    """Scrape data for missing fighters"""
    print("=" * 60)
    print("UFCStats Fighter Scraper")
    print("=" * 60)
    
    # Load missing fighters
    with open('missing_fighters.json') as f:
        missing = json.load(f)
    
    print(f"\nFighters to scrape: {len(missing)}")
    
    scraper = FighterScraper()
    scraped_data = []
    failed = []
    
    for i, fighter in enumerate(missing, 1):
        name = fighter['name']
        print(f"\n[{i}/{len(missing)}] Searching: {name}")
        
        # Search for fighter
        profile_url = scraper.search_fighter(name)
        
        if not profile_url:
            print(f"  ❌ Not found")
            failed.append(name)
            continue
        
        print(f"  Found: {profile_url}")
        
        # Parse profile
        profile = scraper.parse_fighter_profile(profile_url)
        
        if profile:
            # Merge with basic info
            fighter.update(profile)
            scraped_data.append(fighter)
            print(f"  ✅ Scraped stats")
        else:
            failed.append(name)
            print(f"  ⚠️  Could not parse stats")
        
        # Be nice to the server
        time.sleep(1)
    
    # Save results
    print("\n" + "=" * 60)
    print("Scraping Complete")
    print("=" * 60)
    print(f"Successfully scraped: {len(scraped_data)}")
    print(f"Failed: {len(failed)}")
    
    if scraped_data:
        with open('scraped_fighters.json', 'w') as f:
            json.dump(scraped_data, f, indent=2)
        print(f"\nSaved to scraped_fighters.json")
    
    if failed:
        with open('failed_fighters.json', 'w') as f:
            json.dump(failed, f, indent=2)
        print(f"Failed fighters saved to failed_fighters.json")


if __name__ == "__main__":
    main()
