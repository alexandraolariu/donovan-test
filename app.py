import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# 1. CONFIGURARE PAGINĂ
st.set_page_config(page_title="Water License Portal", page_icon="💧", layout="wide")

# --- LISTA NEAGRĂ (Coloane ascunse/eliminate) ---
# Am scos "IssuedDate" de aici ca să o putem folosi în PDF
COLOANE_DE_SCOS = [
    "PostalStateDescription", "PostalCountryDescription", "StatutoryClassDesc",
    "AuthorisationTypeDesc", "AuthorisationStatusDesc", "AllocationClassDesc",
    "IsActive", "IsBillable", "WaterAccountList", 
    "WRPDescriptionList", "ROPDescription", "ROPLocationName", 
    "ROPLocationDescription", "MaxHeightMetre", "IsWaterAllocation", 
    "IsDevelopmentAuthorisation", "IsApproval", "IsNotice", 
    "IsStockDomestic", "BasinList", "IsWaterAuthorisation"
]

# Funcție utilitară pentru transformarea datei în format oficial (textual)
def format_official_date(date_str):
    if not date_str or str(date_str).lower() == 'n/a':
        return "DATE UNKNOWN"
        
    try:
        # Curățăm string-ul (scoatem orele dacă există)
        clean_date = str(date_str).split(' ')[0]
        
        # Încercăm cele mai comune formate de dată
        dt = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(clean_date, fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            return str(date_str) # Dacă nu recunoaște formatul, măcar returnează textul brut

        days_words = {
            1: "FIRST", 2: "SECOND", 3: "THIRD", 4: "FOURTH", 5: "FIFTH",
            6: "SIXTH", 7: "SEVENTH", 8: "EIGHTH", 9: "NINTH", 10: "TENTH",
            11: "ELEVENTH", 12: "TWELFTH", 13: "THIRTEENTH", 14: "FOURTEENTH",
            15: "FIFTEENTH", 16: "SIXTEENTH", 17: "SEVENTEENTH", 18: "EIGHTEENTH",
            19: "NINETEENTH", 20: "TWENTIETH", 21: "TWENTY-FIRST", 22: "TWENTY-SECOND",
            23: "TWENTY-THIRD", 24: "TWENTY-FOURTH", 25: "TWENTY-FIFTH",
            26: "TWENTY-SIXTH", 27: "TWENTY-SEVENTH", 28: "TWENTY-EIGHTH",
            29: "TWENTY-NINTH", 30: "THIRTIETH", 31: "THIRTY-FIRST"
        }
        
        months_words = {
            1: "JANUARY", 2: "FEBRUARY", 3: "MARCH", 4: "APRIL", 5: "MAY", 6: "JUNE",
            7: "JULY", 8: "AUGUST", 9: "SEPTEMBER", 10: "OCTOBER", 11: "NOVEMBER", 12: "DECEMBER"
        }
        
        day_text = days_words.get(dt.day, str(dt.day))
        month_text = months_words.get(dt.month, str(dt.month))
        
        return f"{day_text} day of {month_text} {dt.year}"
    except:
        return str(date_str) # În cel mai rău caz, dă-ne data exact cum e în tabel


# 2. CLASA PDF CU FOOTER AUTOMAT ȘI LINK
# 2. CLASA PDF CU HEADER (LOGO) ȘI FOOTER (LINK) AUTOMAT
class PDF_With_Footer(FPDF):
    def header(self):
        # Verificăm dacă fișierul logo există pentru a evita erorile
        if os.path.exists("donovanlogo.png"):
            # Poziționăm logo-ul în dreapta sus.
            # Parametrii: (cale_imagine, x, y, w, h)
            # Calculăm X: lățimea paginii (210) - marginea dreaptă (20) - lățimea imaginii (~40) = ~150
            # Y: marginea de sus (20) - o ajustare mică ca să nu fie lipit (-5)
            # W (lățime): 40mm (înălțimea se calculează automat proporțional dacă nu e specificată)
            self.image("donovanlogo.png", 150, 15, 40)
            
            # Resetăm cursorul după imagine ca să nu se suprapună cu titlul.
            # Dacă logo-ul e înalt, s-ar putea să ai nevoie de un pdf.ln(20) la începutul create_pdf
            self.set_y(20) 
        
    def footer(self):
        # Poziționăm cursorul la 1.5 cm de subsol
        self.set_y(-15)
        # ... restul codului footer-ului rămâne neschimbat ...
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 100, 100) # Un gri discret
        
        # Textul normal
        text_part1 = "This is not an official extract. For an official extract please contact "
        self.write(5, text_part1)
        
        # Textul cu link (albastru și subliniat)
        self.set_text_color(0, 0, 255)
        self.set_font("helvetica", "IU", 8)
        link_url = "https://www.business.qld.gov.au/industries/mining-energy-water/water/authorisations/licences/applications"
        self.write(5, "Business Queensland", link_url)
        
        # Resetăm culoarea pentru orice eventualitate
        self.set_text_color(0, 0, 0)

def create_pdf(data):
    pdf = PDF_With_Footer() 
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=25)
    
    # Header
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "WATER LICENCE", ln=True, align='C')
    pdf.set_font("helvetica", "I", 12)
    pdf.cell(0, 7, "Water Act 2000", ln=True, align='C')
    pdf.ln(15)

    def add_pdf_row(label, value, label_width=50):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(label_width, 8, f"{label}", border=0)
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(0, 8, f"{str(value)}", border=0)
        pdf.ln(2)

    # SECȚIUNE DATE PRINCIPALE
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(50, 8, "Reference")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(40, 8, str(data.get("Water License", "-")))
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 8, "Expiry Date")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, str(data.get("ExpiryDate", "30/06/2111")), ln=True)
    pdf.ln(2)

    # Restul câmpurilor
    add_pdf_row("Licensee", data.get("ClientLegalName", "-"))
    add_pdf_row("Authorised Purpose", data.get("AuthorisedPurposeList", "-"))
    add_pdf_row("Description of Land", data.get("LocationLandList", "-"))
    add_pdf_row("Nominal Entitlement", data.get('NominalEntitlementPerWaterYearAndUnits', '-'))
    add_pdf_row("Management Subgroup List", data.get("ManagementSubgroupList", "-"))
    add_pdf_row("Water Plan", data.get("WRPDescriptionList", "-"))
    add_pdf_row("Schedule A Conditions", data.get("ScheduleAConditionsList", "-"))
    
    pdf.ln(10)
    
    # Footer-ul actului (Textul legal și data dinamică)
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 6, "This water licence is subject to the conditions endorsed hereon or attached hereto.")
    pdf.ln(4)
    
    # Aplicăm formatarea dinamică pentru IssuedDate
    raw_date = data.get("IssuedDate", "N/A")
    formatted_date = format_official_date(raw_date)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, f"Given at Toowoomba this {formatted_date}.", ln=True)
    
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 6, "Delegate of the Chief Executive", ln=True)
    pdf.cell(0, 6, "Department of Regional Development, Manufacturing and Water", ln=True)

    return bytes(pdf.output())

# 3. DESIGN (CSS)
st.markdown("<style>.main { background-color: #f8f9fa; } #MainMenu, footer, header {visibility: hidden;} .detail-card { background-color: white; padding: 25px; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-top: 20px; }</style>", unsafe_allow_html=True)

# 4. ÎNCĂRCARE DATE
@st.cache_data(show_spinner="Loading database...")
def load_data():
    try:
        if os.path.exists("water-licence.parquet"):
            df = pd.read_parquet("water-licence.parquet")
        else:
            df = pd.read_csv("water-licence-attributes.csv", encoding='cp1252', on_bad_lines='skip')

        cols_to_drop = [c for c in df.columns if any(x.strip().lower() == c.strip().lower() for x in COLOANE_DE_SCOS)]
        df = df.drop(columns=cols_to_drop)

        if "AuthorisationReference" in df.columns:
            df = df.rename(columns={"AuthorisationReference": "Water License"})

        return df.fillna('N/A')
    except Exception as e:
        st.error(f"Eroare la încărcarea datelor: {e}")
        return pd.DataFrame()

df = load_data()

# 5. INTERFAȚA DE CĂUTARE
st.title("💧 Water License Search Portal")
st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1: s_name = st.text_input("👤 Legal Name:", placeholder="Search name...")
with c2: s_auth = st.text_input("🔢 Water License No:", placeholder="Search ID...")
with c3: s_water = st.text_input("🌊 Water Name/Type:", placeholder="Search source...")

d_show = df.copy()
# (Logica de filtrare rămâne neschimbată)
if s_name:
    t_col = "ClientLegalName" if "ClientLegalName" in d_show.columns else d_show.columns[0]
    d_show = d_show[d_show[t_col].astype(str).str.contains(s_name, case=False, na=False)]
if s_auth:
    if "Water License" in d_show.columns:
        d_show = d_show[d_show["Water License"].astype(str).str.contains(s_auth, case=False, na=False)]

final_df = d_show.head(100) if not (s_name or s_auth or s_water) else d_show

# 6. REZULTATE CU COLOANĂ ASCUNSĂ
if not final_df.empty:
    st.info("💡 Select a row to view and download full details.")
    # ASCUNDEM IssuedDate din tabel
    config = {"IssuedDate": None} 
    selection = st.dataframe(
        final_df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row",
        column_config=config
    )
else:
    st.warning("No results found.")
    selection = None

# 7. DETALII ȘI DOWNLOAD
if selection and selection.get("selection") and len(selection["selection"]["rows"]) > 0:
    selected_index = selection["selection"]["rows"][0]
    row_data = final_df.iloc[selected_index].to_dict()
    
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.subheader(f"🔍 Record Details: {row_data.get('Water License', 'N/A')}")
    
    pdf_bytes = create_pdf(row_data)
    csv_one = pd.DataFrame([row_data]).to_csv(index=False).encode('utf-8')

    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.download_button("📄 Download Official PDF", pdf_bytes, f"Licence_{row_data.get('Water License')}.pdf", "application/pdf")
    with b_col2:
        st.download_button("📥 Download CSV Record", csv_one, "record.csv", "text/csv")
    
    st.markdown("---")
    detail_cols = st.columns(3)
    # Afișăm detaliile dar SĂRIM peste IssuedDate în interfață
    display_data = {k: v for k, v in row_data.items() if k != "IssuedDate"}
    for i, (key, value) in enumerate(display_data.items()):
        with detail_cols[i % 3]:
            st.markdown(f"**{key}**")
            st.info(str(value))
    st.markdown('</div>', unsafe_allow_html=True)

# 8. EXPORT GLOBAL
if not d_show.empty:
    st.markdown("---")
    full_csv = d_show.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download All Filtered Results (CSV)", full_csv, "all_results.csv", "text/csv")
