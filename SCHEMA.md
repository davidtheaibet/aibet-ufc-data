# AIbet UFC Data Schema Documentation

**Repository:** https://github.com/davidtheaibet/aibet-ufc-data

---

## File Structure

```
/ufc-data/
├── fighters.json              # Master fighter database
├── events.json                # Historical events
├── fight-history.json         # Historical fight results
├── upcoming-events.json       # Scheduled events
├── fighter-histories.json     # Recent fight records per fighter
├── analysis_engine.py         # Prediction logic
├── gaps/                      # Data completeness tracking
│   ├── weight-class-history.json
│   ├── physical-metrics.json
│   └── data-completeness-tracker.json
└── README.md
```

---

## fighters.json Schema

**Type:** Array of fighter objects

```json
{
  "id": 1234,
  "name": "Max Holloway",
  "nickname": "Blessed",
  "weight_class": "Featherweight",
  "weight_lbs": 145,
  "record_wins": 27,
  "record_losses": 8,
  "record_draws": 0,
  "height": "5'11\"",
  "reach": "69\"",
  "stance": "Orthodox",
  "nationality": "USA",
  "slpm": 7.20,
  "sig_strike_acc": 48,
  "sapm": 4.74,
  "sig_strike_def": 59,
  "td_avg": 0.24,
  "td_acc": 53,
  "td_def": 85,
  "sub_avg": 0.3,
  "last_fights": ["W-Decision", "L-KO", "W-Decision", "W-TKO", "L-Decision"]
}
```

**Field Definitions:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Unique fighter ID |
| `name` | String | Full name |
| `nickname` | String | Fighter nickname |
| `weight_class` | String | Current weight class |
| `weight_lbs` | Integer | Weight in pounds |
| `record_*` | Integer | Win/loss/draw record |
| `height` | String | Height (feet'inches") |
| `reach` | String | Reach in inches |
| `stance` | String | Orthodox/Southpaw/Switch |
| `slpm` | Float | Significant strikes landed per minute |
| `sig_strike_acc` | Integer | Striking accuracy % |
| `sapm` | Float | Significant strikes absorbed per minute |
| `sig_strike_def` | Integer | Striking defense % |
| `td_avg` | Float | Takedown average per 15 min |
| `td_acc` | Integer | Takedown accuracy % |
| `td_def` | Integer | Takedown defense % |
| `sub_avg` | Float | Submission attempts per 15 min |
| `last_fights` | Array | Last 5 fights [Result-Method] |

---

## events.json Schema

**Type:** Array of event objects

```json
{
  "id": "ufc-327",
  "name": "UFC 327: Prochazka vs Ulberg",
  "date": "2026-04-12",
  "location": "Miami, FL",
  "venue": "Kaseya Center",
  "fights": [
    {
      "fight_id": "f-1234",
      "fighter_a": "Jiri Prochazka",
      "fighter_b": "Carlos Ulberg",
      "weight_class": "Light Heavyweight",
      "is_main_event": true,
      "result": null,
      "winner": null,
      "method": null,
      "round": null,
      "time": null
    }
  ]
}
```

---

## upcoming-events.json Schema

Same as events.json but for scheduled future events.

---

## fight-history.json Schema

**Type:** Array of completed fight objects

```json
{
  "fight_id": "f-5678",
  "event_id": "ufc-326",
  "event_name": "UFC 326: Holloway vs Oliveira 2",
  "date": "2026-03-08",
  "fighter_a": "Max Holloway",
  "fighter_a_id": 1234,
  "fighter_b": "Charles Oliveira",
  "fighter_b_id": 5678,
  "weight_class": "Lightweight",
  "winner": "Charles Oliveira",
  "winner_id": 5678,
  "method": "TKO",
  "round": 3,
  "time": "4:32",
  "stats": {
    "fighter_a": {
      "sig_strikes_landed": 89,
      "sig_strikes_attempted": 156,
      "takedowns_landed": 0,
      "takedowns_attempted": 2
    },
    "fighter_b": {
      "sig_strikes_landed": 112,
      "sig_strikes_attempted": 178,
      "takedowns_landed": 3,
      "takedowns_attempted": 5
    }
  }
}
```

---

## fighter-histories.json Schema

**Type:** Object with fighter_id as key

```json
{
  "1234": {
    "fighter_id": 1234,
    "name": "Max Holloway",
    "last_5_fights": [
      {
        "date": "2026-03-08",
        "opponent": "Charles Oliveira",
        "opponent_id": 5678,
        "result": "L",
        "method": "TKO",
        "round": 3,
        "event": "UFC 326"
      }
    ],
    "record_last_5": "3-2-0"
  }
}
```

---

## gaps/weight-class-history.json Schema

**Critical for predictions** — tracks fighter weight class movement

```json
{
  "1234": {
    "fighter_id": 1234,
    "name": "Max Holloway",
    "natural_weight_class": "Featherweight",
    "current_weight_class": "Lightweight",
    "history": [
      {"weight_class": "Featherweight", "from": "2012-01-01", "to": "2026-03-07"},
      {"weight_class": "Lightweight", "from": "2026-03-08", "to": null}
    ],
    "notes": "Moved up to Lightweight for UFC 326 rematch"
  }
}
```

---

## Import Workflow for Dev Team

### Option 1: Manual Import (Current)
1. Download JSON files from repo
2. Parse and insert into your database
3. Map fields to your schema

### Option 2: Automated Import (Recommended)
1. Set up webhook or polling to check repo for updates
2. Auto-pull new JSON when `last_updated` timestamp changes
3. Run import script to update database

### Option 3: API Wrapper (Future)
1. I build API layer on top of JSON
2. Your backend calls API endpoints
3. You cache/store as needed

---

## Update Frequency

| Data Type | Update Trigger | Typical Timing |
|-----------|---------------|----------------|
| Fight results | Post-event | Within 24 hours |
| Fighter stats | Monthly | Beginning of month |
| Upcoming events | When announced | Within 48 hours |
| Odds | Daily | Morning (AEDT) |

---

## Prediction Engine Integration

The `analysis_engine.py` includes logic for:
- Calculating matchup advantages
- Win probability scoring
- Finish method prediction
- Confidence rating

**To integrate:**
1. Port the calculation logic to your backend
2. Feed it fighter data from your database
3. Store predictions for tracking accuracy

---

## Questions?

Contact: Zac / David (AI operations)
