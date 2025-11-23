import asyncio
import base64
import logging
import os
from typing import Any, Dict, Optional

from playwright.async_api import async_playwright, Page
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_openai = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

async def fetch_latest_match_stats(team_name: str) -> Optional[Dict[str, Any]]:
    """
    Uses Playwright to find the latest match report on Flashscore,
    takes a screenshot, and uses GPT-4o to extract stats.
    """
    if not _openai:
        logger.warning("OpenAI not configured, skipping vision extraction")
        return None

    async with async_playwright() as p:
        # Launch browser (headless=True usually, but maybe False for debugging if needed)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # 1. Search for team results on Flashscore via DuckDuckGo (simpler HTML than Google)
            # or just Google. Let's try Google but handle consent forms if any.
            # Actually, Flashscore has a predictable search API? No.
            # Let's try navigating directly if we had IDs.
            # Fallback: Search on DuckDuckGo
            query = f"site:flashscore.com {team_name} team results"
            await page.goto(f"https://duckduckgo.com/?q={query}")
            
            # Click first result
            # Selectors might change, but usually the first organic result
            await page.wait_for_selector('.react-results--main a', timeout=5000)
            results = await page.query_selector_all('.react-results--main a')
            
            target_url = None
            for res in results:
                href = await res.get_attribute('href')
                if href and "flashscore.com/team/" in href:
                    target_url = href
                    break
            
            if not target_url:
                logger.warning("Could not find Flashscore team page for %s", team_name)
                return None

            logger.info("Found team page: %s", target_url)
            await page.goto(target_url)
            
            # 2. Click the first match in "Results"
            # Flashscore structure: .sportName.soccer -> .event__match
            # Wait for results to load
            await page.wait_for_selector('.event__match', timeout=10000)
            
            # The first match in the list is usually the latest result (top of the list)
            # But sometimes it shows "Scheduled" matches if we are on "Fixtures".
            # We need to make sure we are on "Results" tab.
            # URL usually ends in /results/ if we clicked the right link.
            # If not, click "Results" tab.
            
            # Check if we are on results
            if "/results" not in page.url:
                # Try to find "Results" tab
                # This is tricky as selectors are dynamic.
                # Let's assume the search result sent us to the main page or results page.
                pass

            # Click the first match
            # Note: Flashscore opens matches in a popup or new page depending on width.
            # On desktop, it might be a new page or modal.
            # Let's try to get the ID of the first match and construct the URL.
            match_elements = await page.query_selector_all('.event__match')
            if not match_elements:
                logger.warning("No matches found on team page")
                return None
                
            latest_match = match_elements[0]
            match_id = await latest_match.get_attribute('id')
            # ID format: g_1_NxMk... -> remove g_1_
            if match_id and match_id.startswith('g_1_'):
                clean_id = match_id[4:]
                match_url = f"https://www.flashscore.com/match/{clean_id}/#/match-summary/match-statistics/0"
                logger.info("Navigating to match stats: %s", match_url)
                await page.goto(match_url)
                
                # 3. Take Screenshot
                # Wait for stats to load
                try:
                    await page.wait_for_selector('.stat__categoryName', timeout=10000)
                except:
                    logger.warning("Stats tab not found or empty")
                    # Try summary tab if stats fail
                    pass
                
                # Accept cookies if banner exists (Flashscore often has one)
                # await page.click('#onetrust-accept-btn-handler') # Example
                
                screenshot_bytes = await page.screenshot(full_page=False)
                
                # 4. Send to Vision
                return await _analyze_screenshot(screenshot_bytes, team_name)

        except Exception as exc:
            logger.exception("Vision extraction failed: %s", exc)
            return None
        finally:
            await browser.close()

async def _analyze_screenshot(image_bytes: bytes, team_name: str) -> Dict[str, Any]:
    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = f"""
    Analyze this football match statistics screenshot.
    Focus on the performance of "{team_name}".
    
    Extract the following in JSON format:
    {{
        "home_team": "string",
        "away_team": "string",
        "score_home": int,
        "score_away": int,
        "date": "string (YYYY-MM-DD)",
        "stats": {{
            "possession_home": "string",
            "xg_home": "string (if available)",
            "xg_away": "string (if available)",
            "shots_home": int,
            "shots_away": int
        }},
        "key_performers": ["string (player names mentioned or high ratings)"],
        "summary": "string (2-3 sentences describing how {team_name} played based on these stats)"
    }}
    
    If specific stats like xG are missing, use null.
    """

    try:
        response = await _openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        import json
        return json.loads(content)
    except Exception as exc:
        logger.error("OpenAI Vision API error: %s", exc)
        return None
