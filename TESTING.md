# FFZ Quick Test Guide

## Automated Tests

### 1. Database & Models Test
```bash
python test_automated.py
```

**Expected**: 2/3 tests pass (scraper data warning is OK)

---

### 2. Integration Test (Report Generation)

**Prerequisites**: 
- `OPENAI_API_KEY` must be set in `.env`
- User must be registered first

**Step 1: Register Test User**
```bash
curl -X POST http://127.0.0.1:8000/api/public/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ffz.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Step 2: Run Integration Test**
```bash
python test_integration.py
```

**Expected**:
- ✅ Sets up test user with Arsenal subscription
- ✅ Creates 4 mock matches (3 finished, 1 upcoming)
- ✅ Generates report with GPT-4o
- ✅ Report has 4 sections in English
- ✅ Report stored in database

---

## Manual API Tests

### Get Auth Token
```bash
# Login
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@ffz.com","password":"Test123!"}'

# Save the access_token from response
export TOKEN="<your-token-here>"
```

### Test Endpoints

**1. Get Profile**
```bash
curl http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer $TOKEN"
```

**2. Update Language**
```bash
# French
curl -X PUT http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language":"fr"}'

# Spanish
curl -X PUT http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language":"es"}'

# English
curl -X PUT http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language":"en"}'
```

**3. Generate Report**
```bash
curl -X POST http://127.0.0.1:8000/api/reports/generate \
  -H "Authorization: Bearer $TOKEN"
```

**4. Get Latest Report**
```bash
curl http://127.0.0.1:8000/api/reports/latest \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Frontend Tests

### 1. Landing Page
- Open: `http://127.0.0.1:8000`
- Check: Hero, features, pricing sections load

### 2. Registration
- Click "Get Started"
- Fill form and submit
- Check: Redirect to onboarding

### 3. Onboarding
- Complete wizard (language, team, tone)
- Check: Redirect to dashboard

### 4. Dashboard
- Navigate to dashboard
- Check: Profile displays, subscriptions show

---

## Test Multi-Language Reports

```bash
# French Report
curl -X PUT http://127.0.0.1:8000/api/user/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language":"fr"}'

curl -X POST http://127.0.0.1:8000/api/reports/generate \
  -H "Authorization: Bearer $TOKEN"

curl http://127.0.0.1:8000/api/reports/latest \
  -H "Authorization: Bearer $TOKEN" | jq '.data.report.sections[0]'

# Should show: "Cette semaine pour Arsenal"
```

---

## Expected Results

### ✅ Working
- Database schema
- User registration & login
- Profile management
- Subscription management
- Report generation (with mock data)
- Multi-language support (FR/EN/ES)
- Multi-tone support (fan/neutral/analytic/bettor)

### ⚠️ Known Issues
- ESPN scraper returns 0 matches (missing event IDs)
- Vision extractor not tested (needs real Flashscore pages)
- Email verification links show localhost (need PUBLIC_URL in .env)

### 🚧 Not Yet Implemented
- Weekly scheduling (Phase 5)
- Email delivery automation (Phase 5)
- Report archives (Phase 5)
- Billing & trials (Phase 6)

---

## Quick Checklist

- [ ] `python test_automated.py` passes
- [ ] `python test_integration.py` passes
- [ ] Can register user via API
- [ ] Can login and get token
- [ ] Can generate report
- [ ] Report has 4 sections
- [ ] French reports work
- [ ] Spanish reports work
- [ ] Landing page loads
- [ ] Dashboard displays

---

## Next Steps

Once all tests pass:
1. Fix any critical bugs
2. Proceed to Phase 5 (Scheduling & Email Delivery)
