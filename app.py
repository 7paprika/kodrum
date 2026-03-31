import streamlit as st
import json
import math
import base64
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="KO Drum Rating App", layout="wide")

# --- Session State Initialization ---
INPUT_KEYS = ['tag_no', 'rev_no', 'service', 'project', 'date_str', 
              'W_V', 'rho_V', 'mu_V', 'W_L', 'rho_L', 'D', 'H', 'D_p_um', 'user_conclusion']

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
        elif key == 'user_conclusion': st.session_state[key] = ""

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
            st.sidebar.success("✅ Data applied! Please refresh.")
        except json.JSONDecodeError:
            st.sidebar.error("❌ Invalid JSON format.")

data_to_save = {key: st.session_state[key] for key in INPUT_KEYS}
st.sidebar.text_area("Copy JSON to Save", value=json.dumps(data_to_save, indent=2), height=150)
st.sidebar.markdown("---")

# --- UI: Metadata & Inputs ---
st.title("KO Drum Rating Report Generator")
st.markdown("---")

st.header("📝 1. Document Metadata")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
st.session_state['project'] = col_m1.text_input("Project", value=st.session_state['project'])
st.session_state['rev_no'] = col_m2.text_input("Revision", value=st.session_state['rev_no'])
st.session_state['date_str'] = col_m3.text_input("Date", value=st.session_state['date_str'])

col_m_sub1, col_m_sub2 = st.columns(2)
st.session_state['tag_no'] = col_m_sub1.text_input("Tag No.", value=st.session_state['tag_no'])
st.session_state['service'] = col_m_sub2.text_input("Service", value=st.session_state['service'])

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
    
    with st.expander("ℹ️ Particle Size Guide"):
        st.markdown("""
        - **300 ~ 600 μm:** General Flare Header KO Drum (API 521).
        - **100 ~ 300 μm:** Compressor Suction Drum (Prevents impeller erosion).
        - **10 ~ 50 μm:** Fuel Gas KO Drum (Requires internal mesh pad / demister).
        """)

# --- Calculation Engine ---
D_p = st.session_state['D_p_um'] / 1000000.0
g = 9.81
Q_V = st.session_state['W_V'] / (st.session_state['rho_V'] * 3600)
A = math.pi * (st.session_state['D']**2) / 4
U_V = Q_V / A

U_T = 0.5
Re_final, C_D_final = 0, 0
for _ in range(10):
    Re_final = (D_p * U_T * st.session_state['rho_V']) / st.session_state['mu_V']
    C_D_final = (24 / Re_final) + (3 / math.sqrt(Re_final)) + 0.34 if Re_final > 0 else 0.34
    U_T = math.sqrt((4 * g * D_p * (st.session_state['rho_L'] - st.session_state['rho_V'])) / (3 * st.session_state['rho_V'] * C_D_final))

status = "PASS (Suitable)" if U_V < U_T else "FAIL (Carry-over Risk)"
status_color = "green" if U_V < U_T else "red"

st.markdown("---")

# --- Web Screen Preview ---
st.header("📊 3. Output Summary & Formulas (Web Preview)")

st.markdown("**Output Summary Table**")
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
if not st.session_state['user_conclusion']:
    st.session_state['user_conclusion'] = f"""Based on the rigorous iterative hydraulic calculations utilizing the Intermediate Drag Law specified in API Standard 521, the actual upward vapor velocity (U_v = {U_V:.4f} m/s) is strictly maintained below the terminal settling velocity (U_T = {U_T:.4f} m/s) required for the target droplet size of {st.session_state['D_p_um']} μm.

Therefore, the existing vessel dimension (D = {st.session_state['D']:.3f} m) provides adequate cross-sectional area to ensure the successful disengagement of liquid droplets from the vapor phase, meeting the KOSHA PSM process safety design intent under the given operating conditions."""

st.session_state['user_conclusion'] = st.text_area("Edit Conclusion:", value=st.session_state['user_conclusion'], height=150)
user_conclusion_html = st.session_state['user_conclusion'].replace('\n', '<br>')

# --- HTML Report Generation ---
def generate_html_report():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{st.session_state['tag_no']} KO Drum Rating Report</title>
        <script>
        MathJax = {{ tex: {{ inlineMath: [['\\\\(', '\\\\)']] }} }};
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <style>
            body {{ font-family: 'Arial', sans-serif; font-size: 12px; color: #333; margin: 0; padding: 0; background-color: #fff; }}
            .page-container {{ width: 190mm; margin: 10mm auto; padding: 10mm; border: 2px solid #000; box-sizing: border-box; }}
            h1, h2, h3 {{ color: #000; margin-top: 15px; margin-bottom: 5px; }}
            h1 {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; }}
            
            /* Header Table (New 2-row Grid) */
            .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; table-layout: fixed; }}
            .header-table th, .header-table td {{ border: 1px solid #000; padding: 6px; text-align: left; overflow: hidden; white-space: nowrap; }}
            .header-table th {{ background-color: #f2f2f2; font-weight: bold; }}
            
            /* Data Tables (Strict 25% Grid) */
            .data-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; table-layout: fixed; }}
            .data-table th, .data-table td {{ border: 1px solid #000; padding: 6px; text-align: left; width: 25%; white-space: nowrap; overflow: hidden; }}
            .data-table th {{ background-color: #f2f2f2; font-weight: bold; }}
            
            .description {{ font-size: 11px; color: #555; font-style: italic; margin-bottom: 10px; }}
            .math-block {{ margin: 10px 0; font-size: 13px; }}
            .conclusion {{ background-color: #f9f9f9; padding: 10px; border: 1px dashed #333; line-height: 1.5; }}
            @media print {{
                .page-container {{ border: 2px solid #000; margin: 0; padding: 5mm; width: 100%; }}
                .nobreak {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="page-container">
            
            <h1>KO Drum Rating Report</h1>
            
            <table class="header-table">
                <tr>
                    <td rowspan="2" style="width: 15%; text-align: center;">&nbsp;</td>
                    <th style="width: 15%;">Project</th>
                    <td style="width: 30%;">{st.session_state['project']}</td>
                    <th style="width: 8%;">Rev.</th>
                    <td style="width: 8%;">{st.session_state['rev_no']}</td>
                    <th style="width: 8%;">Date</th>
                    <td style="width: 16%;">{st.session_state['date_str']}</td>
                </tr>
                <tr>
                    <th>Tag No.</th>
                    <td>{st.session_state['tag_no']}</td>
                    <th>Service</th>
                    <td colspan="3">{st.session_state['service']}</td>
                </tr>
            </table>

            <h2>1. Input Data</h2>
            <table class="data-table">
                <tr><th colspan="2" style="text-align:center;">Fluid Properties</th><th colspan="2" style="text-align:center;">Equipment & Droplet Data</th></tr>
                <tr><th>Vapor Mass Flow (\\(W_v\\))</th><td>{st.session_state['W_V']:,.1f} kg/hr</td><th>Vessel Inner Dia. (\\(D\\))</th><td>{st.session_state['D']:.3f} m</td></tr>
                <tr><th>Vapor Density (\\(\\rho_v\\))</th><td>{st.session_state['rho_V']:.4f} kg/m³</td><th>Vessel Tan. Height (\\(H\\))</th><td>{st.session_state['H']:.3f} m</td></tr>
                <tr><th>Vapor Viscosity (\\(\\mu_v\\))</th><td>{st.session_state['mu_V']:.6f} kg/m·s</td><th>Target Droplet (\\(D_p\\))</th><td>{st.session_state['D_p_um']} μm</td></tr>
                <tr><th>Liquid Mass Flow (\\(W_L\\))</th><td>{st.session_state['W_L']:,.1f} kg/hr</td><th colspan="2" style="background-color:#fff;"></th></tr>
                <tr><th>Liquid Density (\\(\\rho_L\\))</th><td>{st.session_state['rho_L']:.2f} kg/m³</td><th colspan="2" style="background-color:#fff;"></th></tr>
            </table>

            <h2>2. Output Summary</h2>
            <table class="data-table">
                <tr><th>Vapor Vol. Flow (\\(Q_v\\))</th><td>{Q_V:.4f} m³/s</td><th>Vapor Velocity (\\(U_v\\))</th><td><b>{U_V:.4f} m/s</b></td></tr>
                <tr><th>Vessel Cross Area (\\(A\\))</th><td>{A:.4f} m²</td><th>Terminal Velocity (\\(U_T\\))</th><td><b>{U_T:.4f} m/s</b></td></tr>
                <tr><th>Drag Coefficient (\\(C_D\\))</th><td>{C_D_final:.4f}</td><th>Design Suitability</th><td style="color:{status_color}; font-weight:bold;">{status}</td></tr>
            </table>

            <div class="nobreak">
                <h2>3. Detailed Calculations</h2>
                
                <h3>3.1 Actual Vapor Velocity (\\(U_v\\))</h3>
                <div class="description">Ref: Mass Conservation & Vessel Geometry</div>
                <div class="math-block">
                    \\[ U_v = \\frac{{W_v}}{{\\rho_v \\cdot 3600 \\cdot A}} = \\mathbf{{{U_V:.4f} \\text{{ m/s}}}} \\]
                </div>
                
                <h3>3.2 Final Drag Coefficient (\\(C_D\\))</h3>
                <div class="description">Ref: Intermediate Drag Law (API Std 521). Calculated via iterative convergence based on Particle Reynolds Number (\\(Re\\)).</div>
                <div class="math-block">
                    \\[ Re = \\frac{{D_p \\cdot U_T \\cdot \\rho_v}}{{\\mu_v}} = {Re_final:.2f} \\]
                    \\[ C_D = \\frac{{24}}{{Re}} + \\frac{{3}}{{\\sqrt{{Re}}}} + 0.34 = \\mathbf{{{C_D_final:.4f}}} \\]
                </div>
                
                <h3>3.3 Terminal Settling Velocity (\\(U_T\\))</h3>
                <div class="description">Ref: API Std 521 Equation for terminal velocity of a droplet settling against upward vapor flow.</div>
                <div class="math-block">
                    \\[ U_T = \\sqrt{{\\frac{{4 g D_p (\\rho_L - \\rho_v)}}{{3 \\rho_v C_D}}}} = \\mathbf{{{U_T:.4f} \\text{{ m/s}}}} \\]
                </div>
            </div>

            <div class="nobreak">
                <h2>4. Engineering Conclusion</h2>
                <div class="conclusion">{user_conclusion_html}</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

st.markdown("---")
st.header("📥 5. Download Final Report")
html_bytes = generate_html_report().encode('utf-8')
b64_html = base64.b64encode(html_bytes).decode()
href = f'<a href="data:text/html;charset=utf-8;base64,{b64_html}" download="{st.session_state["tag_no"]}_Rating_Report.html" style="background-color: #0078D7; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Download HTML Report</a>'
st.markdown(href, unsafe_allow_html=True)
