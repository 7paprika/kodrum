import streamlit as st
import json
import math

# --- Page Configuration ---
st.set_page_config(page_title="KO Drum Rigorous Sizing", layout="wide")

# --- CSS Injection for Clean PDF Print (@media print) ---
st.markdown("""
<style>
@media print {
    /* Hide Sidebar */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    /* Hide specific inputs and buttons during print */
    .stTextArea, .stButton, .stDownloadButton, button {
        display: none !important;
    }
    /* Hide top header padding */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    /* Adjust main block width for A4 */
    .block-container {
        padding-top: 0rem !important;
        max-width: 100% !important;
    }
}
/* Table Styling */
table {
    width: 100%;
    border-collapse: collapse;
}
th, td {
    border: 1px solid #dddddd;
    text-align: left;
    padding: 8px;
}
th {
    background-color: #f2f2f2;
}
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
INPUT_KEYS = ['tag_no', 'rev_no', 'service', 'project', 'date_str', 
              'W_V', 'rho_V', 'mu_V', 'W_L', 'rho_L', 'D', 'H', 'D_p_um']

for key in INPUT_KEYS:
    if key not in st.session_state:
        if key == 'project': st.session_state[key] = ""
        elif key == 'date_str': st.session_state[key] = "2026-03-31"
        elif key == 'tag_no': st.session_state[key] = "V-101"
        elif key == 'rev_no': st.session_state[key] = "0"
        elif key == 'service': st.session_state[key] = "Flare KO Drum"
        elif key == 'W_V': st.session_state[key] = 2239.8
        elif key == 'rho_V': st.session_state[key] = 5.679
        elif key == 'mu_V': st.session_state[key] = 0.000009
        elif key == 'W_L': st.session_state[key] = 25360.4
        elif key == 'rho_L': st.session_state[key] = 824.5
        elif key == 'D': st.session_state[key] = 0.6
        elif key == 'H': st.session_state[key] = 1.53
        elif key == 'D_p_um': st.session_state[key] = 300.0

# --- Sidebar: Metadata & Secure JSON Management ---
st.sidebar.header("📝 Metadata & Setup")
st.session_state['tag_no'] = st.sidebar.text_input("Tag No.", value=st.session_state['tag_no'])
st.session_state['rev_no'] = st.sidebar.text_input("Revision", value=st.session_state['rev_no'])
st.session_state['project'] = st.sidebar.text_input("Project", value=st.session_state['project'])
st.session_state['date_str'] = st.sidebar.text_input("Date", value=st.session_state['date_str'])

st.sidebar.markdown("---")
st.sidebar.header("💾 Secure JSON Data Loader")
st.sidebar.caption("Paste JSON text below to bypass upload restrictions.")

json_input = st.sidebar.text_area("JSON Input Text", height=150)
if st.sidebar.button("Load JSON Data"):
    if json_input.strip():
        try:
            data = json.loads(json_input)
            for k, v in data.items():
                if k in st.session_state:
                    st.session_state[k] = v
            st.sidebar.success("✅ Data applied! Please interact with the app to refresh.")
        except json.JSONDecodeError:
            st.sidebar.error("❌ Invalid JSON format.")

# JSON Output Generator
data_to_save = {key: st.session_state[key] for key in INPUT_KEYS}
st.sidebar.text_area("Copy JSON to Save", value=json.dumps(data_to_save, indent=2), height=150)

# --- Core Calculations ---
W_V = st.session_state['W_V']
rho_V = st.session_state['rho_V']
mu_V = st.session_state['mu_V']
W_L = st.session_state['W_L']
rho_L = st.session_state['rho_L']
D = st.session_state['D']
H = st.session_state['H']
D_p = st.session_state['D_p_um'] / 1000000.0
g = 9.81

Q_V = W_V / (rho_V * 3600)
A = math.pi * (D**2) / 4
U_V = Q_V / A

U_T = 0.5
Re_final, C_D_final = 0, 0
for _ in range(10):
    Re_final = (D_p * U_T * rho_V) / mu_V
    C_D_final = (24 / Re_final) + (3 / math.sqrt(Re_final)) + 0.34 if Re_final > 0 else 0.34
    U_T = math.sqrt((4 * g * D_p * (rho_L - rho_V)) / (3 * rho_V * C_D_final))

status = "PASS" if U_V < U_T else "FAIL"

# --- Main Report Rendering ---
st.title("KO Drum Rigorous Sizing Report")
st.markdown(f"**Project:** {st.session_state['project']} &nbsp;&nbsp;|&nbsp;&nbsp; **Tag No:** {st.session_state['tag_no']} &nbsp;&nbsp;|&nbsp;&nbsp; **Date:** {st.session_state['date_str']} &nbsp;&nbsp;|&nbsp;&nbsp; **Rev:** {st.session_state['rev_no']}")
st.markdown("---")

# 1. Summary Table
st.header("1. Executive Summary")
summary_html = f"""
<table>
  <tr>
    <th>Parameter</th><th>Value</th><th>Parameter</th><th>Value</th>
  </tr>
  <tr>
    <td><b>Vessel Inner Diameter</b></td><td>{D:.3f} m</td>
    <td><b>Target Droplet Size</b></td><td>{st.session_state['D_p_um']} μm</td>
  </tr>
  <tr>
    <td><b>Actual Vapor Velocity ($U_v$)</b></td><td><b>{U_V:.4f} m/s</b></td>
    <td><b>Terminal Velocity ($U_T$)</b></td><td><b>{U_T:.4f} m/s</b></td>
  </tr>
  <tr>
    <td colspan="2"><b>Design Suitability ($U_v < U_T$)</b></td>
    <td colspan="2" style="color: {'green' if status=='PASS' else 'red'}; font-weight: bold;">{status}</td>
  </tr>
</table>
"""
st.markdown(summary_html, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 2. Detailed Calculations
st.header("2. Detailed Engineering Calculations")

# Section 2.1
st.markdown("### **2.1 Actual Vapor Velocity ($U_v$)**")
st.caption("Description: The actual upward superficial velocity of the vapor phase inside the vessel.")
st.latex(rf"Q_v = \frac{{W_v}}{{\rho_v \times 3600}} = \frac{{{W_V}}}{{{rho_V} \times 3600}} = {Q_V:.4f} \text{{ m}}^3\text{{/s}}")
st.latex(rf"A = \frac{{\pi D^2}}{{4}} = \frac{{\pi \times {D}^2}}{{4}} = {A:.4f} \text{{ m}}^2")
st.latex(rf"U_v = \frac{{Q_v}}{{A}} = \frac{{{Q_V:.4f}}}{{{A:.4f}}} = \mathbf{{{U_V:.4f} \text{{ m/s}}}}")
st.markdown("<hr style='margin: 1em 0; border: 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

# Section 2.2
st.markdown("### **2.2 Particle Reynolds Number ($Re$)**")
st.caption("Description: A dimensionless quantity indicating the flow regime of the droplet settling through the vapor phase.")
st.latex(rf"Re = \frac{{D_p \cdot U_T \cdot \rho_v}}{{\mu_v}} = \frac{{{D_p} \times {U_T:.4f} \times {rho_V}}}{{{mu_V:.6f}}} = \mathbf{{{Re_final:.2f}}}")
st.markdown("<hr style='margin: 1em 0; border: 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

# Section 2.3
st.markdown("### **2.3 Drag Coefficient ($C_D$)**")
st.caption("Description: The flow resistance coefficient applied to the droplet, evaluated using the intermediate law approximation (API Std 521).")
st.latex(rf"C_D = \frac{{24}}{{Re}} + \frac{{3}}{{\sqrt{{Re}}}} + 0.34 = \frac{{24}}{{{Re_final:.2f}}} + \frac{{3}}{{\sqrt{{{Re_final:.2f}}}}} + 0.34 = \mathbf{{{C_D_final:.4f}}}")
st.markdown("<hr style='margin: 1em 0; border: 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

# Section 2.4
st.markdown("### **2.4 Terminal Settling Velocity ($U_T$)**")
st.caption("Description: The maximum allowable velocity for the target droplet to successfully separate and fall against the upward vapor flow.")
st.latex(rf"U_T = \sqrt{{\frac{{4 g D_p (\rho_L - \rho_v)}}{{3 \rho_v C_D}}}} = \sqrt{{\frac{{4 \times 9.81 \times {D_p} \times ({rho_L} - {rho_V})}}{{3 \times {rho_V} \times {C_D_final:.4f}}}}} = \mathbf{{{U_T:.4f} \text{{ m/s}}}}")

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Note: Variables reflect the final iteration step satisfying the convergence criteria for $U_T$ and $C_D$.")
