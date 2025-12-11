import requests
from bs4 import BeautifulSoup
import csv
from typing import List, Dict
import pandas as pd
import argparse
import numpy as np
import re

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

# CLEAN TIMES FUNCTION

def clean_time(raw_time: str) -> str:
    """
    Cleans TFRRS time strings by removing symbols
    Returns a normalized time string.
    """
    if not raw_time:
        return ""

    # remove everything that is not a digit, colon, or period
    cleaned = re.sub(r"[^0-9:\.]", "", raw_time)

    return cleaned

# EXTRACT EVENT ID FUNCTION

def extractEventMapping(soup: BeautifulSoup) -> Dict[str, str]:
    mapping = {}

    for a in soup.select("li a[href^='#event']"): # Select all <a> tags within <li> that have href starting with '#event'(^=)
        href = a.get("href")
        eventLabel = a.get_text(strip=True)
        eventID = href.split("#", 1)[1]  # Get the part after '#'
        mapping[eventID] = eventLabel

    return mapping



# D1 SCRAPER FUNCTION

def scrapeTffrsD1(year: int, gender: str, event: str) -> pd.DataFrame:
    base_url = "https://www.tfrrs.org/lists/5018/2025_NCAA_Division_I_Outdoor_Qualifying_FINAL"

    resp = requests.get(base_url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    codeMap = extractEventMapping(soup)
    userCodeNorm = event.replace(",", "").upper().strip()

    anchor_id = None
    for eid, label in codeMap.items():
        label_norm = label.replace(",", "").upper().strip()
        if label_norm == userCodeNorm:
            anchor_id = eid
            break

    if anchor_id is None:
        raise ValueError(f"[D1] Could not match event '{event}'.")

    short_label = codeMap[anchor_id]

    event_anchor = soup.find("a", {"id": anchor_id})
    event_block = event_anchor.find_next("div", class_="row")

    #handle women's results
    if gender.lower() == "women":
        event_block = event_block.find_next("div", class_="row")
    rows = event_block.select("div.performance-list-row")

    results = []

    # RELAY DETECTION
    is_relay = short_label.startswith("4x") or "Relay" in short_label

    for row in rows:
        place = row.find("div", {"data-label": "Place"})
        place = place.get_text(strip=True) if place else ""

        raw_time = row.find("div", {"data-label": "Time"})
        raw_time = raw_time.get_text(strip=True) if raw_time else ""

        if is_relay:
            # RELAYS ONLY: place + time + team
            results.append({
                "year": year,
                "division": "D1",
                "gender": gender.lower(),
                "event_code": short_label,
                "place": place,
                "athlete": "",
                "class_year": "",
                "team": row.find("div", {"data-label": "Team"}).get_text(strip=True),
                "time": clean_time(raw_time),
                "meet": row.find("div", {"data-label": "Meet"}).get_text(strip=True),
                "meet_date": row.find("div", {"data-label": "Meet Date"}).get_text(strip=True),
            })

        else:
            # NORMAL EVENTS 
            results.append({
                "year": year,
                "division": "D1",
                "gender": gender.lower(),
                "event_code": short_label,
                "place": place,
                "athlete": row.find("div", {"data-label": "Athlete"}).get_text(strip=True),
                "class_year": row.find("div", {"data-label": "Year"}).get_text(strip=True),
                "team": row.find("div", {"data-label": "Team"}).get_text(strip=True),
                "time": clean_time(raw_time),
                "meet": row.find("div", {"data-label": "Meet"}).get_text(strip=True),
                "meet_date": row.find("div", {"data-label": "Meet Date"}).get_text(strip=True),
            })

    df = pd.DataFrame(results)
    df["place"] = pd.to_numeric(df["place"], errors="coerce")

    # QUALIFYING LOGIC
    RELAYS_TOP16 = {"4x100", "4x400"}
    MULTI_TOP24 = {"Dec", "Hep"}

    if short_label in RELAYS_TOP16:
        cutoff = 16
    elif short_label in MULTI_TOP24:
        cutoff = 24
    else:
        cutoff = 48

    df["qualifying_cutoff"] = cutoff
    df["qualifies"] = df["place"] <= cutoff

    return df



#  D2 SCRAPER FUNCTION

def scrapeTffrsD2(year: int, gender: str, event: str) -> pd.DataFrame:
    base_url = "https://www.tfrrs.org/lists/5018/2025_NCAA_Division_II_Outdoor_Qualifying_FINAL"

    resp = requests.get(base_url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    codeMap = extractEventMapping(soup)
    userCodeNorm = event.replace(",", "").upper().strip()

    anchor_id = None
    for eid, label in codeMap.items():
        if label.replace(",", "").upper().strip() == userCodeNorm:
            anchor_id = eid
            break

    if anchor_id is None:
        raise ValueError(f"[D2] Could not match event '{event}'.")

    short_label = codeMap[anchor_id]

    event_anchor = soup.find("a", {"id": anchor_id})
    event_block = event_anchor.find_next("div", class_="row")

    #handle women's results
    if gender.lower() == "women":
        event_block = event_block.find_next("div", class_="row")
    rows = event_block.select("div.performance-list-row")

    results = []

    # RELAY DETECTION
    is_relay = short_label.startswith("4x") or "Relay" in short_label

    for row in rows:
        place = row.find("div", {"data-label": "Place"})
        place = place.get_text(strip=True) if place else ""

        raw_time = row.find("div", {"data-label": "Time"})
        raw_time = raw_time.get_text(strip=True) if raw_time else ""

        if is_relay:
            # RELAYS: only place + time + team
            results.append({
                "year": year,
                "division": "D2",
                "gender": gender.lower(),
                "event_code": short_label,
                "place": place,
                "athlete": "",
                "class_year": "",
                "team": row.find("div", {"data-label": "Team"}).get_text(strip=True),
                "time": clean_time(raw_time),
                "meet": row.find("div", {"data-label": "Meet"}).get_text(strip=True),
                "meet_date": row.find("div", {"data-label": "Meet Date"}).get_text(strip=True),
            })
        else:
            # INDIVIDUAL EVENTS
            results.append({
                "year": year,
                "division": "D2",
                "gender": gender.lower(),
                "event_code": short_label,
                "place": place,
                "athlete": row.find("div", {"data-label": "Athlete"}).get_text(strip=True),
                "class_year": row.find("div", {"data-label": "Year"}).get_text(strip=True),
                "team": row.find("div", {"data-label": "Team"}).get_text(strip=True),
                "time": clean_time(raw_time),
                "meet": row.find("div", {"data-label": "Meet"}).get_text(strip=True),
                "meet_date": row.find("div", {"data-label": "Meet Date"}).get_text(strip=True),
            })

    df = pd.DataFrame(results)
    df["place"] = pd.to_numeric(df["place"], errors="coerce")

    # QUALIFYING LOGIC
    RELAYS_TOP16 = {"4x100", "4x400"}
    MULTI_TOP24 = {"Dec", "Hep"}

    if short_label in RELAYS_TOP16:
        cutoff = 16
    elif short_label in MULTI_TOP24:
        cutoff = 24
    else:
        cutoff = 22

    df["qualifying_cutoff"] = cutoff
    df["qualifies"] = df["place"] <= cutoff

    return df




#  D3 SCRAPER FUNCTION

def scrapeTffrsD3(year: int, gender: str, event: str) -> pd.DataFrame:
    base_url = "https://www.tfrrs.org/lists/5020/2025_NCAA_Division_III_Outdoor_Qualifying_FINAL"

    resp = requests.get(base_url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    codeMap = extractEventMapping(soup)
    userCodeNorm = event.replace(",", "").upper().strip()

    anchor_id = None
    for eid, label in codeMap.items():
        if label.replace(",", "").upper().strip() == userCodeNorm:
            anchor_id = eid
            break

    if anchor_id is None:
        raise ValueError(f"[D3] Could not match event '{event}'.")

    short_label = codeMap[anchor_id]

    event_anchor = soup.find("a", {"id": anchor_id})
    event_block = event_anchor.find_next("div", class_="row")

    #handle women's results
    if gender.lower() == "women":
        event_block = event_block.find_next("div", class_="row")
    rows = event_block.select("div.performance-list-row")

    results = []

    # RELAY DETECTION
    is_relay = short_label.startswith("4x") or "Relay" in short_label

    for row in rows:
        place = row.find("div", {"data-label": "Place"})
        place = place.get_text(strip=True) if place else ""

        raw_time = row.find("div", {"data-label": "Time"})
        raw_time = raw_time.get_text(strip=True) if raw_time else ""

        if is_relay:
            # RELAYS: only place + time + team
            results.append({
                "year": year,
                "division": "D3",
                "gender": gender.lower(),
                "event_code": short_label,
                "place": place,
                "athlete": "",
                "class_year": "",
                "team": row.find("div", {"data-label": "Team"}).get_text(strip=True),
                "time": clean_time(raw_time),
                "meet": row.find("div", {"data-label": "Meet"}).get_text(strip=True),
                "meet_date": row.find("div", {"data-label": "Meet Date"}).get_text(strip=True),
            })
        else:
            # INDIVIDUAL EVENTS
            results.append({
                "year": year,
                "division": "D3",
                "gender": gender.lower(),
                "event_code": short_label,
                "place": place,
                "athlete": row.find("div", {"data-label": "Athlete"}).get_text(strip=True),
                "class_year": row.find("div", {"data-label": "Year"}).get_text(strip=True),
                "team": row.find("div", {"data-label": "Team"}).get_text(strip=True),
                "time": clean_time(raw_time),
                "meet": row.find("div", {"data-label": "Meet"}).get_text(strip=True),
                "meet_date": row.find("div", {"data-label": "Meet Date"}).get_text(strip=True),
            })

    df = pd.DataFrame(results)
    df["place"] = pd.to_numeric(df["place"], errors="coerce")

    # QUALIFYING LOGIC
    RELAYS_TOP16 = {"4x100", "4x400"}
    MULTI_TOP24 = {"Dec", "Hep"}

    if short_label in RELAYS_TOP16:
        cutoff = 16
    elif short_label in MULTI_TOP24:
        cutoff = 24
    else:
        cutoff = 22

    df["qualifying_cutoff"] = cutoff
    df["qualifies"] = df["place"] <= cutoff

    return df



# TEST BLOCK

def test_scraper():
    print("\n=== TEST D1 1500m MEN ===")
    df1 = scrapeTffrsD1(2025, "men", "1500")
    print(df1[df1["qualifies"] == True][["place", "athlete", "time"]])

    print("\n=== TEST D2 100m MEN ===")
    df2 = scrapeTffrsD2(2025, "men", "100")
    print(df2[df2["qualifies"] == True][["place", "athlete", "time"]])

    print("\n=== TEST D3 5000m WOMEN ===")
    df3 = scrapeTffrsD3(2025, "women", "5000")
    print(df3[df3["qualifies"] == True][["place", "athlete", "time"]])
    
    print("\n=== TEST D1 4x400 RELAY MEN ===")
    df_relay = scrapeTffrsD1(2025, "men", "4x400")
    print(df_relay[df_relay["qualifies"] == True][["place", "team", "time"]])
    
    print("\n=== TEST D2 4x100 RELAY MEN ===")
    df_relay = scrapeTffrsD2(2025, "men", "4x100")
    print(df_relay[df_relay["qualifies"] == True][["place", "team", "time"]])

    print("\n=== TEST D3 4x400 RELAY MEN ===")
    df_relay = scrapeTffrsD3(2025, "men", "4x400")
    print(df_relay[df_relay["qualifies"] == True][["place", "team", "time"]])



if __name__ == "__main__":
    test_scraper()