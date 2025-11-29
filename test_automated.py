"""
Automated test script for FFZ database verification
"""
import asyncio
import sys
from sqlalchemy import inspect, text
from app.models.db import engine, AsyncSessionLocal
from app.models.match import Match
from app.models.user import User, Subscription
from app.models.report import Report

async def test_database_schema():
    """Test that all required tables exist"""
    print("=" * 60)
    print("TEST 1: Database Schema Verification")
    print("=" * 60)
    
    expected_tables = [
        'users',
        'subscriptions', 
        'matches',
        'match_facts',
        'reports',
        'alembic_version'
    ]
    
    try:
        async with engine.connect() as conn:
            # Get table names
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ))
            tables = [row[0] for row in result]
            
            print(f"\n✓ Connected to database")
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
            
            # Check for missing tables
            missing = [t for t in expected_tables if t not in tables]
            
            if missing:
                print(f"\n❌ FAIL: Missing tables: {', '.join(missing)}")
                return False
            else:
                print(f"\n✅ PASS: All required tables present")
                return True
                
    except Exception as e:
        print(f"\n❌ FAIL: Database connection error: {e}")
        return False


async def test_models():
    """Test that models can be queried"""
    print("\n" + "=" * 60)
    print("TEST 2: Model Query Verification")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as db:
            # Test User model
            from sqlalchemy import select
            result = await db.execute(select(User).limit(1))
            user_count = len(result.scalars().all())
            print(f"\n✓ User model: {user_count} users in DB")
            
            # Test Match model
            result = await db.execute(select(Match).limit(1))
            match_count = len(result.scalars().all())
            print(f"✓ Match model: {match_count} matches in DB")
            
            # Test Report model
            result = await db.execute(select(Report).limit(1))
            report_count = len(result.scalars().all())
            print(f"✓ Report model: {report_count} reports in DB")
            
            print(f"\n✅ PASS: All models queryable")
            return True
            
    except Exception as e:
        print(f"\n❌ FAIL: Model query error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scraper_data():
    """Check if we have match data"""
    print("\n" + "=" * 60)
    print("TEST 3: Scraper Data Verification")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func
            
            # Count matches per league
            result = await db.execute(
                select(Match.league_code, func.count(Match.id))
                .group_by(Match.league_code)
            )
            league_counts = result.all()
            
            if league_counts:
                print("\n✓ Match data by league:")
                for league, count in league_counts:
                    print(f"  - {league}: {count} matches")
                print(f"\n✅ PASS: Match data exists")
                return True
            else:
                print("\n⚠️  WARNING: No match data in database")
                print("   Run: python test_scraper.py")
                return False
                
    except Exception as e:
        print(f"\n❌ FAIL: Scraper data check error: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FFZ AUTOMATED TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(await test_database_schema())
    results.append(await test_models())
    results.append(await test_scraper_data())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
