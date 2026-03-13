# UFC Data Update Workflow

**Purpose:** Automated process for keeping UFC data current

---

## Post-Event Update Process

### Step 1: Event Detection (Automated)
- Monitor UFC schedule for completed events
- Check UFC.com, ESPN, Tapology for results
- Trigger: Event date + 6 hours (allow time for official results)

### Step 2: Data Collection (Automated)
- Scrape fight results from UFC Stats
- Collect detailed stats (SLpM, accuracy, takedowns, etc.)
- Update fighter records (wins/losses)
- Update `fight-history.json`

### Step 3: Fighter Stats Update (Automated)
- Recalculate fighter metrics based on new fight
- Update `fighters.json` with new stats
- Update `fighter-histories.json` (last 5 fights)
- Update `gaps/weight-class-history.json` if weight change

### Step 4: Validation (Automated)
- Check data integrity
- Verify all fights have results
- Cross-reference with official UFC stats

### Step 5: Commit & Push (Automated)
- Commit to `aibet-ufc-data` repo
- Tag with event name and date
- Push to GitHub

### Step 6: Notify (Automated)
- Ping dev team webhook (optional)
- Update timestamp in repo
- Log update in `UPDATES.md`

---

## Daily Update Process

### Morning Check (9 AM AEDT)
- Check for new fight announcements
- Update `upcoming-events.json`
- Refresh betting odds if available
- Check for fighter news (injuries, withdrawals)

### Weekly Check (Mondays)
- Full data validation
- Update fighter rankings
- Review and fill data gaps
- Update `gaps/data-completeness-tracker.json`

---

## Manual Override

If automated process fails:

1. **Manual data entry** via spreadsheet → JSON conversion
2. **Emergency update** — direct commit to repo
3. **Rollback** — revert to previous commit if error

---

## Data Sources Priority

| Priority | Source | Data Type |
|----------|--------|-----------|
| 1 | UFC Stats | Official stats, results |
| 2 | UFC.com | Rankings, announcements |
| 3 | ESPN MMA | News, odds |
| 4 | Tapology | Fighter history, regional records |
| 5 | Sherdog | Backup for fighter records |

---

## Dev Team Integration

### Webhook (Optional)
```
POST https://your-api.com/webhook/ufc-update
{
  "event": "data-updated",
  "files_changed": ["fighters.json", "fight-history.json"],
  "timestamp": "2026-03-14T09:00:00Z",
  "commit_hash": "abc123"
}
```

### Polling (Alternative)
Dev team polls `https://api.github.com/repos/davidtheaibet/aibet-ufc-data/commits` every 6 hours

### Timestamp File
Check `last-updated.txt` in repo root for latest update time

---

## Update Log Format (UPDATES.md)

```markdown
## 2026-03-14 - UFC 326 Results Added
- Fights added: 6
- Fighter stats updated: 12
- New fighters added: 2 (Xiao Long, regional records)
- Weight class changes: 1 (Holloway → Lightweight)
- Data completeness: 82%

## 2026-03-13 - Daily Update
- Upcoming events refreshed
- Odds updated for Vegas 114
- No significant changes
```

---

## Automation Status

| Task | Status | Notes |
|------|--------|-------|
| Event detection | 🟡 Manual | Needs scraper build |
| Results collection | 🟡 Manual | Needs UFC Stats scraper |
| Stats calculation | 🟡 Manual | Needs automation |
| Commit & push | 🟢 Automated | Git workflow ready |
| Dev notification | 🔴 Not started | Needs webhook setup |

---

## Next Steps

1. Build UFC Stats scraper for automated results
2. Set up scheduled runner (cron/GitHub Actions)
3. Create webhook endpoint for dev team
4. Build validation checks
5. Document API for dev team consumption

---

Last updated: March 13, 2026
