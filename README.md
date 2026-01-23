## Project Documentation  
**Ryan and Miles**

---

### Goal and Scope of the Project

The goal of this project was to build a robust Python pipeline capable of:

1. **Scraping TFRRS HTML pages** and extracting performance data based on user-specified inputs:
   - Year  
   - Division  
   - Gender  
   - Event  

2. **Returning the top results** for the selected parameters.

3. **Predicting the NCAA Division III qualifying time for 2026** using a machine learning model.  
   - If the user inputs **2026**, the scraper switches to the predictive model.

**Scope:**  
- Historical data coverage: **2010–2025**  
- Predictive model coverage: **2026**

---

### Required Python Libraries (Non-Default)

1. **requests**  
   Used to send HTTP requests to TFRRS webpages and retrieve the raw HTML.

2. **beautifulsoup4**  
   Parses HTML content and extracts meet results, tables, and performance fields.

3. **pandas**  
   Handles all tabular data operations, including cleaning, filtering, and exporting CSVs.

4. **numpy**  
   Supports array operations and numerical processing used in the ML workflow.

5. **scikit-learn (sklearn)**  
   The `KNeighborsRegressor` algorithm is used to predict future qualifying marks.

6. **glob** *(built-in; no installation needed)*  
   Helps load and combine multiple CSV files automatically.

---

### 🔧 Installation Instructions

To install all required libraries at once, run:

```bash
pip install requests beautifulsoup4 pandas numpy scikit-learn
