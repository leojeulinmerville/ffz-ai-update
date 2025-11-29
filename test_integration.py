"""
Integration test for report generation with mock data
"""
import asyncio
from datetime import datetime, timezone, timedelta
from app.models.db import AsyncSessionLocal
from app.models.user import User, Subscription
from app.models.match import Match, MatchStatus
from app.services.report_generator import generate_weekly_report

async def setup_test_data():
    """Create test user, subscription, and matches"""
    print("Setting up test data...")
    
    async with AsyncSessionLocal() as db:
        # Check if test user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "test@ffz.com"))
        user = result.scalars().first()
        
        if not user:
            print("❌ No test user found. Please register via API first:")
            print('   curl -X POST http://127.0.0.1:8000/api/public/register \\')
            print('     -H "Content-Type: application/json" \\')
            print('     -d \'{"email":"test@ffz.com","password":"Test123!","first_name":"Test","last_name":"User"}\'')
            return None
        
        print(f"✓ Found user: {user.email}")
        
        # Update user preferences
        user.language = "en"
        user.favorite_team = "Arsenal"
        await db.commit()
        print(f"✓ Updated user language: {user.language}, favorite_team: {user.favorite_team}")
        
        # Check/create subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.league == "PL"
            )
        )
        sub = result.scalars().first()
        
        if not sub:
            sub = Subscription(
                user_id=user.id,
                league="PL",
                team="Arsenal",
                is_active=True
            )
            db.add(sub)
            await db.commit()
            print(f"✓ Created subscription: PL - Arsenal")
        else:
            print(f"✓ Found subscription: {sub.league} - {sub.team}")
        
        # Create mock matches
        now = datetime.now(timezone.utc)
        
        # Recent matches
        matches_data = [
            {
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "score_home": 2,
                "score_away": 1,
                "date": now - timedelta(days=7),
                "status": MatchStatus.FINISHED.value
            },
            {
                "home_team": "Manchester United",
                "away_team": "Arsenal",
                "score_home": 1,
                "score_away": 3,
                "date": now - timedelta(days=14),
                "status": MatchStatus.FINISHED.value
            },
            {
                "home_team": "Arsenal",
                "away_team": "Liverpool",
                "score_home": 2,
                "score_away": 2,
                "date": now - timedelta(days=21),
                "status": MatchStatus.FINISHED.value
            },
            # Upcoming match
            {
                "home_team": "Arsenal",
                "away_team": "Tottenham",
                "score_home": None,
                "score_away": None,
                "date": now + timedelta(days=3),
                "status": MatchStatus.SCHEDULED.value
            }
        ]
        
        # Delete existing test matches
        from sqlalchemy import delete
        await db.execute(delete(Match).where(Match.league_code == "PL"))
        await db.commit()
        
        # Insert mock matches
        for match_data in matches_data:
            match = Match(
                source_id=f"test_{match_data['home_team']}_{match_data['away_team']}",
                league_code="PL",
                **match_data
            )
            db.add(match)
        
        await db.commit()
        print(f"✓ Created {len(matches_data)} mock matches")
        
        return str(user.id)


async def test_report_generation():
    """Test report generation with mock data"""
    print("\n" + "=" * 60)
    print("INTEGRATION TEST: Report Generation")
    print("=" * 60)
    
    # Setup test data
    user_id = await setup_test_data()
    
    if not user_id:
        print("\n❌ TEST FAILED: Could not setup test data")
        return False
    
    # Generate report
    print("\nGenerating report...")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await generate_weekly_report(user_id, db)
        
        print(f"\n✅ Report generated successfully!")
        print(f"   Report ID: {result['id']}")
        
        report = result['report']
        print(f"\n📊 Report Details:")
        print(f"   Headline: {report['headline']}")
        print(f"   Language: {report['language']}")
        print(f"   Tone: {report['tone']}")
        print(f"   Team: {report['team_name']}")
        print(f"   Sections: {len(report['sections'])}")
        
        print(f"\n📝 Report Sections:")
        for i, section in enumerate(report['sections'], 1):
            print(f"\n   {i}. {section['title']}")
            content_preview = section['content'][:150] + "..." if len(section['content']) > 150 else section['content']
            print(f"      {content_preview}")
        
        # Verify structure
        expected_sections = 4
        if len(report['sections']) != expected_sections:
            print(f"\n⚠️  WARNING: Expected {expected_sections} sections, got {len(report['sections'])}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run integration test"""
    success = await test_report_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ INTEGRATION TEST PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ INTEGRATION TEST FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
