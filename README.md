# AIbet UFC Data Repository

**Purpose:** Dedicated UFC data infrastructure for AIbet betting prediction platform

**Repository:** `davidtheaibet/aibet-ufc-data`

---

## 📊 Datasets

| Dataset | Count | File | Description |
|---------|-------|------|-------------|
| **Fighters** | 4,346 | `fighters.json` | Master fighter database with stats |
| **Historical Events** | 24 | `events.json` | Past UFC events |
| **Historical Fights** | 296 | `fight-history.json` | Fight results and stats |
| **Upcoming Events** | 8 | `upcoming-events.json` | Events Mar-May 2026 |
| **Fighter Histories** | 488 | `fighter-histories.json` | Last 5+ fights per fighter |

## 🔍 Data Gaps (gaps/ directory)

| File | Purpose |
|------|---------|
| `fighter-gaps.json` | Missing data tracking per fighter |
| `weight-class-history.json` | Fighter weight class movements |
| `regional-records.json` | Non-UFC fight history |
| `physical-metrics.json` | Power/strength data |
| `data-completeness-tracker.json` | 82% overall complete |

## 🤖 Analysis Engine

**File:** `analysis_engine.py`

**Metrics Calculated:**
1. **Striking** - Volume, accuracy, defense
2. **Grappling** - Takedowns, submissions
3. **Experience** - Fight count, UFC tenure
4. **Form** - Recent performance trend
5. **Finish Threat** - KO/submission capability

**Output:**
- Win probability with confidence (High/Medium/Low)
- Predicted finish method
- Key matchup advantages

## ⚠️ Critical Lesson

**Weight class accuracy matters more than pure stats.**

The Holloway vs Oliveira 2 prediction failed because:
- Holloway was fighting at Lightweight (not his natural Featherweight)
- Strength/power differential was ignored
- Pure striking volume model didn't account for physical disadvantages

**Always check:**
- Fighter's natural weight class
- Weight class history
- Physical transformations

## 🔄 Integration Notes for Dev Team

1. Pull fighter data from `fighters.json` for matchups
2. Use `analysis_engine.py` logic for predictions
3. Weight class history is in `gaps/weight-class-history.json`
4. Post-fight stats will be added to `fight-history.json`

## 📅 Last Updated

March 12, 2026

## 📝 Data Sources

- UFC Stats (official)
- UFC.com
- Tapology
- Sherdog
