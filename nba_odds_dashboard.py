# all_bookmakers_scraper.py
# Combined scraper for FanDuel, DraftKings, BetMGM, and Hard Rock (if accessible)

import asyncio
from playwright.async_api import async_playwright
import json
import pandas as pd
import streamlit as st

OUTPUT_FILE = "nba_combined_props.json"

async def scrape_all_books():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        all_props = []

        # --- FanDuel ---
        try:
            await page.goto("https://sportsbook.fanduel.com/navigation/nba", timeout=60000)
            await page.wait_for_timeout(8000)
            elements = await page.locator('[data-test="event-market-container"]').all()
            for el in elements[:20]:
                try:
                    text = await el.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) >= 3:
                        all_props.append({
                            "Player": lines[0],
                            "Prop": lines[1],
                            "Odds": lines[2],
                            "Bookmaker": "FanDuel"
                        })
                except:
                    continue
        except Exception as e:
            print("FanDuel scrape failed:", e)

        # --- DraftKings ---
        try:
            await page.goto("https://sportsbook.draftkings.com/leagues/basketball/nba", timeout=60000)
            await page.wait_for_timeout(8000)
            elements = await page.locator("[data-test-id='event-cell']").all()
            for el in elements[:30]:
                try:
                    text = await el.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) >= 3:
                        all_props.append({
                            "Player": lines[0],
                            "Prop": lines[1],
                            "Odds": lines[2],
                            "Bookmaker": "DraftKings"
                        })
                except:
                    continue
        except Exception as e:
            print("DraftKings scrape failed:", e)

        # --- BetMGM ---
        try:
            await page.goto("https://sports.nj.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004", timeout=60000)
            await page.wait_for_timeout(8000)
            elements = await page.locator('div[class*="event-cell"]').all()
            for el in elements[:30]:
                try:
                    text = await el.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) >= 3:
                        all_props.append({
                            "Player": lines[0],
                            "Prop": lines[1],
                            "Odds": lines[2],
                            "Bookmaker": "BetMGM"
                        })
                except:
                    continue
        except Exception as e:
            print("BetMGM scrape failed:", e)

        # --- Hard Rock Bet (placeholder only — may be geo-restricted) ---
        try:
            await page.goto("https://sportsbook.hardrock.bet/sports/basketball/nba", timeout=60000)
            await page.wait_for_timeout(8000)
            elements = await page.locator("div[data-testid*='market-container']").all()
            for el in elements[:20]:
                try:
                    text = await el.inner_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) >= 3:
                        all_props.append({
                            "Player": lines[0],
                            "Prop": lines[1],
                            "Odds": lines[2],
                            "Bookmaker": "Hard Rock"
                        })
                except:
                    continue
        except Exception as e:
            print("Hard Rock scrape failed or blocked:", e)

        # Save all collected props as side-by-side grouped structure
        df = pd.DataFrame(all_props)

        if not df.empty:
            df_grouped = df.pivot_table(
                index=["Player", "Prop"],
                columns="Bookmaker",
                values="Odds",
                aggfunc="first"
            ).reset_index()
            grouped_output = df_grouped.to_dict(orient="records")
            st.dataframe(df_grouped)
        else:
            grouped_output = []
            st.warning("No prop data was collected.")

        with open(OUTPUT_FILE, "w") as f:
            json.dump(grouped_output, f, indent=2)
        print(f"Saved {len(all_props)} total props to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(scrape_all_books())

