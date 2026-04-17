import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# 1. CONFIGURARE PAGINĂ STREAMLIT
st.set_page_config(page_title="Water License Portal", page_icon="💧", layout="wide")

# --- LISTA NEAGRĂ (Coloane eliminate din vizualizare, dar păstrate pentru PDF) ---
COLOANE_DE_SCOS = [
    "PostalStateDescription", "PostalCountryDescription", "StatutoryClassDesc",
    "AuthorisationTypeDesc", "AuthorisationStatusDesc", "AllocationClassDesc",
    "IsActive", "IsBillable", "WaterAccountList", 
    "WRPDescriptionList", "ROPDescription", "ROPLocationName", 
    "ROPLocationDescription", "MaxHeightMetre", "IsWaterAllocation", 
    "IsDevelopmentAuthorisation", "IsApproval", "IsNotice", 
    "IsStockDomestic", "BasinList", "IsWaterAuthorisation"
]

# --- FUNCȚIE CONVERSIE DATĂ ÎN FORMAT OFICIAL ---
def format_official_date(date_str):
    if not date_str or str(date_str).lower() == 'n/a':
        return "TWENTY-FIRST day of SEPTEMBER 2021"
        
    try:
        clean_date = str(date_str).split(' ')[0]
        dt = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(clean_date, fmt)
                break
            except ValueError:
                continue
        
        if dt is None: return str(date_str)

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
        
        return f"{days_words.get(dt.day, dt.day)} day of {months_words.get(dt.month, dt.month)} {dt.year}"
    except:
        return str(date_str)

# 2. CLASA PDF CU LOGO ÎN HEADER ȘI LINK ÎN FOOTER
class PDF_With_Extras(FPDF):
    def header(self):
        if os.path.exists("donovanlogo.png"):
            # Poziționat în dreapta sus (x=165, y=10)
            self.image("donovanlogo.png", 165, 10, 30)
        self.set_y(25)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.write(5, "This is not an official extract. For an official extract please contact ")
        self.set_text_color(0, 0, 255)
        self.set_font("helvetica", "IU", 8)
        link = "https://www.business.qld.gov.au/industries/mining-energy-water/water/authorisations/licences/applications"
        self.write(5, "Business Queensland", link)

def create_pdf(data):
    pdf = PDF_With_Extras()
    pdf.add_page()
    pdf.set_margins(25, 20, 25)
    
    # TITLU
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 7, "WATER LICENCE", ln=True, align='C')
    pdf.set_font("helvetica", "BI", 11)
    pdf.cell(0, 7, "Water Act 2000", ln=True, align='C')
    pdf.ln(12)

    # Funcție internă pentru rânduri aliniate (stil tabel oficial)
    def add_row(label, value):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(45, 8, label, border=0)
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(0, 8, str(value), border=0)
        pdf.ln(1)

    # DATE PRINCIPALE (Reference & Expiry)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(45, 8, "Reference")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(55, 8, str(data.get("Water License", "-")))
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(30, 8, "Expiry Date")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, str(data.get("ExpiryDate", "30/06/2111")), ln=True)
    pdf.ln(1)

    # SECȚIUNI CONFORM IMAGINII
    add_row("Licensee", data.get("ClientLegalName", "-"))
    add_row("Authorised Activity", data.get("AuthorisedActivity", "The taking of water..."))
    add_row("Authorised Purpose", data.get("AuthorisedPurposeList", "-"))
    add_row("Description of Land", data.get("LocationLandList", "-"))
    add_row("Nominal Entitlement", f"{data.get('NominalEntitlementPerWaterYearAndUnits', '-')}")

    pdf.ln(8)
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 5, "This water licence is subject to the conditions endorsed hereon or attached hereto.")
    pdf.ln(4)
    
    # DATA DINAMICĂ
    formatted_date = format_official_date(data.get("IssuedDate", ""))
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, f"Given at Toowoomba this {formatted_date}.", ln=True)
    
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 5, "Delegate of the Chief Executive", ln=True)
    pdf.cell(0, 5, "Department of Regional Development, Manufacturing and Water", ln=True)

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
        
        # Eliminăm coloanele inutile, dar PĂSTRĂM IssuedDate pentru PDF
        cols_to_drop = [c for c in df.columns if any(x.strip().lower() == c.strip().lower() for x in COLOANE_DE_SCOS)]
        df = df.drop(columns=cols_to_drop)

        if "AuthorisationReference" in df.columns:
            df = df.rename(columns={"AuthorisationReference": "Water License"})
        return df.fillna('N/A')
    except Exception as e:
        st.error(f"Eroare: {e}")
        return pd.DataFrame()

df = load_data()

# 5. INTERFAȚA
st.title("💧 Water License Search Portal")
st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1: s_name = st.text_input("👤 Legal Name:")
with c2: s_auth = st.text_input("🔢 Water License No:")
with c3: s_water = st.text_input("🌊 Water Name/Type:")

d_show = df.copy()
if s_name: d_show = d_show[d_show["ClientLegalName"].astype(str).str.contains(s_name, case=False, na=False)]
if s_auth: d_show = d_show[d_show["Water License"].astype(str).str.contains(s_auth, case=False, na=False)]

# 6. REZULTATE
final_df = d_show.head(100) if not (s_name or s_auth) else d_show

if not final_df.empty:
    config = {"IssuedDate": None} # Ascundem data emiterii din tabelul principal
    selection = st.dataframe(
        final_df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row", column_config=config
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
    
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.download_button("📄 Download Official PDF", pdf_bytes, f"Licence_{row_data.get('Water License')}.pdf", "application/pdf")
    with b_col2:
        csv_record = pd.DataFrame([row_data]).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV Record", csv_record, "record.csv", "text/csv")
    
    st.markdown("---")
    # Afișăm detaliile în UI (fără IssuedDate)
    ui_display = {k: v for k, v in row_data.items() if k != "IssuedDate"}
    detail_cols = st.columns(3)
    for i, (key, value) in enumerate(ui_display.items()):
        with detail_cols[i % 3]:
            st.markdown(f"**{key}**")
            st.info(str(value))
    st.markdown('</div>', unsafe_allow_html=True)
