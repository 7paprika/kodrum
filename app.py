import streamlit as st
import json
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from fpdf import FPDF
import base64

# --- Page Configuration ---
st.set_page_config(page_title="KO Drum Sizing Calc", layout="wide")

# --- Piping Database (Simplified for Main Sizes, Sch 40/80) ---
# Format: (Size, Schedule) : Inner Diameter in meters
PIPE_DB = {
    ('1/2"', 'Sch 40'): 0.0158, ('1/2"', 'Sch 80'): 0.0139,
    ('1"', 'Sch 40'): 0.0266, ('1"', 'Sch 80'): 0.0243,
    ('2"', 'Sch 40'): 0.0525, ('2"', 'Sch 80'): 0.0493,
    ('3"', 'Sch 40'): 0.0779, ('3"', 'Sch 80'): 0.0737,
    ('4"', 'Sch 40'): 0.1023, ('4"', 'Sch 80'): 0.0972,
    ('6"', 'Sch 40'): 0.1541, ('6"', 'Sch 80'): 0.1463,
    ('8"', 'Sch 40'): 0.2027, ('8"', 'Sch 80'): 0.1937,
    ('10"', 'Sch 40'): 0.2545, ('10"', 'Sch 80'): 0.2429,
    ('12"', 'Sch 40'): 0.3048, ('12"', 'Sch 80'): 0.2889,
    ('16"', 'Sch 40'): 0.3810, ('16"', 'Sch 80'): 0.3635,
    ('20"', 'Sch 40'): 0.4778, ('20"', 'Sch 80'): 0.4556,
    ('24"', 'Sch 40'): 0.5746, ('24"', 'Sch 80'): 0.5477,
}

pipe_sizes = sorted(list(set([k[0] for k in PIPE_DB.keys()])))
pipe_schs = sorted(list(set([k[1] for k in PIPE_DB.keys()])))

# --- Sidebar: Metadata & Data Management ---
st.sidebar.header("📝 Project Metadata")
col1, col2 = st.sidebar.columns(2)
tag_no = col1.text_input("Tag No.", value="V-101")
rev_no = col2.text_input("Revision", value="0")
service = st.sidebar.text_input("Service", value="Flare KO Drum")
project = st.sidebar.text_input("Project", value="")
date_str = st.sidebar.text_input("Date", value="2026-03-31")

st.sidebar.markdown("---")
st.sidebar.header("💾 Data Management")

# Define all input keys for JSON
INPUT_KEYS = ['W_V', 'rho_V', 'mu_V', 'W_L', 'rho_L', 'D', 'H', 'D_p', 'inlet_size', 'inlet_sch', 'vout_size', 'vout_sch', 'lout_size', 'lout_sch']

# JSON Download
def download_json():
    data_to_save = {key: st.session_state[key] for key in INPUT_KEYS if key in st.session_state}
    json_str = json.dumps(data_to_save, indent=4)
    b64 = base64.b64encode(json_str.encode()).decode()
    href = f'<a href="data:file/json;base64,{b64}" download="kodrum_data.json">Download Input JSON</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

# Main Title
st.title("KO Drum Rigorous Sizing & Hydraulics Calculator")
st.markdown("Reference: API Standard 521 (Section 5.4.2) / KOSHA Guide")

# --- Layout: Inputs ---
st.header("1. Input Parameters")

col_f, col_e, col_n = st.columns(3)

with col_f:
    st.subheader("Fluid Properties")
    W_V = st.number_input("Vapor Flow Rate (kg/hr)", value=2239.8, key='W_V')
    rho_V = st.number_input("Vapor Density (kg/m3)", value=5.679, format="%.3f", key='rho_V')
    mu_V = st.number_input("Vapor Viscosity (kg/m·s)", value=0.000009, format="%.6f", key='mu_V')
    W_L = st.number_input("Liquid Flow Rate (kg/hr)", value=25360.4, key='W_L')
    rho_L = st.number_input("Liquid Density (kg/m3)", value=824.5, key='rho_L')

with col_e:
    st.subheader("Equipment Data")
    D = st.number_input("Vessel Inner Diameter (m)", value=0.6, key='D')
    H = st.number_input("Vessel Tangent Height (m)", value=1.53, key='H')
    
    st.markdown("---")
    st.subheader("Particle Parameter")
    D_p_um = st.number_input("Target Droplet Size (μm)", value=300.0, step=50.0)
    D_p = D_p_um / 1000000.0 # Convert to meters
    st.session_state['D_p'] = D_p
    
    with st.expander("ℹ️ Guide: Target Particle Size"):
        st.write("""
        * **Flare Header KO Drum:** 300 ~ 600 μm
        * **Compressor Suction Drum:** 100 ~ 300 μm (To prevent impeller damage)
        * **Fuel Gas KO Drum:** 10 ~ 50 μm (Requires demister/mesh pad)
        """)

with col_n:
    st.subheader("Nozzle Configuration")
    i_sz = st.selectbox("Inlet Size", pipe_sizes, index=pipe_sizes.index('6"'), key='inlet_size')
    i_sc = st.selectbox("Inlet Sch", pipe_schs, index=pipe_schs.index('Sch 40'), key='inlet_sch')
    
    vo_sz = st.selectbox("Vapor Outlet Size", pipe_sizes, index=pipe_sizes.index('4"'), key='vout_size')
    vo_sc = st.selectbox("Vapor Outlet Sch", pipe_schs, index=pipe_schs.index('Sch 40'), key='vout_sch')
    
    lo_sz = st.selectbox("Liquid Outlet Size", pipe_sizes, index=pipe_sizes.index('2"'), key='lout_size')
    lo_sc = st.selectbox("Liquid Outlet Sch", pipe_schs, index=pipe_schs.index('Sch 40'), key='lout_sch')

download_json() # Sidebar JSON download hook

st.markdown("---")

# --- Calculations ---
g = 9.81
Q_V = W_V / (rho_V * 3600)
Q_L = W_L / (rho_L * 3600)
A_vessel = math.pi * (D**2) / 4
U_V = Q_V / A_vessel

# Iteration for C_D and U_T
U_T = 0.5 # Initial guess
for _ in range(5): # 5 iterations ensure convergence
    Re = (D_p * U_T * rho_V) / mu_V
    if Re > 0:
        C_D = (24 / Re) + (3 / math.sqrt(Re)) + 0.34
    else:
        C_D = 0.34
    U_T = math.sqrt((4 * g * D_p * (rho_L - rho_V)) / (3 * rho_V * C_D))

status = "PASS" if U_V < U_T else "FAIL"

# Nozzle Calcs
def get_id(sz, sc):
    return PIPE_DB.get((sz, sc), 0.1) # Fallback 0.1m

ID_in = get_id(i_sz, i_sc)
ID_vout = get_id(vo_sz, vo_sc)
ID_lout = get_id(lo_sz, lo_sc)

A_in = math.pi * (ID_in**2) / 4
rho_m = (W_V + W_L) / ((Q_V + Q_L)*3600)
V_in = (Q_V + Q_L) / A_in
Mom_in = rho_m * (V_in**2)

A_vout = math.pi * (ID_vout**2) / 4
V_vout = Q_V / A_vout
Mom_vout = rho_V * (V_vout**2)

A_lout = math.pi * (ID_lout**2) / 4
V_lout = Q_L / A_lout

# --- Output Presentation ---
st.header("2. Calculation Results & Hydraulics")

col_res1, col_res2 = st.columns(2)

with col_res1:
    st.subheader("Terminal Velocity Evaluation")
    st.latex(r"U_v = \frac{Q_v}{A_{vessel}} \quad \text{(Ref: Mass Conservation)}")
    st.metric("Actual Vapor Vel (U_v)", f"{U_V:.4f} m/s")
    
    st.latex(r"C_D = \frac{24}{Re} + \frac{3}{\sqrt{Re}} + 0.34 \quad \text{(Ref: API 521)}")
    st.latex(r"U_T = \sqrt{\frac{4 g D_p (\rho_L - \rho_v)}{3 \rho_v C_D}} \quad \text{(Ref: API 521 / Stokes)}")
    st.metric("Terminal Velocity (U_T)", f"{U_T:.4f} m/s")
    
    if status == "PASS":
        st.success(f"Result: {status} (U_v < U_T)")
    else:
        st.error(f"Result: {status} (U_v > U_T) - Carry-over risk!")

with col_res2:
    st.subheader("Nozzle Hydraulics")
    st.latex(r"Momentum = \rho V^2")
    st.markdown(f"**Inlet Nozzle ({i_sz} {i_sc}):**")
    st.write(f"- Velocity: {V_in:.2f} m/s")
    st.write(f"- Momentum: {Mom_in:.1f} kg/(m·s²)")
    if Mom_in > 1500:
        st.warning("High Inlet Momentum (>1500). Inlet Baffle is strictly required.")
        
    st.markdown(f"**Vapor Outlet ({vo_sz} {vo_sc}):**")
    st.write(f"- Velocity: {V_vout:.2f} m/s")
    st.write(f"- Momentum: {Mom_vout:.1f} kg/(m·s²)")
    
    st.markdown(f"**Liquid Outlet ({lo_sz} {lo_sc}):**")
    st.write(f"- Velocity: {V_lout:.2f} m/s")
    if V_lout > 1.5:
        st.error(f"CRITICAL: Liquid velocity ({V_lout:.2f} m/s) exceeds 1.5 m/s. Severe pump cavitation risk. NPSHa calculation is mandatory.")

st.markdown("---")

# --- Graphics: Vessel Diagram ---
st.header("3. Vessel Dimension Graphic")
fig, ax = plt.subplots(figsize=(4, 6))

# Draw Vessel Body
vessel = patches.Rectangle((0, 0), D, H, linewidth=2, edgecolor='black', facecolor='none')
ax.add_patch(vessel)

# Draw Heads (Elliptical approx)
head_bottom = patches.Arc((D/2, 0), D, D/2, angle=0, theta1=180, theta2=360, linewidth=2, edgecolor='black')
head_top = patches.Arc((D/2, H), D, D/2, angle=0, theta1=0, theta2=180, linewidth=2, edgecolor='black')
ax.add_patch(head_bottom)
ax.add_patch(head_top)

# Nozzle indicators (Simplified)
ax.plot([-0.1, 0], [H*0.75, H*0.75], 'k-', lw=2) # Inlet
ax.text(-0.3, H*0.75, f'Inlet\n{i_sz}', va='center')

ax.plot([D/2, D/2], [H+D/4, H+D/4+0.1], 'k-', lw=2) # Top
ax.text(D/2+0.05, H+D/4+0.1, f'Vapor\n{vo_sz}', va='bottom')

ax.plot([D/2, D/2], [-D/4, -D/4-0.1], 'k-', lw=2) # Bottom
ax.text(D/2+0.05, -D/4-0.1, f'Liquid\n{lo_sz}', va='top')

# Labels
ax.text(D/2, H/2, f'ID = {D} m\nH = {H} m', ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8))

ax.set_xlim(-D, 2*D)
ax.set_ylim(-D, H+D)
ax.axis('off')

st.pyplot(fig)

# --- PDF Report Generation ---
st.header("4. Generate Report")

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "KO Drum Sizing & Hydraulics Report", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Project: {project} | Tag: {tag_no} | Service: {service}", ln=True)
    pdf.cell(0, 10, f"Date: {date_str} | Revision: {rev_no}", ln=True)
    pdf.line(10, 35, 200, 35)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Separation Evaluation", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Target Droplet Size: {D_p_um} um", ln=True)
    pdf.cell(0, 8, f"Actual Vapor Velocity (U_v): {U_V:.4f} m/s", ln=True)
    pdf.cell(0, 8, f"Terminal Velocity (U_T): {U_T:.4f} m/s", ln=True)
    pdf.cell(0, 8, f"Evaluation Result: {status}", ln=True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. Nozzle Hydraulics", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Inlet ({i_sz} {i_sc}): Vel = {V_in:.2f} m/s, Mom = {Mom_in:.1f} kg/m.s2", ln=True)
    pdf.cell(0, 8, f"Vapor Out ({vo_sz} {vo_sc}): Vel = {V_vout:.2f} m/s", ln=True)
    pdf.cell(0, 8, f"Liquid Out ({lo_sz} {lo_sc}): Vel = {V_lout:.2f} m/s", ln=True)
    
    if V_lout > 1.5:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 8, "WARNING: Liquid velocity exceeds 1.5 m/s. Check Pump NPSHa.", ln=True)
        pdf.set_text_color(0, 0, 0)
        
    return pdf.output(dest='S').encode('latin-1')

pdf_bytes = create_pdf()
st.download_button(label="📄 Download PDF Report", data=pdf_bytes, file_name=f"{tag_no}_Report.pdf", mime="application/pdf")
