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

# 2. FUNCȚIE GENERARE PDF (Format Oficial)
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

    # Tabel Date (Format "Label: Value")
    def add_pdf_row(label, value):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(50, 8, f"{label}", border=0)
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(0, 8, f"{str(value)}", border=0)
        pdf.ln(2)

    # Mapare date pe etichete oficiale
    add_pdf_row("Reference", data.get("Water License", "N/A"))
    add_pdf_row("Licensee", data.get("ClientLegalName", "N/A"))
    add_pdf_row("Authorised Activity", data.get("AuthorisationTypeDesc", "N/A"))
    add_pdf_row("Authorised Purpose", data.get("StatutoryClassDesc", "N/A"))
    
    # Verificăm dacă există coloana de volum, altfel punem N/A
    volum = data.get('TotalVolume', 'N/A')
    add_pdf_row("Nominal Entitlement", f"{volum} Megalitres")
    
    pdf.ln(15)
    
    # Footer Legal
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 6, "This water licence is subject to the conditions endorsed hereon or attached hereto.")
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 6, "Delegate of the Chief Executive", ln=True)
    pdf.cell(0, 6, "Department of Regional Development, Manufacturing and Water", ln=True)

    return pdf.output()

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
        # Încearcă Parquet apoi CSV
        if os.path.exists("water-licence.parquet"):
            df = pd.read_parquet("water-licence.parquet")
        else:
            df = pd.read_csv("water-licence-attributes.csv", encoding='cp1252', on_bad_lines='skip')

        # Curățare coloane
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

# LOGICA DE FILTRARE
d_show = df.copy()

if s_name:
    target_name_col = "ClientLegalName" if "ClientLegalName" in d_show.columns else d_show.columns[0]
    d_show = d_show[d_show[target_name_col].astype(str).str.contains(s_name, case=False, na=False)]

if s_auth:
    if "Water License" in d_show.columns:
        d_show = d_show[d_show["Water License"].astype(str).str.contains(s_auth, case=False, na=False)]

if s_water:
    water_cols = [c for c in d_show.columns if "WaterName" in c or "WaterName/Type" in c]
    if water_cols:
        d_show = d_show[d_show[water_cols[0]].astype(str).str.contains(s_water, case=False, na=False)]

# 6. AFIȘARE REZULTATE
st.markdown(f"### 📋 Results ({len(d_show)} records found)")

final_df = d_show.head(100) if not (s_name or s_auth or s_water) else d_show

if not final_df.empty:
    st.info("💡 Select a row to view and download full details.")
    selection = st.dataframe(
        final_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
else:
    st.warning("No results found.")
    selection = None

# 7. DETALII RÂND SELECTAT & DOWNLOAD PDF
if selection and selection.get("selection") and len(selection["selection"]["rows"]) > 0:
    selected_index = selection["selection"]["rows"][0]
    row_data = final_df.iloc[selected_index].to_dict()
    
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.subheader(f"🔍 Record Details: {row_data.get('Water License', 'N/A')}")
    
    # Generare fișiere pentru download
    pdf_bytes = create_pdf(row_data)
    csv_bytes = pd.DataFrame([row_data]).to_csv(index=False).encode('utf-8')

    # Butoane Download
    btn1, btn2 = st.columns(2)
    with btn1:
        st.download_button("📄 Download Official PDF", pdf_bytes, f"Licence_{row_data.get('Water License')}.pdf", "application/pdf")
    with btn2:
        st.download_button("📥 Download CSV Data", csv_bytes, "record.csv", "text/csv")
    
    st.markdown("---")
    
    # Afișare vizuală a tuturor datelor în coloane
    detail_cols = st.columns(3)
    for i, (key, value) in enumerate(row_data.items()):
        with detail_cols[i % 3]:
            st.markdown(f"**{key}**")
            st.write(str(value))
            
    st.markdown('</div>', unsafe_allow_html=True)

# 8. EXPORT GLOBAL
if not d_show.empty:
    st.sidebar.markdown("### Export Full Results")
    full_csv = d_show.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download All (CSV)", full_csv, "all_results.csv", "text/csv")
