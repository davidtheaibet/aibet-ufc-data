#!/usr/bin/env python3
"""
UFC Upcoming Events Scraper
Fetches upcoming events from UFCStats.com with ufc_id and fighter details
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "http://www.ufcstats.com"
UPCOMING_URL = f"{BASE_URL}/statistics/events/upcoming"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def parse_event_date(date_str):
    """Parse various date formats"""
    formats = [
        '%B %d, %Y',
        '%b %d, %Y',
        '%Y-%m-%d',
        '%m/%d/%Y'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except:
            continue
    return date_str

def extract_fighter_name(name_str):
    """Clean fighter name"""
    return name_str.strip() if name_str else None

def scrape_upcoming_events():
    """Scrape upcoming events list from UFCStats"""
    print("🔍 Fetching upcoming events from UFCStats...")
    
    response = requests.get(UPCOMING_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    events = []
    
    # Find event rows
    event_rows = soup.find_all('tr', class_='b-statistics__table-row')
    
    for row in event_rows:
        try:
            # Skip header rows
            if 'b-statistics__table-row_type_head' in row.get('class', []):
                continue
            
            # Extract event link and name
            event_link = row.find('a', class_='b-link_style_white')
            if not event_link:
                continue
            
            event_name = event_link.text.strip()
            event_url = event_link.get('href', '')
            
            # Extract ufc_id from URL
            # URL format: http://www.ufcstats.com/event-details/xxxxx
            ufc_id = None
            if '/event-details/' in event_url:
                ufc_id = event_url.split('/event-details/')[-1].split('?')[0]
            
            # Extract date
            date_cell = row.find('span', class_='b-statistics__date')
            event_date = parse_event_date(date_cell.text) if date_cell else None
            
            # Extract location
            location_cell = row.find('td', class_='b-statistics__table-col_l-align_left')
            location = location_cell.text.strip() if location_cell else None
            
            events.append({
                'ufc_id': ufc_id,
                'name': event_name,
                'date': event_date,
                'location': location,
                'url': event_url if event_url.startswith('http') else urljoin(BASE_URL, event_url),
                'status': 'upcoming'
            })
            
        except Exception as e:
            print(f"⚠️ Error parsing event row: {e}")
            continue
    
    print(f"✅ Found {len(events)} upcoming events")
    return events

def scrape_event_fights(event_url):
    """Scrape fight card for a specific event"""
    print(f"🔍 Fetching fights from {event_url}...")
    
    try:
        response = requests.get(event_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {event_url}: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    fights = []
    
    # Find fight rows
    fight_rows = soup.find_all('tr', class_='b-fight-details__table-row')
    
    for idx, row in enumerate(fight_rows, 1):
        try:
            # Skip header rows
            if 'b-fight-details__table-row_type_head' in row.get('class', []):
                continue
            
            # Extract fighter names
            fighter_links = row.find_all('a', class_='b-link_style_black')
            if len(fighter_links) < 2:
                continue
            
            fighter_a = extract_fighter_name(fighter_links[0].text)
            fighter_b = extract_fighter_name(fighter_links[1].text)
            
            # Extract weight class
            weight_class_cell = row.find('td', class_='b-fight-details__table-col_style_align-left')
            weight_class = weight_class_cell.text.strip() if weight_class_cell else None
            
            # Check if main event (first fight listed is usually main event)
            is_main_event = (idx == 1)
            
            # Extract method/result if available
            method_cell = row.find('td', class_='b-fight-details__table-col_style_align-left')
            method = None
            if method_cell:
                method_text = method_cell.text.strip()
                if method_text and len(method_text) < 50:  # Not a fighter name
                    method = method_text
            
            fights.append({
                'position': idx,
                'fighter_a': fighter_a,
                'fighter_b': fighter_b,
                'weight_class': weight_class,
                'is_main_event': is_main_event,
                'method': method
            })
            
        except Exception as e:
            print(f"⚠️ Error parsing fight row: {e}")
            continue
    
    print(f"✅ Found {len(fights)} fights")
    return fights

def merge_with_existing_data(new_events, existing_file='upcoming-events.json'):
    """Merge new scraped data with existing upcoming-events.json"""
    try:
        with open(existing_file, 'r') as f:
            existing = json.load(f)
            existing_events = existing.get('upcoming_events', [])
    except:
        existing_events = []
    
    # Create lookup by name + date
    existing_lookup = {}
    for evt in existing_events:
        key = f"{evt.get('name', '')}_{evt.get('date', '')}"
        existing_lookup[key] = evt
    
    # Merge data
    merged = []
    for new_evt in new_events:
        key = f"{new_evt['name']}_{new_evt['date']}"
        existing = existing_lookup.get(key, {})
        
        # Prefer new data for ufc_id, url
        # Keep existing data for main_card/prelims if not in new data
        merged_evt = {
            'id': existing.get('id') or f"ufc-{new_evt['ufc_id']}" if new_evt['ufc_id'] else key.replace(' ', '-').lower(),
            'ufc_id': new_evt['ufc_id'],
            'name': new_evt['name'],
            'date': new_evt['date'],
            'location': new_evt['location'] or existing.get('location'),
            'venue': existing.get('venue'),
            'url': new_evt['url'],
            'status': 'upcoming',
            'is_ppv': existing.get('is_ppv', False),
            'is_fight_night': existing.get('is_fight_night', True),
            'main_card': existing.get('main_card', []),
            'prelims': existing.get('prelims', []),
            'scraped_fights': new_evt.get('fights', [])
        }
        merged.append(merged_evt)
    
    return merged

def main():
    print("=" * 60)
    print("UFC Upcoming Events Scraper")
    print("=" * 60)
    
    # Step 1: Get upcoming events list
    events = scrape_upcoming_events()
    
    if not events:
        print("❌ No upcoming events found")
        return
    
    # Step 2: Get fight details for each event
    for event in events[:3]:  # Limit to first 3 to avoid rate limiting
        print(f"\n📅 Processing: {event['name']}")
        fights = scrape_event_fights(event['url'])
        event['fights'] = fights
    
    # Step 3: Merge with existing data
    print("\n🔄 Merging with existing data...")
    merged = merge_with_existing_data(events)
    
    # Step 4: Save output
    output = {
        'metadata': {
            'exported_at': datetime.now().isoformat(),
            'source': 'ufcstats.com',
            'count': len(merged),
            'scraper_version': '1.0'
        },
        'upcoming_events': merged
    }
    
    output_file = 'upcoming-events-enhanced.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved {len(merged)} events to {output_file}")
    print(f"📁 Full path: {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for evt in merged:
        print(f"\n🥊 {evt['name']}")
        print(f"   Date: {evt['date']}")
        print(f"   ufc_id: {evt['ufc_id']}")
        print(f"   Fights: {len(evt.get('scraped_fights', []))}")
        print(f"   URL: {evt['url']}")

if __name__ == '__main__':
    main()
