# nba_prop_scraper.py
# Run this script manually or as a background service to fetch NBA props

import asyncio
from playwright.async_api import async_playwright
import json

OUTPUT_FILE = "nba_props.json"

async def scrape_fanduel_props():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://sportsbook.fanduel.com/navigation/nba", timeout=60000)
        await page.wait_for_timeout(8000)  # wait for dynamic JS to load

        content = await page.content()

        # Example parse: Extract player prop containers
        props = []
        elements = await page.locator('[data-test="event-market-container"]').all()
        for el in elements[:20]:
            try:
                text = await el.inner_text()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if len(lines) >= 3:
                    props.append({
                        "Player": lines[0],
                        "Prop": lines[1],
                        "Odds": lines[2]
                    })
            except:
                continue

        await browser.close()

        # Save to file
        with open(OUTPUT_FILE, "w") as f:
            json.dump(props, f, indent=2)
        print(f"Saved {len(props)} props to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(scrape_fanduel_props())

