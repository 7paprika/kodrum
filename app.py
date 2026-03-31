import streamlit as st
import json
import math
import base64
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="KO Drum Rating App", layout="wide")

# --- Session State Initialization ---
INPUT_KEYS = ['tag_no', 'rev_no', 'service', 'project', 'date_str', 
              'W_V', 'rho_V', 'mu_V', 'W_L', 'rho_L', 'D', 'H', 'D_p_um']

for key in INPUT_KEYS:
    if key not in st.session_state:
        if key == 'project': st.session_state[key] = "SK Trichem Project"
        elif key == 'date_str': st.session_state[key] = datetime.now().strftime("%Y-%m-%d")
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

# --- Sidebar: Secure JSON Data Loader ---
st.sidebar.header("💾 Secure JSON Data Loader")
json_input = st.sidebar.text_area("JSON Input Text", height=150)
if st.sidebar.button("Load JSON Data"):
    if json_input.strip():
        try:
            data = json.loads(json_input)
            for k, v in data.items():
                if k in st.session_state:
                    st.session_state[k] = v
            st.sidebar.success("✅ Data applied! Please interact to refresh.")
        except json.JSONDecodeError:
            st.sidebar.error("❌ Invalid JSON format.")

data_to_save = {key: st.session_state[key] for key in INPUT_KEYS}
st.sidebar.text_area("Copy JSON to Save", value=json.dumps(data_to_save, indent=2), height=150)
st.sidebar.markdown("---")

# --- UI: Metadata & Inputs ---
st.title("KO Drum Rating Report Generator")
st.markdown("Review the calculations, edit the Engineering Conclusion, and download the HTML report.")
st.markdown("---")

st.header("📝 1. Document Metadata")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
st.session_state['project'] = col_m1.text_input("Project", value=st.session_state['project'])
st.session_state['tag_no'] = col_m2.text_input("Tag No.", value=st.session_state['tag_no'])
st.session_state['service'] = col_m3.text_input("Service", value=st.session_state['service'])
st.session_state['rev_no'] = col_m4.text_input("Revision", value=st.session_state['rev_no'])

st.header("⚙️ 2. Process & Equipment Input Data")
col_i1, col_i2 = st.columns(2)

with col_i1:
    st.subheader("Fluid Properties")
    st.session_state['W_V'] = st.number_input("Vapor Mass Flow, W_v (kg/hr)", value=st.session_state['W_V'], step=100.0)
    st.session_state['rho_V'] = st.number_input("Vapor Density, ρ_v (kg/m³)", value=st.session_state['rho_V'], format="%.4f")
    st.session_state['mu_V'] = st.number_input("Vapor Viscosity, μ_v (kg/m·s)", value=st.session_state['mu_V'], format="%.6f")
    st.session_state['W_L'] = st.number_input("Liquid Mass Flow, W_L (kg/hr)", value=st.session_state['W_L'], step=1000.0)
    st.session_state['rho_L'] = st.number_input("Liquid Density, ρ_L (kg/m³)", value=st.session_state['rho_L'], format="%.2f")

with col_i2:
    st.subheader("Equipment & Droplet Specs")
    st.session_state['D'] = st.number_input("Vessel Inner Dia., D (m)", value=st.session_state['D'], format="%.3f")
    st.session_state['H'] = st.number_input("Vessel Tan. Height, H (m)", value=st.session_state['H'], format="%.3f")
    st.session_state['D_p_um'] = st.number_input("Target Droplet, D_p (μm)", value=st.session_state['D_p_um'], step=50.0)

# --- Calculation Engine ---
W_V = st.session_state['W_V']
rho_V = st.session_state['rho_V']
mu_V = st.session_state['mu_V']
W_L = st.session_state['W_L']
rho_L = st.session_state['rho_L']
D = st.session_state['D']
H = st.session_state['H']
D_p_um = st.session_state['D_p_um']
tag_no = st.session_state['tag_no']
project = st.session_state['project']
service = st.session_state['service']
rev_no = st.session_state['rev_no']
current_date = st.session_state['date_str']

D_p = D_p_um / 1000000.0
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

status = "PASS (Suitable)" if U_V < U_T else "FAIL (Carry-over Risk)"
status_color = "green" if U_V < U_T else "red"

st.markdown("---")

# --- Web Screen Preview ---
st.header("📊 3. Output Summary & Formulas (Web Preview)")

st.markdown("**Output Summary Table**")
# Applying inline styling to force 25% column width and nowrap on the web preview
st.markdown(f"""
<table style="width:100%; table-layout:fixed; border-collapse:collapse; text-align:left;">
  <tr>
    <th style="width:25%; border:1px solid #ccc; padding:8px; background-color:#f2f2f2; white-space:nowrap;">Vapor Vol. Flow ($Q_v$)</th>
    <td style="width:25%; border:1px solid #ccc; padding:8px; white-space:nowrap;">{Q_V:.4f} m³/s</td>
    <th style="width:25%; border:1px solid #ccc; padding:8px; background-color:#f2f2f2; white-space:nowrap;">Vapor Velocity ($U_v$)</th>
    <td style="width:25%; border:1px solid #ccc; padding:8px; white-space:nowrap;"><b>{U_V:.4f} m/s</b></td>
  </tr>
  <tr>
    <th style="border:1px solid #ccc; padding:8px; background-color:#f2f2f2; white-space:nowrap;">Vessel Cross Area ($A$)</th>
    <td style="border:1px solid #ccc; padding:8px; white-space:nowrap;">{A:.4f} m²</td>
    <th style="border:1px solid #ccc; padding:8px; background-color:#f2f2f2; white-space:nowrap;">Terminal Velocity ($U_T$)</th>
    <td style="border:1px solid #ccc; padding:8px; white-space:nowrap;"><b>{U_T:.4f} m/s</b></td>
  </tr>
  <tr>
    <th style="border:1px solid #ccc; padding:8px; background-color:#f2f2f2; white-space:nowrap;">Drag Coefficient ($C_D$)</th>
    <td style="border:1px solid #ccc; padding:8px; white-space:nowrap;">{C_D_final:.4f}</td>
    <th style="border:1px solid #ccc; padding:8px; background-color:#f2f2f2; white-space:nowrap;">Design Suitability</th>
    <td style="border:1px solid #ccc; padding:8px; white-space:nowrap; color:{status_color}; font-weight:bold;">{status}</td>
  </tr>
</table>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("**Detailed Calculation Formulas**")
st.latex(rf"U_v = \frac{{Q_v}}{{A}} = \frac{{{Q_V:.4f}}}{{{A:.4f}}} = {U_V:.4f} \text{{ m/s}}")
st.latex(rf"Re = \frac{{D_p \cdot U_T \cdot \rho_v}}{{\mu_v}} = {Re_final:.2f}")
st.latex(rf"C_D = \frac{{24}}{{Re}} + \frac{{3}}{{\sqrt{{Re}}}} + 0.34 = {C_D_final:.4f}")
st.latex(rf"U_T = \sqrt{{\frac{{4 g D_p (\rho_L - \rho_v)}}{{3 \rho_v C_D}}}} = {U_T:.4f} \text{{ m/s}}")

st.markdown("---")

# --- Editable Conclusion ---
st.header("✍️ 4. Engineering Conclusion")
default_conclusion = f"""Based on the rigorous iterative hydraulic calculations utilizing the Intermediate Drag Law specified in API Standard 521, the actual upward vapor velocity (U_v = {U_V:.4f} m/s) is strictly maintained below the terminal settling velocity (U_T = {U_T:.4f} m/s) required for the target droplet size of {D_p_um} μm.

Therefore, the existing vessel dimension (D = {D:.3f} m) provides adequate cross-sectional area to ensure the successful disengagement of liquid droplets from the vapor phase, meeting the KOSHA PSM process safety design intent under the given operating conditions."""

user_conclusion = st.text_area("Edit Conclusion:", value=default_conclusion, height=150)
user_conclusion_html = user_conclusion.replace('\n', '<br>')

# --- HTML Report Generation ---
def generate_html_report():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{tag_no} KO Drum Rating Report</title>
        <script>
        MathJax = {{ tex: {{ inlineMath: [['\\\\(', '\\\\)']] }} }};
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <style>
            body {{ font-family: 'Arial', sans-serif; font-size: 12px; color: #333; margin: 0; padding: 0; background-color: #fff; }}
            .page-container {{ width: 190mm; margin: 10mm auto; padding: 10mm; border: 2px solid #000; box-sizing: border-box; }}
            h1, h2, h3 {{ color: #000; margin-top: 15px; margin-bottom: 5px; }}
            h1 {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; }}
            
            /* Header Table (Maintains proportions) */
            .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            .header-table th, .header-table td {{ border: 1px solid #000; padding: 6px; text-align: left; }}
            
            /* Data Tables (Strictly 25% per column, no wrap) */
            .data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; table-layout: fixed; }}
            .data-table th, .data-table td {{ border: 1px solid #000; padding: 6px; text-align: left; width: 25%; white-space: nowrap; overflow: hidden; }}
            .data-table th {{ background-color: #f2f2f2; font-weight: bold; }}
            
            .description {{ font-size: 11px; color: #555; font-style: italic; margin-bottom: 15px; }}
            .math-block {{ margin: 10px 0; font-size: 13px; }}
            .conclusion {{ background-color: #f9f9f9; padding: 10px; border: 1px dashed #333; line-height: 1.5; }}
            @media print {{
                body {{ background-color: #fff; }}
                .page-container {{ border: 2px solid #000; margin: 0; padding: 5mm; width: 100%; box-shadow: none; }}
                .nobreak {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="page-container">
            <table class="header-table">
                <tr>
                    <td rowspan="3" style="width: 20%; text-align: center; vertical-align: middle;">&nbsp;</td>
                    <td rowspan="3" style="width: 40%; text-align: center; vertical-align: middle; font-size: 18px; font-weight: bold;">
                        KO Drum Rating Report
                    </td>
                    <th style="width: 15%; background-color: #f2f2f2;">Project</th>
                    <td>{project}</td>
                </tr>
                <tr>
                    <th style="background-color: #f2f2f2;">Tag No.</th>
                    <td>{tag_no}</td>
                </tr>
                <tr>
                    <th style="background-color: #f2f2f2;">Date / Rev.</th>
                    <td>{current_date} / Rev.{rev_no}</td>
                </tr>
                <tr>
                    <th colspan="2" style="background-color: #f2f2f2;">Service</th>
                    <td colspan="2">{service}</td>
                </tr>
            </table>

            <h2>1. Input Data</h2>
            <table class="data-table">
                <tr><th colspan="2" style="text-align:center;">Fluid Properties</th><th colspan="2" style="text-align:center;">Equipment & Droplet Data</th></tr>
                <tr><th>Vapor Mass Flow (\\(W_v\\))</th><td>{W_V:,.1f} kg/hr</td><th>Vessel Inner Dia. (\\(D\\))</th><td>{D:.3f} m</td></tr>
                <tr><th>Vapor Density (\\(\\rho_v\\))</th><td>{rho_V:.4f} kg/m³</td><th>Vessel Tan. Height (\\(H\\))</th><td>{H:.3f} m</td></tr>
                <tr><th>Vapor Viscosity (\\(\\mu_v\\))</th><td>{mu_V:.6f} kg/m·s</td><th>Target Droplet (\\(D_p\\))</th><td>{D_p_um} μm</td></tr>
                <tr><th>Liquid Mass Flow (\\(W_L\\))</th><td>{W_L:,.1f} kg/hr</td><th colspan="2" style="background-color:#fff;"></th></tr>
                <tr><th>Liquid Density (\\(\\rho_L\\))</th><td>{rho_L:.2f} kg/m³</td><th colspan="2" style="background-color:#fff;"></th></tr>
            </table>

            <h2>2. Output Summary</h2>
            <table class="data-table">
                <tr><th>Vapor Vol. Flow (\\(Q_v\\))</th><td>{Q_V:.4f} m³/s</td><th>Vapor Velocity (\\(U_v\\))</th><td><b>{U_V:.4f} m/s</b></td></tr>
                <tr><th>Vessel Cross Area (\\(A\\))</th><td>{A:.4f} m²</td><th>Terminal Velocity (\\(U_T\\))</th><td><b>{U_T:.4f} m/s</b></td></tr>
                <tr><th>Drag Coefficient (\\(C_D\\))</th><td>{C_D_final:.4f}</td><th>Design Suitability</th><td style="color:{status_color}; font-weight:bold;">{status}</td></tr>
            </table>

            <div class="nobreak">
                <h2>3. Detailed Calculation & Formulas</h2>
                <h3>3.1 Actual Vapor Velocity (\\(U_v\\))</h3>
                <div class="description">Ref: Mass Conservation & Vessel Geometry</div>
                <div class="math-block">
                    \\[ U_v = \\frac{{Q_v}}{{A}} = \\frac{{\\frac{{W_v}}{{\\rho_v \\times 3600}}}}{{\\frac{{\\pi D^2}}{{4}}}} = \\frac{{\\frac{{{W_V}}}{{{rho_V} \\times 3600}}}}{{\\frac{{\\pi ({D})^2}}{{4}}}} = \\mathbf{{{U_V:.4f} \\text{{ m/s}}}} \\]
                </div>
            </div>

            <div class="nobreak">
                <h3>3.2 Final Drag Coefficient (\\(C_D\\))</h3>
                <div class="description">Ref: Intermediate Drag Law (API Std 521). Calculated via iterative convergence based on Particle Reynolds Number (\\(Re\\)).</div>
                <div class="math-block">
                    \\[ Re = \\frac{{D_p \\cdot U_T \\cdot \\rho_v}}{{\\mu_v}} = \\frac{{{D_p} \\times {U_T:.4f} \\times {rho_V}}}{{{mu_V:.6f}}} = {Re_final:.2f} \\]
                </div>
                <div class="math-block">
                    \
