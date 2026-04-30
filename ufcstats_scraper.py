#!/usr/bin/env python3
"""
UFCStats.com Scraper - Complete Fighter Data
Gets all stats: striking, takedowns, submissions, fight history
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import Dict, List, Optional
from datetime import datetime

class UFCStatsScraper:
    """Scrape fighter data from UFCStats.com"""
    
    BASE_URL = "http://www.ufcstats.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.fighters_scraped = 0
    
    def search_fighter(self, name: str) -> Optional[str]:
        """Search for fighter and return their profile URL"""
        search_url = f"{self.BASE_URL}/statistics/fighters/search"
        
        try:
            response = self.session.get(
                search_url,
                params={'query': name},
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for fighter links
            fighter_links = soup.find_all('a', class_='b-link')
            
            for link in fighter_links:
                link_text = link.text.strip()
                if name.lower() in link_text.lower() or link_text.lower() in name.lower():
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
                'scraped_at': datetime.now().isoformat()
            }
            
            # Parse name
            name_elem = soup.find('span', class_='b-content__title-highlight')
            if name_elem:
                profile['name'] = name_elem.text.strip()
            
            # Parse record
            record_elem = soup.find('span', class_='b-content__title-record')
            if record_elem:
                record_text = record_elem.text.strip()
                match = re.search(r'(\d+)-(\d+)-(\d+)', record_text)
                if match:
                    profile['record_wins'] = int(match.group(1))
                    profile['record_losses'] = int(match.group(2))
                    profile['record_draws'] = int(match.group(3))
            
            # Parse stats from the stats table
            stats_table = soup.find('div', class_='b-list__info-box')
            if stats_table:
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
            
            # Parse physical attributes
            physical = soup.find('div', class_='b-list__info-box')
            if physical:
                rows = physical.find_all('li', class_='b-list__box-list-item')
                for row in rows:
                    text = row.get_text(strip=True)
                    if 'Height:' in text:
                        profile['height'] = text.split(':')[-1].strip()
                    elif 'Weight:' in text:
                        profile['weight'] = text.split(':')[-1].strip()
                    elif 'Reach:' in text:
                        profile['reach'] = text.split(':')[-1].strip()
                    elif 'Stance:' in text:
                        profile['stance'] = text.split(':')[-1].strip()
            
            self.fighters_scraped += 1
            return profile
            
        except Exception as e:
            print(f"  Error parsing profile: {e}")
            return None
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        match = re.search(r'[\d.]+', text.replace(',', ''))
        return float(match.group()) if match else None
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage and convert to decimal"""
        match = re.search(r'(\d+)%', text)
        if match:
            return float(match.group(1)) / 100
        return None
    
    def scrape_fighter(self, name: str) -> Optional[Dict]:
        """Scrape a single fighter by name"""
        print(f"[{self.fighters_scraped + 1}] Scraping: {name}")
        
        url = self.search_fighter(name)
        if not url:
            print(f"  ✗ Not found: {name}")
            return None
        
        print(f"  Found: {url}")
        
        profile = self.parse_fighter_profile(url)
        if profile:
            print(f"  ✓ Got stats: SLpM={profile.get('slpm')}, TD={profile.get('td_avg')}")
        else:
            print(f"  ✗ Failed to parse")
        
        # Be nice to the server
        time.sleep(1)
        
        return profile


def main():
    """Scrape all missing/upcoming fighters"""
    
    # Fighters that need data (from your audit)
    fighters_to_scrape = [
        # Missing fighters
        "Ben Johnston", "Brando Peričić", "Farès Ziam", "Jingnan Xiong",
        "Joel Álvarez", "Luis Dias De Assis", "Mateusz Rębecki",
        "Ollie Schmid", "Thomas Gantt", "Yi Sak Lee",
        # Needs stats
        "Cameron Smotherman", "Edgar Chairez", "Iwo Baraniewski",
        "Jacqueline Cavalcanti", "Jakub Wiklacz", "Jeisla Chaves",
        "Junior Tafa", "Kai Asakura", "Kevin Christian", "Louie Sutherland",
        "Malcolm Wellmaker", "Marwan Rahiki", "Mauricio Ruffy",
        "Ozzy Diaz", "Ramon Taveras", "Tai Tuivasa", "Yuneisy Duben", "Zhang Mingyang"
    ]
    
    print("="*70)
    print("UFCSTATS.COM SCRAPER - PRIORITY FIGHTERS")
    print("="*70)
    print(f"Fighters to scrape: {len(fighters_to_scrape)}")
    print()
    
    scraper = UFCStatsScraper()
    results = []
    failed = []
    
    for name in fighters_to_scrape:
        profile = scraper.scrape_fighter(name)
        if profile:
            results.append(profile)
        else:
            failed.append(name)
    
    # Save results
    output = {
        'metadata': {
            'total_attempted': len(fighters_to_scrape),
            'successful': len(results),
            'failed': len(failed),
            'scraped_at': datetime.now().isoformat(),
            'source': 'ufcstats.com'
        },
        'fighters': results,
        'failed': failed
    }
    
    with open('ufcstats_scraped_fighters.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "="*70)
    print("SCRAPING COMPLETE")
    print("="*70)
    print(f"Successful: {len(results)}/{len(fighters_to_scrape)}")
    print(f"Failed: {len(failed)}")
    print(f"\nSaved to: ufcstats_scraped_fighters.json")
    
    if failed:
        print(f"\nFailed fighters:")
        for name in failed:
            print(f"  - {name}")


if __name__ == "__main__":
    main()
