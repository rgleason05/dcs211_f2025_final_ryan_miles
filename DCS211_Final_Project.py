import requests
from bs4 import BeautifulSoup
import csv
from typing import List, Dict
import pandas as pd
import argparse
import numpy as np

#Ryan and Miles

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

'''
testURL = "https://www.tfrrs.org/lists/5020/2025_NCAA_Division_III_Outdoor_Qualifying_FINAL#event6"

resp = requests.get(testURL, headers=headers, timeout=10)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")

# 1. Find the anchor for the event you care about (event6 = men's 100m)
event_anchor = soup.find("a", {"id": "event6"})
if event_anchor is None:
    print("Couldn't find event6 anchor")
    exit()

# 2. The actual event block is the next <div class="row ..."> after that anchor
event_block = event_anchor.find_next("div", class_="row")
if event_block is None:
    print("Couldn't find event block for event6")
    exit()

# 3. Inside that block, all result rows have class "performance-list-row"
rows = event_block.select("div.performance-list-row")
print(f"Found {len(rows)} performance rows for men's 100m.\n")

results = []

for row in rows:
    place_div = row.find("div", {"data-label": "Place"})
    athlete_div = row.find("div", {"data-label": "Athlete"})
    year_div = row.find("div", {"data-label": "Year"})
    team_div = row.find("div", {"data-label": "Team"})
    time_div = row.find("div", {"data-label": "Time"})
    meet_div = row.find("div", {"data-label": "Meet"})
    meet_date_div = row.find("div", {"data-label": "Meet Date"})

    place = place_div.get_text(strip=True) if place_div else ""
    athlete = athlete_div.get_text(strip=True) if athlete_div else ""
    year = year_div.get_text(strip=True) if year_div else ""
    team = team_div.get_text(strip=True) if team_div else ""
    time = time_div.get_text(strip=True) if time_div else ""
    meet = meet_div.get_text(strip=True) if meet_div else ""
    meet_date = meet_date_div.get_text(strip=True) if meet_date_div else ""
    

    result = {
        "event": "100 Meters",
        "gender": "Men",
        "place": place,
        "athlete": athlete,
        "year": year,
        "team": team,
        "time": time,
        "meet": meet,
        "meet_date": meet_date,
    }
    results.append(result)

# Print first 5 to check
for r in results[:48]:
    print(r)

df = pd.DataFrame(results)
df["place"] = df["place"].astype(int)
df_top22 = df[df["place"] <= 22]
print(df_top22[["place", "athlete", "time"]])

df["time"] = df["time"].astype(float)

df.to_csv("100m_men_2025.csv", index=False)
'''


def extractEventMapping(soup: BeautifulSoup) -> Dict[str, str]:
    mapping = {}

    for a in soup.select("li a[href^='#event']"): # Select all <a> tags within <li> that have href starting with '#event'(^=)
        href = a.get("href")
        eventLabel = a.get_text(strip=True)
        eventID = href.split("#", 1)[1]  # Get the part after '#'
        mapping[eventID] = eventLabel

    return mapping

def scrapeTffrsD1(year: int, gender: str, event: str) -> pd.DataFrame:
    base_url = "https://www.tfrrs.org/lists/5019/2025_NCAA_Division_I_Outdoor_Qualifying_FINAL"

    # 1. Fetch webpage
    resp = requests.get(base_url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 2. Event ID → label mapping (event6 → "100", event22 → "10,000", etc.)
    codeMap = extractEventMapping(soup)

    # Normalize the user's event name ("10,000" → "10000")
    userCodeNorm = event.replace(",", "").upper().strip()

    anchor_id = None
    for eid, label in codeMap.items():
        label_norm = label.replace(",", "").upper().strip()
        if label_norm == userCodeNorm:
            anchor_id = eid
            break

    if anchor_id is None:
        raise ValueError(
            f"[D1] Could not match event: {event}. Available: {sorted(codeMap.values())}"
        )

    short_label = codeMap[anchor_id]
    print(f"[D1] Matched event '{event}' -> {anchor_id} ({short_label})")

    # 3. Find the event block
    event_anchor = soup.find("a", {"id": anchor_id})
    if event_anchor is None:
        raise RuntimeError(f"[D1] Could not find anchor id={anchor_id}")

    event_block = event_anchor.find_next("div", class_="row")
    if event_block is None:
        raise RuntimeError(f"[D1] Could not find event block for id={anchor_id}")

    rows = event_block.select("div.performance-list-row")
    print(f"[D1] Found {len(rows)} rows for event {short_label}.\n")

    # 4. Extract row data (your explicit style)
    results: List[Dict] = []

    for row in rows:
        place_div = row.find("div", {"data-label": "Place"})
        athlete_div = row.find("div", {"data-label": "Athlete"})
        class_year_div = row.find("div", {"data-label": "Year"})
        team_div = row.find("div", {"data-label": "Team"})
        time_div = row.find("div", {"data-label": "Time"})
        meet_div = row.find("div", {"data-label": "Meet"})
        meet_date_div = row.find("div", {"data-label": "Meet Date"})

        place = place_div.get_text(strip=True) if place_div else ""
        athlete = athlete_div.get_text(strip=True) if athlete_div else ""
        class_year = class_year_div.get_text(strip=True) if class_year_div else ""
        team = team_div.get_text(strip=True) if team_div else ""
        time = time_div.get_text(strip=True) if time_div else ""
        meet = meet_div.get_text(strip=True) if meet_div else ""
        meet_date = meet_date_div.get_text(strip=True) if meet_date_div else ""

        result = {
            "year": year,                  # season year, e.g. 2025
            "division": "D1",
            "gender": gender.lower(),
            "event_code": short_label,     # e.g. "100"
            "place": place,
            "athlete": athlete,
            "class_year": class_year,      # FR-1 / SR-4 etc
            "team": team,
            "time": time,
            "meet": meet,
            "meet_date": meet_date,
        }
        results.append(result)

    df = pd.DataFrame(results)
    df["place"] = pd.to_numeric(df["place"], errors="coerce")
    df["time"] = pd.to_numeric(df["time"], errors="coerce")

    TOP16_EVENTS = {"4x100", "4x400", "Dec", "Hep"}

    if short_label in TOP16_EVENTS:
        qualifying_cutoff = 16
    else:
        qualifying_cutoff = 22

    df["qualifying_cutoff"] = qualifying_cutoff
    df["qualifies"] = df["place"] <= qualifying_cutoff

    return df



#def scrapeTffrsD2(year: int, gender: str, event: str) -> pd.DataFrame:


#def scrapeTffrsD3(year: int, gender: str, event: str) -> pd.DataFrame:



if __name__ == "__main__":
    df_test = scrapeTffrsD1(2025, "men", "100")
    print(df_test.head(10))  # show first 10 rows
    print("\n=== QUALIFIERS ONLY ===")
    qualifiers = df_test[df_test["qualifies"]]
    print(qualifiers[["place", "athlete", "time"]])