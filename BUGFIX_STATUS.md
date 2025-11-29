# Bugs Fixed - Status Update

## ✅ Bug 1: Import Error (FIXED)
**File**: `app/api/public.py`
**Change**: `decode_jwt_token` → `decode_jwt`
**Status**: Email verification now works

## 🔧 Bug 2-6: Require System Refactor

The remaining bugs all stem from the same root cause: **The dashboard uses the OLD generation system** (`/news/generate` → `report_builder.py`) instead of the NEW system I just built (`/api/reports/generate` → `report_generator.py`).

### Current State:
- Dashboard calls `/news/generate` (old system)
- Old system uses `llm_generator.py` with fallback logic
- Old system doesn't respect language/tone properly
- Old system doesn't send emails
- Old system has wrong report structure

### Solution:
Need to migrate dashboard to use new `/api/reports/generate` endpoint and deprecate old system.

This requires:
1. Update Dashboard.js to call `/api/reports/generate`
2. Add email sending to manual generation
3. Fix language/tone in new report_generator
4. Update prompts to match product vision
5. Add frequency preference to user model
6. Remove old generation system

**Estimated time**: 30-45 minutes for complete fix

**Alternative**: Quick patch old system, but this creates technical debt
