import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from thefuzz import process
import time
import io

# --- CONFIGURATION & DATA ---
DISTRICTS = [
     "Datia", "Dindori","Jhabua" ,"Khargone", "Satna",
]

CATEGORIES = {
    "District Administration": ["Collector", "Additional Collector", "ADM", "Joint Collector", "Deputy Collector", "CEO Zila Panchayat", "Tehsildar"],
    "Police Department": ["Superintendent of Police", "Addl. SP", "DSP", "SHO", "Sub-Inspector"],
     "Election Department": ["Election Officer", "ERO", "AERO"],
}

## --- 2. SCRAPER ENGINE WITH BACKEND AUDIT ---
def scrape_district_directory(district, category_name):
    slug = district.lower().replace(" ", "")
    url = f"https://{slug}.nic.in/en/directory/"
    category_keywords = CATEGORIES[category_name]
    if CATEGORIES[category_name] == "Election Department":
        url = f"https://{slug}.nic.in/en/deo/"
    
    # DEV AUDIT: Start Log
    print(f"\n[AUDIT] Scanning District: {district.upper()}")
    print(f"[AUDIT] Target URL: {url}")
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[ERROR] {district} returned Status Code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        print(f"[AUDIT] Found {len(tables)} tables on page.")
        
        results = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    designation = cols[0].get_text(strip=True)
                    name = cols[1].get_text(strip=True)
                    
                    best_match = process.extractOne(designation, category_keywords)
                    if best_match and best_match[1] > 70:
                        results.append({
                            "District": district,
                            "Designation": designation,
                            "Official Name": name,
                            "Phone": cols[2].get_text(strip=True) if len(cols) > 2 else "N/A",
                            "Email": cols[3].get_text(strip=True) if len(cols) > 3 else "N/A"
                        })
                        
        
        print(f"[SUCCESS] Scraped {len(results)} matching officials for {district}.")
        return results

    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to scrape {district}: {str(e)}")
        return []

# --- 3. STREAMLIT INTERFACE ---
st.set_page_config(page_title="MP District Gov Identity", layout="wide")
st.title("🏛️ MP District Officials Scraper")

with st.sidebar:
    st.header("Search Parameters")
    selected_district = st.selectbox("Select District", ["All"] + DISTRICTS)
    selected_category = st.selectbox("Select Department", list(CATEGORIES.keys()))
    
    st.divider()
    fetch_btn = st.button("🚀 Run Scraper", width='stretch')

if fetch_btn:
    districts_to_scan = DISTRICTS if selected_district == "All" else [selected_district]
    final_data = []
    
    progress_text = "Operation in progress. Check VS Code terminal for logs."
    my_bar = st.progress(0, text=progress_text)
    
    for idx, dist in enumerate(districts_to_scan):
        scraped_rows = scrape_district_directory(dist, selected_category)
        final_data.extend(scraped_rows)
        # Update progress
        my_bar.progress((idx + 1) / len(districts_to_scan), text=f"Scanning {dist}...")
        time.sleep(0.5) # Prevent IP blocking

    if final_data:
        df = pd.DataFrame(final_data)
        st.subheader(f"📊 Scraped Results ({len(df)} entries found)")
        st.dataframe(df, width='stretch')
        
        # Excel Export
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Officials')
            
            st.download_button(
                label="📥 Download Consolidated Excel",
                data=output.getvalue(),
                file_name=f"MP_Officials_{selected_category.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )
        except Exception as e:
            st.error(f"Excel Generation Error: {e}. Ensure 'xlsxwriter' is installed.")
    else:
        st.error("No data found. Check the terminal for error logs.")