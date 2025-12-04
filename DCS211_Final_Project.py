import requests
from bs4 import BeautifulSoup
import csv
from typing import List, Dict
import pandas as pd
#Ryan and Miles
testURL = "https://www.tfrrs.org/lists/5020/2025_NCAA_Division_III_Outdoor_Qualifying_FINAL#event6"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

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
    wind_div = row.find("div", {"data-label": "Wind"})

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
print(df_top22)

df["time"] = df["time"].astype(float)

df.to_csv("100m_men_2025.csv", index=False)
