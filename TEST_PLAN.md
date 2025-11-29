# FFZ Testing Plan - Phases 1-4

## Test Objectives

Validate that all implemented features work correctly before proceeding to Phase 5 (Scheduling & Delivery).

---

## Test Environment

- **Local**: `http://127.0.0.1:8000`
- **Database**: Local PostgreSQL (`ffz_db`)
- **Required**: `OPENAI_API_KEY` in `.env`

---

## Test Suite

### 1. ✅ Database & Migrations

**Objective**: Verify database schema is correct

```bash
# Check current migration
python -m alembic current

# Verify all tables exist
python -c "
from app.models.db import engine
from sqlalchemy import inspect
import asyncio

async def check_tables():
    async with engine.connect() as conn:
        inspector = inspect(conn)
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        print('Tables:', tables)
        expected = ['users', 'subscriptions', 'matches', 'match_facts', 'reports', 'alembic_version']
        missing = [t for t in expected if t not in tables]
        if missing:
            print(f'❌ Missing tables: {missing}')
        else:
            print('✅ All tables present')

asyncio.run(check_tables())
"
```

**Expected**: All tables present, no missing migrations

---

### 2. ✅ Authentication & User Management

**Test 2.1: Registration**

```bash
# Register new user
curl -X POST http://127.0.0.1:8000/api/public/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ffz.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Expected**: 
- Status 200
- Returns user object with `id`, `email`
- User created in database
- Verification email sent (check logs)

**Test 2.2: Login**

```bash
# Login
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ffz.com",
    "password": "TestPass123!"
  }'
```

**Expected**:
- Status 200
- Returns `access_token`
- Save token for subsequent tests

**Test 2.3: Get Profile**

```bash
# Get profile (replace TOKEN)
curl http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected**:
- Status 200
- Returns user profile with subscriptions

---

### 3. ✅ Onboarding Flow

**Test 3.1: Complete Onboarding**

```bash
# Update profile (language, favorite team)
curl -X PUT http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "favorite_team": "Arsenal"
  }'
```

**Expected**: Status 200, profile updated

**Test 3.2: Add Subscriptions**

```bash
# Subscribe to Premier League
curl -X POST http://127.0.0.1:8000/api/user/subscriptions \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "league": "PL",
    "team": "Arsenal",
    "is_active": true
  }'
```

**Expected**: Status 200, subscription created

---

### 4. ✅ Data Pipeline - Scraping

**Test 4.1: Manual Scrape**

```bash
# Run scraper test
python test_scraper.py
```

**Expected**:
- Scrapes matches for PL
- Logs show HTTP requests to ESPN
- Matches inserted/updated in database

**Test 4.2: Verify Match Data**

```python
# Check matches in DB
python -c "
import asyncio
from app.models.db import AsyncSessionLocal
from app.models.match import Match
from sqlalchemy import select

async def check_matches():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Match).limit(10))
        matches = result.scalars().all()
        print(f'Found {len(matches)} matches')
        for m in matches[:3]:
            print(f'  {m.home_team} vs {m.away_team} ({m.date})')

asyncio.run(check_matches())
"
```

**Expected**: Matches exist in database

---

### 5. ✅ Report Generation

**Test 5.1: Generate Report (API)**

```bash
# Generate report
curl -X POST http://127.0.0.1:8000/api/reports/generate \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected**:
- Status 200 (if matches exist) OR
- Status 400 with error message (if no matches)

**Possible Issues**:
- "No active subscriptions" → Add subscription (Test 3.2)
- "No team specified" → Update profile with favorite_team (Test 3.1)
- No matches in DB → Run scraper (Test 4.1)

**Test 5.2: Get Latest Report**

```bash
# Get latest report
curl http://127.0.0.1:8000/api/reports/latest \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected**:
- Status 200
- Returns report with:
  - `headline`
  - `sections` array (4 sections)
  - `language` (en/fr/es)
  - `tone` (neutral/fan/analytic/bettor)

**Test 5.3: Verify Report Structure**

Check that report contains:
- ✅ "This Week for [Team]" section
- ✅ "What the Stats Say" section
- ✅ "Key Players & Moments" section
- ✅ "What's Next" section
- ✅ Content is in correct language
- ✅ Tone matches user preference

---

### 6. ✅ Multi-Language Testing

**Test 6.1: French Report**

```bash
# Update language to French
curl -X PUT http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"language": "fr"}'

# Generate French report
curl -X POST http://127.0.0.1:8000/api/reports/generate \
  -H "Authorization: Bearer <TOKEN>"

# Get report
curl http://127.0.0.1:8000/api/reports/latest \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected**: Report in French with section titles:
- "Cette semaine pour [équipe]"
- "Ce que les stats révèlent"
- etc.

**Test 6.2: Spanish Report**

```bash
# Update to Spanish
curl -X PUT http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"language": "es"}'

# Generate & retrieve
curl -X POST http://127.0.0.1:8000/api/reports/generate \
  -H "Authorization: Bearer <TOKEN>"
```

**Expected**: Report in Spanish

---

### 7. ✅ Frontend Testing

**Test 7.1: Landing Page**

1. Open `http://127.0.0.1:8000`
2. Verify:
   - ✅ Hero section loads
   - ✅ "Get Started" button works
   - ✅ Responsive on mobile

**Test 7.2: Registration Flow**

1. Click "Get Started"
2. Fill registration form
3. Submit
4. Verify redirect to onboarding

**Test 7.3: Onboarding**

1. Complete onboarding wizard:
   - Select language
   - Choose team & leagues
   - Pick tone
2. Verify redirect to dashboard

**Test 7.4: Dashboard**

1. Navigate to Dashboard
2. Verify:
   - ✅ Profile info displays
   - ✅ Subscriptions show
   - ✅ "Generate Report" button exists

---

## Test Results Template

```markdown
## Test Results - [Date]

### Database & Migrations
- [ ] All tables present
- [ ] Migrations up to date

### Authentication
- [ ] Registration works
- [ ] Login works
- [ ] Profile retrieval works

### Onboarding
- [ ] Profile update works
- [ ] Subscription creation works

### Data Pipeline
- [ ] Scraper runs successfully
- [ ] Matches stored in DB

### Report Generation
- [ ] Report generation works
- [ ] Latest report retrieval works
- [ ] Report structure correct

### Multi-Language
- [ ] English reports work
- [ ] French reports work
- [ ] Spanish reports work

### Frontend
- [ ] Landing page loads
- [ ] Registration flow works
- [ ] Onboarding flow works
- [ ] Dashboard displays

### Issues Found
[List any issues]

### Notes
[Any observations]
```

---

## Known Limitations (MVP)

1. **No real match data**: Scraper may return 0 matches if ESPN has no recent data
2. **Vision not tested**: Playwright Vision requires real Flashscore pages
3. **Email delivery**: Verification emails sent but not tested end-to-end
4. **Caching**: Not implemented (deferred to post-MVP)

---

## Next Steps After Testing

1. Fix any critical bugs found
2. Proceed to Phase 5 (Scheduling & Email Delivery)
3. Implement weekly report automation
