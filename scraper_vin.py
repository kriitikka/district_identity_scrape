import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from thefuzz import process
import time
import io
import urllib3
import re

# --- CONFIGURATION ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DISTRICTS = [
    "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", 
    "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", 
    "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", 
    "Katni", "Khandwa", "Khargone", "Maihar", "Mandla", "Mauganj", "Mandsaur", "Morena", "Narsinghpur", "Neemuch", 
    "Niwari", "Panna", "Pandhurna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", 
    "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", 
    "Ujjain", "Umaria", "Vidisha"
]

# Expanded Keywords for Hindi compatibility
KEYWORDS_MAP = {
    "1. District Administration": ["Collector", "DM", "ADM", "Upper Collector", "Joint Collector", "Deputy Collector", "CEO Zila Panchayat", "Tehsildar", "Naib Tehsildar", "Patwari", "Revenue", "कलेक्टर", "जिलाधीश", "अपर कलेक्टर", "संयुक्त कलेक्टर", "डिप्टी कलेक्टर", "तहसीलदार", "नायब तहसीलदार"],
    "2. Police Department": ["Superintendent of Police", "SP", "Addl. SP", "DSP", "SHO", "Sub-Inspector", "SI", "Police", "Home Guards", "Cyber Crime", "पुलिस", "अधीक्षक", "थाना प्रभारी", "रक्षित निरीक्षक"],
    "3. Judiciary": ["District Judge", "Sessions Judge", "CJM", "Civil Judge", "Prosecution", "Public Prosecutor", "Legal Services", "न्यायाधीश", "न्याय", "अभियोजन"],
    "4. Health & Medical": ["CMHO", "Civil Surgeon", "Health Officer", "Malaria", "TB Officer", "Family Welfare", "Ayush", "Drug Inspector", "Medical", "स्वास्थ्य", "चिकित्सा", "सर्जन", "आयुष"],
    "5. School Education": ["DEO", "District Education Officer", "ADEO", "BEO", "DPC", "RMSA", "Mid-Day Meal", "Excellence School", "शिक्षा", "डीईओ", "बीईओ", "प्राचार्य"],
    "6. Higher Education": ["Principal", "Government College", "Professor", "Registrar", "Lead College", "Scholarship", "महाविद्यालय", "प्राचार्य", "उच्च शिक्षा"],
    "7. Agriculture": ["Agriculture", "Deputy Director Agriculture", "Horticulture", "Soil Conservation", "Kisan", "कृषि", "उप संचालक", "किसान", "उद्यानिकी"],
    "8. Horticulture": ["Horticulture", "Assistant Director Horticulture", "Food Processing", "उद्यानिकी", "फल", "सब्जी"],
    "9. Animal Husbandry": ["Veterinary", "Animal Husbandry", "Livestock", "VS", "AVFO", "Poultry", "पशु", "चिकित्सक", "पशुपालन"],
    "10. Public Works (PWD)": ["Executive Engineer", "PWD", "Assistant Engineer", "Sub-Engineer", "Bridge", "Road", "लोक निर्माण", "कार्यपालन यंत्री", "सड़क"],
    "11. Public Health Eng (PHE)": ["PHE", "Executive Engineer PHE", "Water Quality", "Handpump", "Jal Jeevan", "लोक स्वास्थ्य यांत्रिकी", "पेयजल"],
    "12. Water Resources": ["Water Resources", "Irrigation", "Canal", "Dam", "Tube Well", "जल संसाधन", "सिंचाई", "नहर"],
    "13. Forest Department": ["DFO", "Forest", "Ranger", "ACF", "Conservator", "Wildlife", "वन", "मंडलाधिकारी", "रेंजर", "परिक्षेत्र"],
    "14. Revenue Department": ["Revenue", "Land Records", "SLR", "Superintendent Land Records", "Nazul", "Diversion", "भू-अभिलेख", "राजस्व", "अधीक्षक"],
    "15. Social Justice": ["Social Justice", "Social Welfare", "Disability", "Pension", "Samagra", "सामाजिक न्याय", "निःशक्तजन", "पेंशन"],
    "16. Women & Child Dev": ["WCD", "Woman and Child", "Anganwadi", "CDPO", "Project Officer", "Supervisor", "Ladli Laxmi", "महिला", "बाल विकास", "परियोजना अधिकारी"],
    "17. Tribal Affairs": ["Tribal", "AC Tribal", "Adim Jati", "Scheduled Tribe", "Hostel", "Ashram", "आदिम जाति", "जनजाति", "कल्याण"],
    "18. Labour & Employment": ["Labour", "Employment Officer", "Exchange", "Shram", "Building Workers", "श्रम", "रोजगार", "पदाधिकारी"],
    "19. Industry & Commerce": ["Industry", "GM DIC", "Trade", "MSME", "Industrial Area", "DIC", "उद्योग", "व्यापार", "प्रबंधक"],
    "20. Food & Civil Supplies": ["Food Officer", "Supply Officer", "DSO", "Civil Supplies", "Ration", "PDS", "खाद्य", "आपूर्ति", "नागरिक आपूर्ति"],
    "21. Excise Department": ["Excise", "District Excise Officer", "Liquor", "आबकारी", "मद्य निषेध"],
    "22. Transport Department": ["RTO", "Transport", "DTO", "Vehicle", "License", "परिवहन", "आरटीओ", "गाड़ी"],
    "23. Cooperatives": ["Cooperative", "Registrar", "Bank", "Society", "Audit", "सहकारिता", "पंजीयक", "बैंक"],
    "24. Energy (Electricity)": ["Electricity", "MPEB", "Discom", "O&M", "Vidyut", "ऊर्जा", "विद्युत", "बिजली"],
    "25. Sports & Youth": ["Sports", "Youth Welfare", "Stadium", "Khelo India", "खेल", "युवा कल्याण"],
    "26. Public Relations": ["PRO", "Public Relations", "Information", "Jansampark", "जनसंपर्क", "सूचना"],
    "27. IT & e-Gov": ["NIC", "DIO", "Informatics", "e-Governance", "Digital", "विज्ञान", "सूचना प्रौद्योगिकी"],
    "28. Rural Development": ["Rural Development", "Panchayat", "NREGA", "RES", "Rural Engineering", "ग्रामीण", "पंचायत", "आरईएस"],
    "29. Urban Development": ["Municipality", "Municipal", "Nagar Palika", "CMO", "Parishad", "Nagar Nigam", "नगर पालिका", "निगम", "सीएमओ"],
    "30. Statistics": ["Statistics", "Planning", "Economics", "सांख्यिकी", "योजना"],
    "31. Consumer Affairs": ["Consumer", "Forum", "Court", "Protection", "उपभोक्ता", "संरक्षण"],
    "32. Election": ["Election", "Voter", "Voting", "Retruning Officer", "निर्वाचन", "चुनाव", "मतदाता"]
}

HEADER_PATTERNS = {
    "name": ["Name", "Official Name", "Officer Name", "Employee Name", "नाम", "अधिकारी का नाम", "Name of Officer", "अधिकारी"],
    "designation": ["Designation", "Post", "Portfolio", "पद", "पदनाम", "दायित्व"],
    "phone": ["Phone", "Mobile", "Contact", "Tel", "Cell", "No", "दूरभाष", "मोबाइल", "Telephone", "लैंड लाईन नंबर", "सम्पर्क"],
    "email": ["Email", "E-mail", "Address", "ईमेल", "ई-मेल", "पता"]
}

# --- HELPER FUNCTIONS ---

def get_base_domain(district_name):
    slug = district_name.lower().replace(" ", "").replace("-", "")
    return f"https://{slug}.nic.in"

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def get_candidate_urls(base_url, headers):
    """
    Generates a prioritized list of URLs to try:
    1. Scraped link from menu (High precision)
    2. English Standard Path
    3. Hindi Standard Path (Critical fallback)
    """
    candidates = []
    
    # 1. Deep Search (Menu Scan)
    try:
        response = requests.get(base_url, headers=headers, timeout=5, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            keywords = ["Who's Who", "Directory", "Officials", "संपर्क", "निर्देशिका", "कौन क्या है"]
            
            for link in soup.find_all('a', href=True):
                if any(k.lower() in clean_text(link.get_text()).lower() for k in keywords):
                    found = link['href']
                    if not found.startswith("http"):
                        if not found.startswith("/"): found = "/" + found
                        full = base_url + found
                        if full not in candidates: candidates.append(full)
    except:
        pass

    # 2. Add Standard Fallbacks (English THEN Hindi)
    candidates.append(base_url + "/en/about-district/whos-who/") # English
    candidates.append(base_url + "/about-district/whos-who/")    # Hindi (often default)
    candidates.append(base_url + "/directory/")
    
    return list(dict.fromkeys(candidates)) # Remove duplicates while preserving order

def parse_table_headers(table):
    header_map = {}
    rows = table.find_all('tr')
    if not rows: return None
    
    # Check first few rows for header-like content
    for i in range(min(3, len(rows))):
        cells = rows[i].find_all(['th', 'td'])
        temp_map = {}
        found_matches = 0
        
        for idx, col in enumerate(cells):
            text = clean_text(col.get_text())
            for key, patterns in HEADER_PATTERNS.items():
                match = process.extractOne(text, patterns)
                if match and match[1] > 80: 
                    if key not in temp_map:
                        temp_map[key] = idx
                        found_matches += 1
                    break
        
        # If we found at least Name and Designation, accept this row as header
        if 'name' in temp_map and 'designation' in temp_map:
            return temp_map, i + 1 # Return map and the index of the next row
            
    return None, 0

def scrape_district_directory(district, category_name):
    base_domain = get_base_domain(district)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    urls_to_try = get_candidate_urls(base_domain, headers)
    
    logs = []
    
    for url in urls_to_try:
        logs.append(f"Trying: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=12, verify=False)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            # --- FIX IS HERE: Corrected the fallback key to match the new numbered list ---
            # Old (Crashing): KEYWORDS_MAP.get(category_name, KEYWORDS_MAP["District Administration"])
            # New (Fixed):    KEYWORDS_MAP.get(category_name, KEYWORDS_MAP["1. District Administration"])
            category_keywords = KEYWORDS_MAP.get(category_name, KEYWORDS_MAP["1. District Administration"])
            
            page_results = []
            
            for table in tables:
                col_map, start_row = parse_table_headers(table)
                rows = table.find_all('tr')
                
                for row in rows[start_row:]:
                    cols = row.find_all('td')
                    if not cols: continue
                    clean_cols = [clean_text(c.get_text()) for c in cols]
                    
                    d_name, d_desig, d_phone, d_email = "", "", "", ""
                    
                    # Strategy A: Header Map
                    if col_map:
                        try:
                            if 'name' in col_map and len(cols) > col_map['name']: d_name = clean_cols[col_map['name']]
                            if 'designation' in col_map and len(cols) > col_map['designation']: d_desig = clean_cols[col_map['designation']]
                            if 'phone' in col_map and len(cols) > col_map['phone']: d_phone = clean_cols[col_map['phone']]
                            if 'email' in col_map and len(cols) > col_map['email']: d_email = clean_cols[col_map['email']]
                        except: continue

                    # Strategy B: Content Guessing
                    elif len(clean_cols) >= 2:
                        start_idx = 1 if (clean_cols[0].isdigit() and len(clean_cols[0]) < 4) else 0
                        if len(clean_cols) > start_idx + 1:
                            txt_A, txt_B = clean_cols[start_idx], clean_cols[start_idx+1]
                            match_A = process.extractOne(txt_A, category_keywords)
                            match_B = process.extractOne(txt_B, category_keywords)
                            sA = match_A[1] if match_A else 0
                            sB = match_B[1] if match_B else 0
                            
                            if sA > 60 and sA >= sB: d_desig, d_name = txt_A, txt_B
                            elif sB > 60: d_desig, d_name = txt_B, txt_A

                        for text in clean_cols:
                            if re.search(r'[6-9]\d{9}', text) or "07" in text: 
                                if len(text) < 40: d_phone = text
                            if "@" in text or "[at]" in text: d_email = text

                    # Filter by Category
                    if d_desig:
                        best_match = process.extractOne(d_desig, category_keywords)
                        if best_match and best_match[1] > 55:
                            page_results.append({
                                "District": district,
                                "Department": category_name,
                                "Designation": d_desig,
                                "Official Name": d_name,
                                "Phone": d_phone,
                                "Email": d_email,
                                "Source URL": url
                            })
            
            if len(page_results) > 0:
                return page_results, logs
        except Exception as e:
            logs.append(f"Error on {url}: {str(e)}")
            continue

    return [], logs
# --- STREAMLIT UI ---
st.set_page_config(page_title="MP District Gov Identity", layout="wide")
st.title("🏛️ MP Govt. Officials Identity Finder")
st.markdown("The Definitive Digital Directory for MP Administration\n")
st.markdown("55 Districts. 32 Departments. One Click.")
with st.sidebar:
    st.header("Settings")
    selected_district = st.selectbox("Select District", ["All 55 Districts"] + DISTRICTS)
    selected_category = st.selectbox("Select Department", list(KEYWORDS_MAP.keys()))
    run_btn = st.button("🚀 Start Scan", type="primary")

if run_btn:
    districts = DISTRICTS if selected_district == "All 55 Districts" else [selected_district]
    all_data = []
    
    prog_bar = st.progress(0)
    status_text = st.empty()
    log_expander = st.expander("Show Live Logs", expanded=True)
    
    for i, d in enumerate(districts):
        status_text.text(f"Scanning {d} ({i+1}/{len(districts)})...")
        
        data, logs = scrape_district_directory(d, selected_category)
        
        # Live Logging in Expander
        with log_expander:
            if data:
                st.success(f"{d}: Found {len(data)} records on {data[0]['Source URL']}")
            else:
                st.error(f"{d}: No data found.")
                for l in logs: st.caption(l)
                
        if data: all_data.extend(data)
        prog_bar.progress((i+1)/len(districts))
        
    status_text.text("✅ Processing Complete!")
    
    if all_data:
        df = pd.DataFrame(all_data)
        st.dataframe(df, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        st.download_button(" Download Excel", buffer.getvalue(), "MP_Data.xlsx")
    else:
        st.warning("No data found.")
