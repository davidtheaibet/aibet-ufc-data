# UFC Data Knowledge Base v2.0

Comprehensive UFC fighter database and analysis engine for AIbet.

**Version**: 2.0  
**Last Updated**: March 12, 2026  
**Source**: ufcstats.com, ufc.com

---

## 🎯 What's New in v2.0

### UFC 326 Lessons Applied

This update addresses the analysis failures from **Holloway vs Oliveira** at UFC 326:

1. **✅ Weight Class Accuracy**
   - Added fighter's natural/primary weight class
   - Track weight class history (all divisions fought at)
   - Identify when fighters are competing outside their natural weight

2. **✅ Power Differential Analysis**
   - KO power scoring based on KO rate and volume
   - Takedown power indicators
   - Physical presence scoring (height/reach for weight class)
   - Overall power rating (0-100)

3. **✅ Physical Transformation Impact**
   - Weight cut risk assessment (Low/Medium/High)
   - Weight trend analysis (moving up/down/stable)
   - Performance penalties for extreme weight cuts
   - Power translation assessment when moving weight classes

---

## 📁 File Structure

```
ufc-data/
├── fighters.json          # Master fighter database (4,346 fighters)
├── events.json            # Historical events (24 events)
├── fight-history.json     # Historical fight results (296 fights)
├── upcoming-events.json   # Upcoming UFC events (8 events)
├── analysis-engine.py     # Enhanced fight prediction engine v2.0
├── export_enhanced.py     # Data export utility with enhancements
└── README.md              # This file
```

---

## 📊 Data Statistics

- **Fighters**: 4,346 with comprehensive stats
- **Weight Classes**: All UFC divisions (Flyweight to Heavyweight, Men's and Women's)
- **Historical Events**: 24 events with full fight cards
- **Fight Records**: 296 historical fights with detailed stats
- **Upcoming Events**: 8 scheduled events through May 2026

---

## 🎯 Fighter Data Fields

### Basic Info
- `name` - Full name
- `nickname` - Fighter nickname
- `weight_class` - Weight division
- `height` - Height (e.g., "6' 0\"")
- `reach` - Reach (e.g., "74\"")
- `stance` - Fighting stance (Orthodox/Southpaw)
- `date_of_birth` - Date of birth

### Fight Record
- `record_wins` - Total wins
- `record_losses` - Total losses
- `record_draws` - Total draws
- `win_rate` - Calculated win percentage
- `finish_rate` - Percentage of wins by finish

### Fight Metrics (UFC Stats)
- `slpm` - Significant strikes landed per minute
- `sig_strike_acc` - Significant striking accuracy (0-1)
- `sapm` - Significant strikes absorbed per minute
- `sig_strike_def` - Significant strike defense (0-1)
- `td_avg` - Average takedowns per fight
- `td_acc` - Takedown accuracy (0-1)
- `td_def` - Takedown defense (0-1)
- `sub_avg` - Average submissions attempted per fight

### Win Methods
- `win_methods.ko_tko` - KO/TKO wins
- `win_methods.submissions` - Submission wins
- `win_methods.decisions` - Decision wins

### 🆕 Weight Class Analysis (v2.0)
```json
"weight_class_analysis": {
  "natural_weight_class": "Featherweight",
  "current_weight_class": "Lightweight",
  "weight_class_history": ["Featherweight", "Lightweight"],
  "has_moved_weight": true,
  "weight_trend": "Moving Up",
  "weight_cut_risk": "Low",
  "is_at_natural_weight": false
}
```

### 🆕 Power Indicators (v2.0)
```json
"power_indicators": {
  "ko_power_score": 75.5,
  "ko_rate": 45.2,
  "takedown_power_score": 62.0,
  "physical_presence_score": 68.5,
  "overall_power_rating": 71.2,
  "finish_rate": 65.0
}
```

### Recent Form
- `recent_fights` - Last 5 fights with results and stats

---

## 🔮 Analysis Engine v2.0

**File**: `analysis-engine.py`

### Features
- **Striking Analysis**: Volume, accuracy, defense scoring
- **Grappling Analysis**: Takedown offense/defense, submission threat
- **Experience Scoring**: Fight record depth and quality
- **Form Analysis**: Recent performance trends
- **🆕 Power Indicators**: KO rate, takedown power, physical presence
- **🆕 Weight Class Analysis**: Natural vs current weight, cut risk, transformation impact
- **Win Probability**: With confidence scoring
- **Likely Finish Method**: KO/Submission/Decision prediction

### Scoring Algorithm
```
Overall Score = 
  (Striking × 0.22) +
  (Grappling × 0.22) +
  (Experience × 0.18) +
  (Form × 0.18) +
  (Power × 0.10) +
  (Weight Class × 0.10) +
  Transformation Impact
```

### Weight Class Penalties
- **Moving Down (High Risk)**: -15 points
- **Moving Down (Medium Risk)**: -8 points
- **Moving Up**: -5 points (power may not translate)
- **At Natural Weight**: No penalty

### Usage

```python
from analysis-engine import UFCAnalysisEngine

# Initialize engine
engine = UFCAnalysisEngine()

# Analyze a matchup
result = engine.analyze_matchup("Max Holloway", "Charles Oliveira")

# Output includes:
# - Weight class analysis for both fighters
# - Power differential assessment
# - Transformation impact evaluation
# - Weight cut risk warnings

# Get fighter profile with weight class history
profile = engine.get_fighter_profile("Max Holloway")
```

### Prediction Output

```json
{
  "fighter_a": {
    "name": "Max Holloway",
    "weight_class": "Lightweight",
    "natural_weight_class": "Featherweight",
    "weight_penalty": -5,
    "power_indicators": {
      "overall_power_rating": 65.5,
      "ko_power_score": 70.2
    },
    "transformation_impact": {
      "impact_score": -10,
      "concerns": ["Power may not translate to higher weight"],
      "assessment": "Negative"
    }
  },
  "power_differential": {
    "power_differential": -8.5,
    "advantage": "Charles Oliveira",
    "advantage_margin": 8.5
  },
  "prediction": {
    "winner": "Charles Oliveira",
    "confidence": "Medium",
    "probability_a": 42.0,
    "probability_b": 58.0,
    "likely_method": "Submission"
  },
  "key_factors": [
    {
      "factor": "weight_class",
      "description": "Max Holloway not at natural weight class",
      "impact": "negative"
    },
    {
      "factor": "power",
      "description": "Significant power advantage to Charles Oliveira",
      "impact": "positive"
    }
  ]
}
```

---

## 📅 Upcoming Events

| Date | Event | Location |
|------|-------|----------|
| Mar 15, 2026 | UFC Fight Night: Emmett vs Vallejos | Las Vegas, NV |
| Mar 22, 2026 | UFC Fight Night: Evloev vs Murphy | London, UK |
| Mar 29, 2026 | UFC Fight Night: Adesanya vs Pyfer | Seattle, WA |
| Apr 5, 2026 | UFC Fight Night: Moicano vs Duncan | Las Vegas, NV |
| Apr 12, 2026 | UFC 327: Prochazka vs Ulberg | Miami, FL |
| Apr 19, 2026 | UFC Fight Night: Burns vs Malott | Winnipeg, Canada |
| Apr 26, 2026 | UFC Fight Night: Brady vs Buckley | Las Vegas, NV |
| May 2, 2026 | UFC Fight Night: Della Maddalena vs Prates | Perth, Australia |

---

## 🔄 Data Updates

To refresh the data from the source database:

```bash
cd ufc-data
python3 export_enhanced.py
```

---

## 📈 Data Sources

- **Primary**: ufcstats.com (official UFC statistics)
- **Secondary**: ufc.com (rankings and upcoming events)
- **Last Updated**: March 12, 2026

---

## ⚠️ Known Limitations

1. **Win Method Breakdown**: Some historical fights lack detailed finish method data
2. **Recent Form**: Limited to fights recorded in the database
3. **Odds**: Not currently included (placeholder values in upcoming events)
4. **Weight Class History**: Limited by available fight records; may not capture early career weight classes
5. **Physical Transformation**: No visual/image analysis; based on stats only
6. **Weight Cut Data**: No direct access to weight cut process; inferred from weight class changes

---

## 🔧 Future Enhancements

- [ ] Integration with live odds APIs
- [ ] Fighter injury/withdrawal tracking
- [ ] More detailed fight statistics (round-by-round)
- [ ] Head-to-head matchup history
- [ ] Training camp and corner information
- [ ] Video analysis integration for form assessment
- [ ] Social media sentiment analysis

---

## 📝 UFC 326 Post-Mortem

**Fight**: Max Holloway vs Charles Oliveira  
**Issue**: Analysis failed to account for weight class dynamics

**Root Causes**:
1. Holloway was fighting at Lightweight (155 lbs), not his natural Featherweight (145 lbs)
2. Power differential favored Oliveira who was naturally bigger
3. Holloway's striking volume advantage was negated by the weight difference

**Solutions Implemented**:
- ✅ Track natural vs current weight class
- ✅ Calculate power ratings for weight class
- ✅ Assess weight cut risk and transformation impact
- ✅ Apply performance penalties for weight class changes

---

**For questions or issues, contact the AIbet development team.**
