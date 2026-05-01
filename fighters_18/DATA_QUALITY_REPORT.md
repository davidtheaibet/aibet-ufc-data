# 18 Fighters Collection - Data Quality Report

**Collection Date:** 2026-05-01  
**Total Fighters:** 18

## Summary

- ✅ **16 fighters with complete records**
- ⚠️ **2 fighters with incomplete records (database issue)**

## Complete Records (16 fighters)

| Fighter | Record | Weight Class | Status |
|---------|--------|--------------|--------|
| Cameron Smotherman | 12-6-0 | N/A | ✅ Complete |
| Edgar Chairez | 13-6-0 | Flyweight | ✅ Complete |
| Iwo Baraniewski | 7-0-0 | Light Heavyweight | ✅ Complete |
| Jacqueline Cavalcanti | 10-1-0 | Bantamweight | ✅ Complete |
| Jakub Wiklacz | 2-0-0 | N/A | ✅ Complete |
| Jeisla Chaves | 7-0-0 | N/A | ✅ Complete |
| Kai Asakura | 21-6-0 | Flyweight | ✅ Complete |
| Kevin Christian | 9-3-0 | Light Heavyweight | ✅ Complete |
| Louie Sutherland | 10-4-0 | Heavyweight | ✅ Complete |
| Malcolm Wellmaker | 10-1-0 | Bantamweight | ✅ Complete |
| Marwan Rahiki | 7-0-0 | N/A | ✅ Complete |
| Mauricio Ruffy | 1-1-0 | N/A | ✅ Complete |
| Ozzy Diaz | 10-3-0 | N/A | ✅ Complete |
| Ramon Taveras | 10-4-0 | Featherweight | ✅ Complete |
| Yuneisy Duben | 6-1-0 | N/A | ✅ Complete |
| Zhang Mingyang | 19-7-0 | Light Heavyweight | ✅ Complete |

## Incomplete Records (2 fighters) ⚠️

| Fighter | Database Shows | Should Be | Issue |
|---------|----------------|-----------|-------|
| **Tai Tuivasa** | 0-1-0 | ~14-7 | Database only has recent UFC fight |
| **Junior Tafa** | 0-1-0 | More fights | Database only has recent UFC fight |

### Explanation

These two fighters have incomplete records in the source database (fighters.json). The database only captured their most recent UFC fights instead of their complete career records.

**Tai Tuivasa** is an established UFC heavyweight with approximately 14 wins and 7 losses in his career.

**Junior Tafa** has more fights than the 0-1 shown in the database.

### Recommendation

These fighters need to be re-scraped from UFCStats.com to get their complete career records. The current data shows only their most recent UFC appearance.

## Data Files

- `18_fighters_collection.json` - Complete collection with all 18 fighters
- `fighters_18/` - Individual JSON files for each fighter
- `DATA_QUALITY_REPORT.md` - This file

## Collection Method

Data extracted from existing aibet-ufc-data repository (fighters.json, fight-history.json). Records reflect what's currently in the database.

## Next Steps

1. Re-scrape Tai Tuivasa and Junior Tafa from UFCStats.com for complete records
2. Update fighters.json with corrected data
3. Re-run extraction to update this collection
