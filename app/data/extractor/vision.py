import asyncio
import base64
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from playwright.async_api import async_playwright
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_openai = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

async def extract_match_stats(home_team: str, away_team: str, date_obj: datetime) -> Optional[Dict[str, Any]]:
    """
    Extracts deep match stats using Playwright and OpenAI Vision.
    Target: Flashscore (or similar).
    """
    if not _openai:
        logger.warning("OpenAI not configured, skipping vision extraction")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        )
        page = await context.new_page()
        
        try:
            # 1. Search for the match specifically
            # Format: "Flashscore {home} vs {away} {date}"
            date_str = date_obj.strftime("%Y-%m-%d")
            query = f"site:flashscore.com {home_team} vs {away_team} {date_str} match summary"
            
            logger.info(f"Searching for match: {query}")
            await page.goto(f"https://duckduckgo.com/?q={query}")
            
            try:
                await page.wait_for_selector('.result__a', timeout=10000)
                results = await page.query_selector_all('.result__a')
            except Exception:
                logger.warning("DuckDuckGo results not found, falling back to Google")
                await page.goto(f"https://www.google.com/search?q={query}")
                await page.wait_for_selector('a h3', timeout=10000)
                results = await page.query_selector_all('a h3')

            target_url = None
            for res in results:
                href = await res.get_attribute('href')
                # Flashscore match URLs usually look like /match/{id}/#/match-summary
                if href and "/match/" in href and "flashscore" in href:
                    target_url = href
                    break
            
            if not target_url:
                logger.warning(f"Could not find Flashscore match page for {home_team} vs {away_team}")
                return None

            # Ensure we go to the stats tab
            # URL format: .../match/{id}/#/match-summary/match-statistics/0
            if "/#/match-summary" in target_url:
                base_url = target_url.split("/#/")[0]
                target_url = f"{base_url}/#/match-summary/match-statistics/0"
            
            logger.info(f"Navigating to match stats: {target_url}")
            await page.goto(target_url)
            await page.wait_for_load_state('networkidle')
            
            # Wait for stats container
            try:
                await page.wait_for_selector('.stat__categoryName', timeout=10000)
            except Exception:
                logger.warning("Stats tab not found or empty")
                # Maybe it's not loaded yet or wrong URL, try clicking "Stats" tab if visible?
                # For now, just return None to avoid complexity
                return None

            # Take screenshot
            screenshot_bytes = await page.screenshot(full_page=False)
            
            # Analyze
            return await _analyze_screenshot(screenshot_bytes, home_team, away_team)

        except Exception as exc:
            logger.exception(f"Vision extraction failed: {exc}")
            return None
        finally:
            await browser.close()

async def _analyze_screenshot(image_bytes: bytes, home_team: str, away_team: str) -> Dict[str, Any]:
    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    prompt = f"""
    Analyze this football match statistics screenshot for {home_team} vs {away_team}.
    
    Extract the following in JSON format:
    {{
        "stats": {{
            "possession_home": "string (e.g. '55%')",
            "possession_away": "string",
            "xg_home": "float (or null)",
            "xg_away": "float (or null)",
            "shots_home": int,
            "shots_away": int,
            "shots_on_target_home": int,
            "shots_on_target_away": int,
            "corners_home": int,
            "corners_away": int
        }},
        "key_events": [
            {{ "minute": int, "type": "goal/card/sub", "player": "string", "team": "home/away" }}
        ]
    }}
    
    If key events are not visible in the stats screenshot, return an empty list for them.
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
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        content = response.choices[0].message.content
        import json
        return json.loads(content)
    except Exception as exc:
        logger.error(f"OpenAI Vision API error: {exc}")
        return None
