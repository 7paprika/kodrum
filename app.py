import streamlit as st
import json
import math
import base64

# --- Page Configuration ---
st.set_page_config(page_title="KO Drum Rigorous Sizing Calc", layout="wide")

# --- Session State Initialization ---
INPUT_KEYS = ['tag_no', 'rev_no', 'service', 'project', 'date_str', 
              'W_V', 'rho_V', 'mu_V', 'W_L', 'rho_L', 'D', 'H', 'D_p_um']

for key in INPUT_KEYS:
    if key not in st.session_state:
        # Default values
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

# --- Sidebar: Metadata & JSON Management ---
st.sidebar.header("📝 Document Metadata")
st.session_state['tag_no'] = st.sidebar.text_input("Tag No.", value=st.session_state['tag_no'])
st.session_state['rev_no'] = st.sidebar.text_input("Revision", value=st.session_state['rev_no'])
st.session_state['service'] = st.sidebar.text_input("Service", value=st.session_state['service'])
st.session_state['project'] = st.sidebar.text_input("Project", value=st.session_state['project'])
st.session_state['date_str'] = st.sidebar.text_input("Date", value=st.session_state['date_str'])

st.sidebar.markdown("---")
st.sidebar.header("💾 Data Management (JSON)")

# Load JSON
uploaded_file = st.sidebar.file_uploader("Upload JSON File", type=['json'])
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        for k, v in data.items():
            if k in st.session_state:
                st.session_state[k] = v
        st.sidebar.success("Data loaded successfully! Please refresh or interact to apply.")
    except Exception as e:
        st.sidebar.error(f"Error loading JSON: {e}")

# Save JSON
data_to_save = {key: st.session_state[key] for key in INPUT_KEYS}
json_str = json.dumps(data_to_save, indent=4)
b64 = base64.b64encode(json_str.encode()).decode()
href = f'<a href="data:file/json;base64,{b64}" download="{st.session_state["tag_no"]}_kodrum.json" style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #4CAF50; text-decoration: none; border-radius: 4px;">📥 Download Input JSON</a>'
st.sidebar.markdown(href, unsafe_allow_html=True)

# --- Main Report Header ---
st.title("Liquid-Vapor Separation: Rigorous Sizing Calculation")
st.markdown(f"**Project:** {st.session_state['project']} | **Tag No:** {st.session_state['tag_no']} | **Service:** {st.session_state['service']}")
st.markdown(f"**Date:** {st.session_state['date_str']} | **Rev:** {st.session_state['rev_no']}")
st.markdown("---")

# --- Layout: Inputs ---
st.header("1. Input Parameters")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Fluid Properties")
    st.session_state['W_V'] = st.number_input("Vapor Mass Flow, W_v (kg/hr)", value=st.session_state['W_V'])
    st.session_state['rho_V'] = st.number_input("Vapor Density, ρ_v (kg/m3)", value=st.session_state['rho_V'], format="%.4f")
    st.session_state['mu_V'] = st.number_input("Vapor Viscosity, μ_v (kg/m·s)", value=st.session_state['mu_V'], format="%.6f")
    st.session_state['W_L'] = st.number_input("Liquid Mass Flow, W_L (kg/hr)", value=st.session_state['W_L'])
    st.session_state['rho_L'] = st.number_input("Liquid Density, ρ_L (kg/m3)", value=st.session_state['rho_L'], format="%.2f")

with col2:
    st.subheader("Equipment & Droplet Data")
    st.session_state['D'] = st.number_input("Vessel Inner Diameter, D (m)", value=st.session_state['D'], format="%.3f")
    st.session_state['H'] = st.number_input("Vessel Tangent Height, H (m)", value=st.session_state['H'], format="%.3f")
    st.session_state['D_p_um'] = st.number_input("Target Droplet Size, D_p (μm)", value=st.session_state['D_p_um'], step=50.0)
    
    with st.expander("ℹ️ Particle Size Guide"):
        st.markdown("""
        - **300 ~ 600 μm:** General Flare Header KO Drum (API 521).
        - **100 ~ 300 μm:** Compressor Suction Drum (Prevents impeller erosion).
        - **10 ~ 50 μm:** Fuel Gas KO Drum (Requires internal mesh pad / demister).
        """)

st.markdown("---")

# --- Calculations & Iteration ---
W_V = st.session_state['W_V']
rho_V = st.session_state['rho_V']
mu_V = st.session_state['mu_V']
W_L = st.session_state['W_L']
rho_L = st.session_state['rho_L']
D = st.session_state['D']
H = st.session_state['H']
D_p_um = st.session_state['D_p_um']

D_p = D_p_um / 1000000.0  # um to m
g = 9.81

# 1. Volumetric Flow
Q_V = W_V / (rho_V * 3600)
Q_L = W_L / (rho_L * 3600)

# 2. Area and Actual Velocity
A = math.pi * (D**2) / 4
U_V = Q_V / A

# 3. Iteration for C_D and U_T (Silent background calculation)
U_T = 0.5 # Initial assumption
Re_final = 0
C_D_final = 0

for _ in range(10): # 10 iterations for strict convergence
    Re_final = (D_p * U_T * rho_V) / mu_V
    if Re_final > 0:
        C_D_final = (24 / Re_final) + (3 / math.sqrt(Re_final)) + 0.34
    else:
        C_D_final = 0.34
    U_T = math.sqrt((4 * g * D_p * (rho_L - rho_V)) / (3 * rho_V * C_D_final))

status = "PASS (Suitable Design)" if U_V < U_T else "FAIL (Risk of Liquid Carry-over)"
status_color = "green" if U_V < U_T else "red"

# --- Output Presentation ---
st.header("2. Separation Hydraulics Result")

st.markdown("#### 2.1 Volumetric Flow & Actual Velocity")

# Q_V
st.latex(rf"Q_v = \frac{{W_v}}{{\rho_v \times 3600}} = \frac{{{W_V}}}{{{rho_V} \times 3600}} = {Q_V:.4f} \text{{ m}}^3\text{{/s}}")
st.caption("Description: Actual volumetric flow rate of the vapor phase.")

# Area
st.latex(rf"A = \frac{{\pi D^2}}{{4}} = \frac{{\pi \times {D}^2}}{{4}} = {A:.4f} \text{{ m}}^2")
st.caption("Description: Internal cross-sectional area of the vertical vessel.")

# U_V
st.latex(rf"U_v = \frac{{Q_v}}{{A}} = \frac{{{Q_V:.4f}}}{{{A:.4f}}} = {U_V:.4f} \text{{ m/s}}")
st.caption("Description: Actual upward velocity of the vapor inside the drum.")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 2.2 Terminal Settling Velocity (Rigorous Iteration Method)")
st.info("Note: The values below represent the final converged state after iterative calculation.")

# Reynolds
st.latex(rf"Re = \frac{{D_p \cdot U_T \cdot \rho_v}}{{\mu_v}} = \frac{{{D_p} \times {U_T:.4f} \times {rho_V}}}{{{mu_V:.6f}}} = {Re_final:.2f}")
st.caption("Description: Particle Reynolds number at final terminal velocity.")

# Drag Coefficient
st.latex(rf"C_D = \frac{{24}}{{Re}} + \frac{{3}}{{\sqrt{{Re}}}} + 0.34 = \frac{{24}}{{{Re_final:.2f}}} + \frac{{3}}{{\sqrt{{{Re_final:.2f}}}}} + 0.34 = {C_D_final:.4f}")
st.caption("Description: Drag coefficient based on Intermediate Law (API Std 521).")

# U_T
st.latex(rf"U_T = \sqrt{{\frac{{4 g D_p (\rho_L - \rho_v)}}{{3 \rho_v C_D}}}} = \sqrt{{\frac{{4 \times 9.81 \times {D_p} \times ({rho_L} - {rho_V})}}{{3 \times {rho_V} \times {C_D_final:.4f}}}}} = {U_T:.4f} \text{{ m/s}}")
st.caption("Description: Terminal settling velocity required for droplets to separate from vapor flow (API Std 521).")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 2.3 Final Evaluation")
st.latex(rf"\text{{Evaluation Check: }} U_v \text{{ (}}{U_V:.4f}\text{{ m/s) }} < U_T \text{{ (}}{U_T:.4f}\text{{ m/s)}}")
st.markdown(f"<h3 style='color: {status_color}; text-align: center;'>Result: {status}</h3>", unsafe_allow_html=True)
