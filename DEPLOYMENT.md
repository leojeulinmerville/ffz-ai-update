# Phase 5 Deployment Guide

## Prerequisites

- Docker Desktop running
- `.env` file configured with:
  - `OPENAI_API_KEY`
  - `MAILEROO_API_KEY`
  - `MAILEROO_DEFAULT_FROM`
  - `PUBLIC_URL`

---

## Deployment Steps

### 1. Stop Current Services

```bash
# Stop local uvicorn if running
# Ctrl+C in terminal

# Or stop Docker if running
docker-compose -f docker/docker-compose.yml down
```

### 2. Apply Database Migrations

```bash
# Start database only
docker-compose -f docker/docker-compose.yml up -d postgres

# Wait for postgres to be ready (check health)
docker-compose -f docker/docker-compose.yml ps

# Apply migrations
docker-compose -f docker/docker-compose.yml run --rm api alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Running upgrade ... -> 5edfc5d355d3, Add delivery tracking fields
```

### 3. Start All Services

```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

### 4. Verify Deployment

**Check Health**:
```bash
curl http://localhost:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "scheduler_running": true,
  "database_ready": true
}
```

**Check Logs**:
```bash
docker-compose -f docker/docker-compose.yml logs -f api
```

**Look for**:
```
INFO: Application startup complete.
INFO: Registered weekly report job: day=0, hour=9:00 Europe/Paris
```

---

## Testing

### Test 1: Manual Report Generation

```bash
# Register a test user (if not already done)
curl -X POST http://localhost:8000/api/public/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@ffz.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@ffz.com","password":"Test123!"}'

# Save the token from response
export TOKEN="<your-token>"

# Add subscription
curl -X POST http://localhost:8000/api/user/subscriptions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"league":"PL","team":"Arsenal","is_active":true}'

# Generate report
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Authorization: Bearer $TOKEN"
```

### Test 2: Manual Weekly Job Trigger

```bash
docker-compose -f docker/docker-compose.yml exec api python -c "
import asyncio
from app.scheduler.report_jobs import job_generate_weekly_reports
asyncio.run(job_generate_weekly_reports())
"
```

**Expected output**:
```
INFO: Starting weekly report generation job
INFO: Found X eligible users for reports
INFO: Processing batch 1 (X users)
INFO: Generating report for test@ffz.com
INFO: Sending report email to test@ffz.com
INFO: Report <id> sent successfully to test@ffz.com
INFO: Weekly report job completed: 1 sent, 0 failed
```

### Test 3: Verify Email Delivery

1. **Check Maileroo Dashboard**: Look for sent email
2. **Check Database**:
   ```bash
   docker-compose -f docker/docker-compose.yml exec postgres psql -U ffz_user -d ffz_db -c "
   SELECT id, user_id, sent_at, delivery_status 
   FROM reports 
   ORDER BY created_at DESC 
   LIMIT 5;
   "
   ```

---

## Configuration

### Change Schedule

Edit `.env`:
```ini
# Run on Fridays at 18:00
REPORT_SCHEDULE_DAY=4      # 0=Mon, 4=Fri
REPORT_SCHEDULE_HOUR=18
REPORT_SCHEDULE_MINUTE=0
```

Restart:
```bash
docker-compose -f docker/docker-compose.yml restart api
```

### Batch Size

For large user bases:
```ini
REPORT_BATCH_SIZE=100  # Process 100 users at a time
```

---

## Troubleshooting

### Issue: Scheduler Not Running

**Check**:
```bash
curl http://localhost:8000/health
```

If `scheduler_running: false`:
```bash
docker-compose -f docker/docker-compose.yml logs api | grep -i scheduler
```

**Fix**: Restart services

### Issue: No Emails Sent

**Check Maileroo Config**:
```bash
docker-compose -f docker/docker-compose.yml exec api python -c "
import os
print('MAILEROO_API_KEY:', 'SET' if os.getenv('MAILEROO_API_KEY') else 'NOT SET')
print('MAILEROO_DEFAULT_FROM:', os.getenv('MAILEROO_DEFAULT_FROM'))
"
```

**Check Logs**:
```bash
docker-compose -f docker/docker-compose.yml logs api | grep -i maileroo
```

### Issue: Migration Fails

**Error**: `Target database is not up to date`

**Fix**:
```bash
# Check current revision
docker-compose -f docker/docker-compose.yml exec api alembic current

# Upgrade
docker-compose -f docker/docker-compose.yml exec api alembic upgrade head
```

### Issue: No Eligible Users

**Check**:
```bash
docker-compose -f docker/docker-compose.yml exec postgres psql -U ffz_user -d ffz_db -c "
SELECT 
  COUNT(*) as total_users,
  SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active,
  SUM(CASE WHEN is_verified THEN 1 ELSE 0 END) as verified,
  SUM(CASE WHEN trial_ends_at > NOW() OR subscription_status = 'active' THEN 1 ELSE 0 END) as has_access
FROM users;
"
```

**Fix**: Ensure users have:
- `is_active = true`
- `is_verified = true`
- `trial_ends_at > now()` OR `subscription_status = 'active'`
- At least one active subscription

---

## Production Checklist

- [ ] `.env` has production values
- [ ] `PUBLIC_URL` set to production domain
- [ ] Maileroo sender email verified
- [ ] Database migrations applied
- [ ] Services started and healthy
- [ ] Scheduler registered (check logs)
- [ ] Manual test successful
- [ ] Email delivery confirmed
- [ ] Monitoring setup (logs, Maileroo dashboard)

---

## Rollback

If issues occur:

```bash
# Stop services
docker-compose -f docker/docker-compose.yml down

# Rollback migration
docker-compose -f docker/docker-compose.yml run --rm api alembic downgrade -1

# Restart
docker-compose -f docker/docker-compose.yml up -d
```

---

## Next Steps

Once deployed and tested:
1. Monitor first automated run (next Monday 09:00)
2. Check delivery rates in Maileroo
3. Gather user feedback
4. Proceed to Phase 6 (Billing & Trial)
