import requests
from bs4 import BeautifulSoup
import csv
from typing import List, Dict
import pandas as pd
import argparse
import numpy as np
import re
from sklearn.neighbors import KNeighborsRegressor
import glob
from sklearn.neighbors import KNeighborsRegressor
import time

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
    This function Normalize TFRRS time strings by removing any unwanted characters.
    This function keeps only digits, colons, and periods to preserve
    valid time formats.
    
    Parameters:
        raw_time (str): The raw time string scraped from TFRRS.

    Returns:
        str: A cleaned, normalized time string. 
    """
     if not raw_time:
        return ""
     
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
D1_URLS = {
    2025: "https://www.tfrrs.org/lists/5018/2025_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2024: "https://www.tfrrs.org/lists/4515/2024_NCAA_Division_I_Rankings_FINAL",
    2023: "https://www.tfrrs.org/lists/4044/2023_NCAA_Division_I_All_Schools_Rankings",
    2022: "https://www.tfrrs.org/lists/3711/2022_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2021: "https://api.tfrrs.org/lists/3191/2021_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2020: "https://www.tfrrs.org/lists/2909/2020_NCAA_Division_I_Outdoor_Qualifying",
    2019: "https://upload.tfrrs.org/lists/2568/2019_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2018: "https://www.tfrrs.org/lists/2279/2018_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2017: "https://www.tfrrs.org/lists/1912/2017_NCAA_Div_I_Outdoor_Qualifying_FINAL",
    2016: "https://www.tfrrs.org/lists/1688/2016_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2015: "https://api.tfrrs.org/lists/1439/2015_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2014: "https://www.tfrrs.org/lists/1228/2014_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2013: "https://www.tfrrs.org/lists/1029/2013_NCAA_Division_I_Outdoor_Qualifying_FINAL",
    2012: "https://www.tfrrs.org/lists/840/2012_NCAA_Div_I_Outdoor_Qualifiers_Final",
    2011: "https://www.tfrrs.org/lists/673/2011_NCAA_Division_I_Outdoor_POP_List_FINAL",
    2010: "https://tf.tfrrs.org/lists/528/2010_NCAA_Division_I_Outdoor_POP_List_FINAL"
}

def scrapeTffrsD1(year: int, gender: str, event: str) -> pd.DataFrame:
    """

    This function scrapes NCAA Division I Outdoor Qualifying results for a given year, gender,
    and event from the TFRRS website.

    This function:
      • Downloads the HTML page for the specified year's D1 qualifying list.  
      • Locates the specific event block using the event mapping extracted
        from the page. 
      • Supports both men's and women's result tables.  
      • Detects relay events and extracts relay‑specific fields.  
      • Converts times into cleaned, standardized strings.  
      • Adds qualifying logic.

    Parameters: 

    year : int
        The year of the national qualifing 
    gender : str
        men's or women's events 
    event : str
        The event label as it appears in TFRRS

    Returns: pd.DataFrame - A DataFrame containing one row per athlete or relay including other information such as time, gender, place etc..

    """
    base_url = D1_URLS[year]

    resp = requests.get(base_url, headers=headers, timeout=30)
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

    if short_label in RELAYS_TOP16:
        cutoff = 16
    else:
        cutoff = 48

    df["qualifying_cutoff"] = cutoff
    df["qualifies"] = df["place"] <= cutoff

    return df



#  D2 SCRAPER FUNCTION

D2_URLS = {
    2025: "https://www.tfrrs.org/lists/5019/2025_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2024: "https://www.tfrrs.org/lists/4516/2024_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2023: "https://www.tfrrs.org/lists/4045/2023_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2022: "https://www.tfrrs.org/lists/3595/2022_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2021: "https://www.tfrrs.org/lists/3194/2021_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2020: "https://www.tfrrs.org/lists/2908/2020_NCAA_Div_II_Outdoor_Qualifying",
    2019: "https://www.tfrrs.org/lists/2571/2019_NCAA_Div_II_Outdoor_Qualifying_FINAL",
    2018: "https://www.tfrrs.org/lists/2282/2018_NCAA_Div_II_Outdoor_Qualifying_FINAL",
    2017: "https://www.tfrrs.org/lists/1913/2017_NCAA_Div_II_Outdoor_Qualifying_FINAL",
    2016: "https://www.tfrrs.org/lists/1685/2016_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2015: "https://www.tfrrs.org/lists/1442/2015_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2014: "https://www.tfrrs.org/lists/1231/2014_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2013: "https://www.tfrrs.org/lists/1032/2013_NCAA_Division_II_Outdoor_Qualifying_FINAL",
    2012: "https://www.tfrrs.org/lists/841/2012_NCAA_Div_II_Outdoor_Qualifier_List_Final",
    2011: "https://www.tfrrs.org/lists/674/2011_NCAA_Division_II_Outdoor_POP_List_FINAL",
    2010: "https://www.tfrrs.org/lists/529/2010_NCAA_Division_II_Outdoor_POP_List_Final"
}

def scrapeTffrsD2(year: int, gender: str, event: str) -> pd.DataFrame:
    """
     This function scrapes NCAA Division II Outdoor Qualifying results for a given year, gender,
    and event from the TFRRS website.

    This function:
      • Downloads the HTML page for the specified year's D2 qualifying list.  
      • Locates the specific event block using the event mapping extracted
        from the page. 
      • Supports both men's and women's result tables.  
      • Detects relay events and extracts relay‑specific fields.  
      • Converts times into cleaned, standardized strings.  
      • Adds qualifying logic.

    Parameters: 

    year : int
        The year of the national qualifing 
    gender : str
        men's or women's events 
    event : str
        The event label as it appears in TFRRS

    Returns: pd.DataFrame - A DataFrame containing one row per athlete or relay including other information such as time, gender, place etc..

    """
    base_url = D2_URLS[year]

    resp = requests.get(base_url, headers=headers, timeout=30)
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

    if short_label in RELAYS_TOP16:
        cutoff = 16
    else:
        cutoff = 22

    df["qualifying_cutoff"] = cutoff
    df["qualifies"] = df["place"] <= cutoff

    return df




#  D3 SCRAPER FUNCTION

D3_URLS = {
    2025: "https://www.tfrrs.org/lists/5020/2025_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2024: "https://tfrrs.org/lists/4517/2024_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2023: "https://www.tfrrs.org/lists/4043/2023_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2022: "https://www.tfrrs.org/lists/3714/2022_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2021: "https://www.tfrrs.org/lists/3195/2021_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2020: "https://tfrrs.org/lists/2907/2020_NCAA_Div_III_Outdoor_Qualifying",
    2019: "https://www.tfrrs.org/lists/2572/2019_NCAA_Div_III_Outdoor_Qualifying_FINAL",
    2018: "https://www.tfrrs.org/lists/2283/2018_NCAA_Div_III_Outdoor_Qualifying_FINAL",
    2017: "https://www.tfrrs.org/lists/1914/2017_NCAA_Div_III_Outdoor_Qualifying_FINAL",
    2016: "https://www.tfrrs.org/lists/1684/2016_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2015: "https://www.tfrrs.org/lists/1443/2015_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2014: "https://www.tfrrs.org/lists/1232/2014_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2013: "https://www.tfrrs.org/lists/1033/2013_NCAA_Division_III_Outdoor_Qualifying_FINAL",
    2012: "https://www.tfrrs.org/lists/842/2012_NCAA_Div_III_Outdoor_Qualifier_List",
    2011: "https://www.tfrrs.org/lists/675/2011_NCAA_Division_III_Outdoor_POP_List_FINAL",
    2010: "https://www.tfrrs.org/lists/530/2010_NCAA_Division_III_Outdoor_Track__Field"
}

def scrapeTffrsD3(year: int, gender: str, event: str) -> pd.DataFrame:
    """
     This function scrapes NCAA Division I Outdoor Qualifying results for a given year, gender,
    and event from the TFRRS website.

    This function:
      • Downloads the HTML page for the specified year's D1 qualifying list.  
      • Locates the specific event block using the event mapping extracted
        from the page. 
      • Supports both men's and women's result tables.  
      • Detects relay events and extracts relay‑specific fields.  
      • Converts times into cleaned, standardized strings.  
      • Adds qualifying logic.

    Parameters: 

    year : int
        The year of the national qualifing 
    gender : str
        men's or women's events 
    event : str
        The event label as it appears in TFRRS

    Returns: pd.DataFrame - A DataFrame containing one row per athlete or relay including other information such as time, gender, place etc..

    """
    base_url = D3_URLS[year]


    resp = requests.get(base_url, headers=headers, timeout=30)
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

    if short_label in RELAYS_TOP16:
        cutoff = 16
    else:
        cutoff = 22

    df["qualifying_cutoff"] = cutoff
    df["qualifies"] = df["place"] <= cutoff

    return df

'''
#make CSV's


DIVISIONS = {
    "D1": scrapeTffrsD1,
    "D2": scrapeTffrsD2,
    "D3": scrapeTffrsD3
}
YEARS = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
GENDERS = ["men", "women"]

for div, scraper in DIVISIONS.items():
    for year in YEARS:
        for gender in GENDERS:

            # Gender‑specific hurdle events
            if gender == "men":
                events = [
                    "100", "200", "400", "800", "1500", "5000", "10000",
                    "110H", "400H", "4x100", "4x400"
                ]
            else:  # women
                events = [
                    "100", "200", "400", "800", "1500", "5000", "10000",
                    "100H", "400H", "4x100", "4x400"
                ]

            for event in events:
                try:
                    df = scraper(year, gender, event)
                    filename = f"{div}_{year}_{event}_{gender}.csv"
                    df.to_csv(filename, index=False)
                    print("Saved:", filename)
                except Exception as e: #stop from crahing entire loop
                    print("Error:", div, year, gender, event, e)

                time.sleep(0.5) #added to give TFFRS a break between requests

files = glob.glob("*.csv") # Finds every file in the current folder that ends with .csv  and puts them in a list

all_dfs = [pd.read_csv(f) for f in files] # Loops through the list of filenames and reads each CSV into a DataFrame
                                          # all_dfs becomes a list like: [df1, df2, df3, ...]

big_df = pd.concat(all_dfs, ignore_index=True) #Combines all DataFrames into one giant DataFrame
big_df.to_csv("all_results_2010_2025.csv", index=False)  

'''

def time_to_seconds(t: str) -> float:
    """
    This function converts and athletes time str into total seconds. 

    Parameters: 
    t : str - Raw time string scraped from TFRRS

    Returns: 
    float: Total time in seconds. If empty no value is shown. 
    """
    t = str(t).strip()
    if not t:
        return float("nan")

    parts = t.split(":")
    
    if len(parts) == 1:
            # e.g. '10.22'
            return float(parts[0])
    elif len(parts) == 2:
        # MM:SS.xx
        m = float(parts[0])
        s = float(parts[1])
        return m * 60 + s
    else:
        raise ValueError("Unexpected time format")



def seconds_to_time_str(seconds: float) -> str:
    """
     This function converts a time value in seconds back into a formatted string.

    Parameters:
    seconds : float - Total time in seconds 

    Returns:
    str: A formatted time string the way the time appears on TFFRS. 
    """
    if seconds < 60:
        return f"{seconds:0.2f}"

    m = int(seconds // 60)
    s = seconds - m * 60
    return f"{m}:{s:05.2f}"  # mm:ss.ss
        

def cutoff_place_for(division: str, event: str) -> int:
    """
    This function determines the qualifying-place cutoff for a given NCAA division and event.

    This function normalizes the event name and detects relays.  
    Relay events always use a top‑16 cutoff.  
    Individual events use:
        • Division I  → top 48  
        • Division II → top 22  
        • Division III → top 22

    Parameters: 
    division : str
        NCAA division label 
    event : str
        Event name as scraped or provided by the user
       

    Returns:
    int: The qualifying place cutoff for this division and event.
    """
    event_norm = event.replace(",", "").upper().strip()
    is_relay = event_norm.startswith("4X") or "RELAY" in event_norm

    if is_relay:
        return 16
    if division.upper() == "D1":
        return 48
    else:
        return 22

def predict_qualifying_for(big_df: pd.DataFrame, division: str, gender: str, event: str):
    """
    This function predicts the national qualifying cutoff mark for a given division, gender,
    and event using historical TFRRS data.

    This function:
      • Normalizes gender input 
      • Determines the qualifying cutoff place 
      • Extracts historical results for ONLY athletes/teams at that cutoff place
      • Converts times to seconds
      • Uses a KNN regression model using recent years (>= 2021)
      • Falls back to all years if not enough recent data
      • Prints the predicted qualifying time for 2026

    Parameters: 
    big_df : pd.DataFrame - Full dataset of all scraped results 
    division : str - NCAA division 
    gender : str - men or women
    event : str -  Normalized event code as seen on TFFRS
    
    Returns: None 
    """
    div = division.upper()
    gender_norm = gender.lower().strip()
    if gender_norm in ["mens", "men's"]:
        gender_norm = "men"
    if gender_norm in ["womens", "women's"]:
        gender_norm = "women"
    event_norm = event
    cutoff = cutoff_place_for(div, event_norm)


    # Filter to the rows for this group
    df_slice = big_df[
        (big_df["division"] == div) &
        (big_df["gender"] == gender_norm) &
        (big_df["event_code"] == event_norm) &
        (big_df["place"] == cutoff)
    ].copy()

    # If missing 
    if df_slice.empty:
        available = big_df[
            (big_df["division"] == div) &
            (big_df["gender"] == gender_norm) &
            (big_df["event_code"] == event_norm)
        ]["place"].unique()

        lower = [p for p in available if p < cutoff]
        if lower:
            fallback_place = max(lower)
            df_slice = big_df[
                (big_df["division"] == div) &
                (big_df["gender"] == gender_norm) &
                (big_df["event_code"] == event_norm) &
                (big_df["place"] == fallback_place)
            ].copy()
            

    df_slice["time_seconds"] = df_slice["time"].apply(time_to_seconds)
    df_slice = df_slice.dropna(subset=["time_seconds"])

    if df_slice.empty:
        print(f"No valid times for {div} {gender_norm} {event_norm}")
        return

    recent = df_slice[df_slice["year"] >= 2021] #use only recent years 

    if len(recent) >= 3:
        df_recent = recent
    else:
        df_recent = df_slice   # fallback to use all years

    if df_recent.empty:
        print(f"No valid times for {div} {gender_norm} {event_norm}")
        return

    X = df_recent[["year"]].values #convert to NumPy array 
    y = df_recent["time_seconds"].values #convert to NumPy array

    k = min(3, len(X))
    knn = KNeighborsRegressor(n_neighbors=k, weights="distance") #K nearest neighbors regression model, and making closer years count more than older years
    knn.fit(X, y) #.fit to train with year and time(converted to seconds)

    pred_sec = knn.predict([[2026]])[0] #2026 array with 1 value (predicted seconds)
    pred_str = seconds_to_time_str(pred_sec)

    print("\n==================================================")
    print(f"Predicted qualifying mark for {div} {gender_norm} {event_norm}, 2026:")
    print(f"→ Qualifying place: {cutoff}")
    print(f"→ Predicted cutoff time: {pred_str}")
    print("==================================================")

'''
def run_all_predictions(big_df: pd.DataFrame):
    """
    This function generates and print 2026 qualifying predictions for all NCAA divisions,
    both genders, and all standard track running events. 

    Parameters:
    big_df : pd.DataFrame - A dataframe containing historical TFRRS results with many colums 

    Returns: None
        
    """
    
    
    DIVISIONS = ["D1", "D2", "D3"]
    GENDERS = ["men", "women"]

    # Base events that apply to both genders
    BASE_EVENTS = [
        "100", "200", "400", "800", "1500", "5000", "10,000",
        "400H", "4x100", "4x400"
    ]

    print("\n================ ALL 2026 PREDICTIONS ================\n")

    for div in DIVISIONS:
        for gender in GENDERS:

            # Gender specific hurdle event
            hurdle_event = "110H" if gender == "men" else "100H"

            # Build final list for this gender
            EVENTS = BASE_EVENTS + [hurdle_event]

            for event in EVENTS:
                predict_qualifying_for(big_df, div, gender, event)

    print("\n================ DONE ================\n")




def test_scraper():
    print("\n=== TEST D1 1500m MEN ===")
    df1 = scrapeTffrsD1(2023, "men", "1500")
    print(df1[df1["qualifies"] == True][["place", "athlete", "time"]])

    print("\n=== TEST D2 100m MEN ===")
    df2 = scrapeTffrsD2(2022, "men", "100")
    print(df2[df2["qualifies"] == True][["place", "athlete", "time"]])

    print("\n=== TEST D3 5000m WOMEN ===")
    df3 = scrapeTffrsD3(2024, "women", "5000")
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

''' 

def getScraperForDivision(division: str):
    div = division.upper()
    if div == "D1":
        return scrapeTffrsD1
    elif div == "D2":
        return scrapeTffrsD2
    else: 
        return scrapeTffrsD3

def main():
    '''
    # Load the master dataset
    big_df = pd.read_csv("all_results_2021_2025.csv")
    print("Loaded master CSV with", len(big_df), "rows")
    
    # Run predictions for every event/div/gender
    run_all_predictions(big_df)
     '''
    parser = argparse.ArgumentParser(description="TFFRS scraper + predict NCAA qualifying marks for 2026")
    parser.add_argument("year", type=int, help="Year of interest (2010-2026)",)
    parser.add_argument("division", type=str, help="NCAA division (D1, D2, or D3)",)
    parser.add_argument("gender", type=str, help="Gender (men or women)",)
    parser.add_argument("event", type=str, help='Event code (e.g. "100", "1500", "4x100", "100H"/"110H")',)

    args = parser.parse_args()

    year = args.year
    division = args.division
    gender = args.gender
    event = args.event

    if 2010 <= year <= 2025:
        scraper = getScraperForDivision(division)
        print(f"Scraping {division} {gender} {event} for {year}...")
        df = scraper(year, gender, event)

        if df.empty:
            print("No data returned from scraper.")
            return

        cutoff = df["qualifying_cutoff"].iloc[0]
        numQual = (df["qualifies"] == True).sum()

        print(f"Cutoff place: {cutoff}, # qualifiers: {numQual}")
        print("\n================ Scraped Results ================")
        event_norm = event.replace(",", "").upper().strip()
        is_relay = event_norm.startswith("4X") or "Relay" in event_norm
        if is_relay:
            cols = ["place", "team", "time", "qualifies"]
        else:
            cols = ["place", "athlete", "time", "qualifies"]
        print(df[cols])
        print("=================================================\n")

    elif year == 2026:
        big_df = pd.read_csv("all_results_2010_2025.csv")
        print("Loaded master CSV with", len(big_df), "rows")

        predict_qualifying_for(big_df, division, gender, event)
    
    else:
        print("Year must be between 201o and 2026.")
        return

if __name__ == "__main__":
    main()
    #test_scraper()
