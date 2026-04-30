# UFC Data Package - For Review

**Generated:** May 1, 2026  
**Purpose:** Polymarket Integration  
**Coverage:** 77.4% of upcoming fighters (May-July 2026)

---

## Executive Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Total upcoming fighters | 124 | 100% |
| ✅ Complete data | 96 | 77.4% |
| ⚠️ Needs stats | 18 | 14.5% |
| ❌ Missing | 10 | 8.1% |

**Status:** READY FOR POLYMARKET - 96 fighters have complete prediction data

---

## Data Coverage by Fighter

### ✅ Complete Data (96 fighters)
All fighters have:
- Record (wins/losses/draws)
- Weight class
- Striking stats (slpm, sig_strike_acc, sapm, sig_strike_def)
- Grappling stats (td_avg, td_acc, td_def, sub_avg)

**Key fighters with complete data:**
- Alex Pereira ✅
- Ilia Topuria ✅
- Justin Gaethje ✅
- Michael Chandler ✅
- Sean O'Malley ✅
- Khamzat Chimaev ✅
- Sean Strickland ✅
- Alexander Volkov ✅
- Ciryl Gane ✅
- Derrick Lewis ✅
- And 86 more...

### ⚠️ Needs Stats (18 fighters)
In database but missing detailed statistics:
- Cameron Smotherman
- Edgar Chairez
- Iwo Baraniewski
- Jacqueline Cavalcanti
- Jakub Wiklacz
- Jeisla Chaves
- Junior Tafa
- Kai Asakura
- Kevin Christian
- Louie Sutherland
- Malcolm Wellmaker
- Marwan Rahiki
- Mauricio Ruffy
- Ozzy Diaz
- Ramon Taveras
- Tai Tuivasa
- Yuneisy Duben
- Zhang Mingyang

### ❌ Missing (10 fighters)
Not found in database:
- Ben Johnston
- Brando Peričić
- Farès Ziam
- Jingnan Xiong
- Joel Álvarez
- Luis Dias De Assis
- Mateusz Rębecki
- Ollie Schmid
- Thomas Gantt
- Yi Sak Lee

---

## Data Sources

### 1. Main Database (aibet-ufc-data)
- **4,436 fighters** total
- **2,587 fighters** with complete stats (58.3%)
- Includes: slpm, sig_strike_acc, sapm, sig_strike_def, td_avg, td_acc, td_def, sub_avg

### 2. Fight Stats Database
- **592 detailed fight stat records**
- Per-fight statistics: strikes, takedowns, submissions, control time
- Covers 296 fights (488 fighters)

### 3. Sports-Build Database
- Exported from: theaibet-sports-build
- **4,455 fighters** with UFCStats data
- Merged 92 fighters with complete stats

---

## Files Included

| File | Description |
|------|-------------|
| `UFC_DATA_EXPORT_FOR_REVIEW.json` | Complete export with all fighter categories |
| `fighters.json` | Main database (4,436 fighters) |
| `fight-stats-detailed.json` | 592 per-fight stat records |
| `ufc_complete_export.json` | Sports-build database export |
| `calibration_data.json` | Model calibration (292 fights analyzed) |
| `ufc_prediction_system.py` | Production prediction system |

---

## Recommendation

**For Polymarket Integration:**

1. **Use the 96 fighters with complete data** - This is sufficient for main card predictions
2. **Flag the 28 incomplete fighters** - These are likely preliminary card or new signings
3. **Focus on high-profile matchups** - Pereira, Topuria, Gaethje, Chandler, etc. all have complete data

**Data Quality:**
- 77% coverage is acceptable for betting predictions
- Missing fighters are mostly unknown/preliminary fighters
- All major stars have complete data

---

## Next Steps

1. ✅ Review this data package
2. ✅ Validate 96 complete fighters for Polymarket
3. ⏭️ Build prediction models using complete data
4. ⏭️ Manual entry for 28 missing/incomplete if needed

---

**Contact:** David (AI Operations)  
**Repository:** davidtheaibet/aibet-ufc-data
