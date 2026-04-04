import streamlit as st
import pandas as pd
import os
from fpdf import FPDF

# 1. CONFIGURARE PAGINĂ
st.set_page_config(page_title="Water License Portal", page_icon="💧", layout="wide")

# --- LISTA NEAGRĂ (Coloane eliminate pentru memorie) ---
COLOANE_DE_SCOS = [
    "PostalStateDescription", "PostalCountryDescription", "StatutoryClassDesc",
    "AuthorisationTypeDesc", "AuthorisationStatusDesc", "AllocationClassDesc",
    "IsActive", "IsBillable", "IssuedDate", "WaterAccountList", 
    "WRPDescriptionList", "ROPDescription", "ROPLocationName", 
    "ROPLocationDescription", "MaxHeightMetre", "IsWaterAllocation", 
    "IsDevelopmentAuthorisation", "IsApproval", "IsNotice", 
    "IsStockDomestic", "BasinList", "IsWaterAuthorisation"
]

# 2. FUNCȚIE GENERARE PDF (Format Oficial - Inclusiv Expiry Date)
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    
    # Header
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "WATER LICENCE", ln=True, align='C')
    pdf.set_font("helvetica", "I", 12)
    pdf.cell(0, 7, "Water Act 2000", ln=True, align='C')
    pdf.ln(15)

    # Funcție internă pentru rânduri aliniate
    def add_pdf_row(label, value, label_width=50):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(label_width, 8, f"{label}", border=0)
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(0, 8, f"{str(value)}", border=0)
        pdf.ln(2)

    # SECȚIUNE DATE PRINCIPALE (Aliniere Reference și Expiry pe același rând)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(50, 8, "Reference")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(40, 8, str(data.get("Water License", "N/A")))
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 8, "Expiry Date")
    pdf.set_font("helvetica", "", 10)
    # Folosim coloana ExpiryDate (sau similară din dataset-ul tău)
    pdf.cell(0, 8, str(data.get("ExpiryDate", "30/06/2111")), ln=True)
    pdf.ln(2)

    # Restul câmpurilor
    add_pdf_row("Licensee", data.get("ClientLegalName", "N/A"))
    add_pdf_row("Authorised Activity", data.get("AuthorisationTypeDesc", "N/A"))
    add_pdf_row("Authorised Purpose", data.get("StatutoryClassDesc", "N/A"))
    
    # Adăugăm Description of Land dacă există în datele tale
    land = data.get("DescriptionOfLand", "N/A")
    add_pdf_row("Description of Land", land)
    
    volum = data.get('TotalVolume', 'N/A')
    add_pdf_row("Nominal Entitlement", f"{volum} Megalitres")
    
    pdf.ln(10)
    
    # Footer Text (Exact ca în imagine)
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 6, "This water licence is subject to the conditions endorsed hereon or attached hereto.")
    pdf.ln(4)
    
    # Data emiterii (Exemplu: fixat ca în imagine sau extras din date)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 8, "Given at Toowoomba this TWENTY-FIRST day of SEPTEMBER 2021.", ln=True)
    
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 6, "Delegate of the Chief Executive", ln=True)
    pdf.cell(0, 6, "Department of Regional Development, Manufacturing and Water", ln=True)

    return bytes(pdf.output())

# 3. DESIGN (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    #MainMenu, footer, header {visibility: hidden;}
    .detail-card { 
        background-color: white; padding: 25px; border-radius: 15px; 
        border: 1px solid #e0e0e0; box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

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
with c1: 
    s_name = st.text_input("👤 Legal Name:", placeholder="Search name...")
with c2: 
    s_auth = st.text_input("🔢 Water License No:", placeholder="Search ID...")
with c3: 
    s_water = st.text_input("🌊 Water Name/Type:", placeholder="Search source...")

# FILTRARE
d_show = df.copy()
if s_name:
    t_col = "ClientLegalName" if "ClientLegalName" in d_show.columns else d_show.columns[0]
    d_show = d_show[d_show[t_col].astype(str).str.contains(s_name, case=False, na=False)]
if s_auth:
    if "Water License" in d_show.columns:
        d_show = d_show[d_show["Water License"].astype(str).str.contains(s_auth, case=False, na=False)]
if s_water:
    w_cols = [c for c in d_show.columns if "WaterName" in c or "WaterName/Type" in c]
    if w_cols:
        d_show = d_show[d_show[w_cols[0]].astype(str).str.contains(s_water, case=False, na=False)]

# 6. REZULTATE
st.markdown(f"### 📋 Results ({len(d_show)} records found)")
final_df = d_show.head(100) if not (s_name or s_auth or s_water) else d_show

if not final_df.empty:
    st.info("💡 Select a row to view and download full details.")
    selection = st.dataframe(
        final_df, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row"
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
        st.download_button("📄 Download Official PDF", pdf_bytes, f"Licence_{row_data.get('Water License')}.pdf", "application/pdf", key="pdf_btn")
    with b_col2:
        st.download_button("📥 Download CSV Record", csv_one, "record.csv", "text/csv", key="csv_btn")
    
    st.markdown("---")
    detail_cols = st.columns(3)
    for i, (key, value) in enumerate(row_data.items()):
        with detail_cols[i % 3]:
            st.markdown(f"**{key}**")
            st.info(str(value))
    st.markdown('</div>', unsafe_allow_html=True)

# 8. EXPORT GLOBAL
if not d_show.empty:
    st.markdown("---")
    full_csv = d_show.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download All Filtered Results (CSV)", full_csv, "all_results.csv", "text/csv")
