
import streamlit as st
import pandas as pd
# Import your functions from your main project file
from DCS211_Final_Project import (getScraperForDivision, predict_qualifying_for)

st.title("NCAA Track & Field Qualifying Predictor")

st.write("Select your inputs below:")

# User Inputs

year = st.number_input(
    "Year",
    min_value=2010,
    max_value=2026,
    value=2026
)

division = st.selectbox(
    "Division",
    ["D1", "D2", "D3"]
)

gender = st.selectbox(
    "Gender",
    ["men", "women"]
)

event = st.text_input(
    "Event (examples: 100, 1500, 4x400, 100H, 110H)"
)

#Run Button

if st.button("Run"):
    if year == 2026:
        big_df = pd.read_csv("all_results_2010_2025.csv")
        result = predict_qualifying_for(big_df, division, gender, event)
        st.success(result)
    else:
        scraper = getScraperForDivision(division)
        df = scraper(year, gender, event)
        st.dataframe(df)