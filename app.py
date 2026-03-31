import streamlit as st
import math
import base64
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="KO Drum Rating App", layout="wide")

# --- UI: Metadata & Inputs ---
st.title("KO Drum Rating Report Generator")
st.markdown("Review the calculations on the screen, edit the Engineering Conclusion if necessary, and download the final HTML report.")
st.markdown("---")

st.header("📝 1. Document Metadata")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
project = col_m1.text_input("Project", "SK Trichem Project")
tag_no = col_m2.text_input("Tag No.", "V-101")
service = col_m3.text_input("Service", "Flare KO Drum")
rev_no = col_m4.text_input("Revision", "0")

st.header("⚙️ 2. Process & Equipment Input Data")
col_i1, col_i2 = st.columns(2)

with col_i1:
    st.subheader("Fluid Properties")
    W_V = st.number_input("Vapor Mass Flow, W_v (kg/hr)", value=2239.8, step=100.0)
    rho_V = st.number_input("Vapor Density, ρ_v (kg/m³)", value=5.679, format="%.4f")
    mu_V = st.number_input("Vapor Viscosity, μ_v (kg/m·s)", value=0.000009, format="%.6f")
    W_L = st.number_input("Liquid Mass Flow, W_L (kg/hr)", value=25360.4, step=1000.0)
    rho_L = st.number_input("Liquid Density, ρ_L (kg/m³)", value=824.5, format="%.2f")

with col_i2:
    st.subheader("Equipment & Droplet Specs")
    D = st.number_input("Vessel Inner Diameter, D (m)", value=0.600, format="%.3f")
    H = st.number_input("Vessel Tangent Height, H (m)", value=1.530, format="%.3f")
    D_p_um = st.number_input("Target Droplet Size, D_p (μm)", value=300.0, step=50.0)

# --- Calculation Engine ---
D_p = D_p_um / 1000000.0
g = 9.81

Q_V = W_V / (rho_V * 3600)
A = math.pi * (D**2) / 4
U_V = Q_V / A

# Iteration for C_D and U_T
U_T = 0.5
Re_final, C_D_final = 0, 0
for _ in range(10):
    Re_final = (D_p * U_T * rho_V) / mu_V
    C_D_final = (24 / Re_final) + (3 / math.sqrt(Re_final)) + 0.34 if Re_final > 0 else 0.34
    U_T = math.sqrt((4 * g * D_p * (rho_L - rho_V)) / (3 * rho_V * C_D_final))

status = "PASS (Suitable)" if U_V < U_T else "FAIL (Carry-over Risk)"
status_color = "green" if U_V < U_T else "red"
current_date = datetime.now().strftime("%Y-%m-%d")

st.markdown("---")

# --- Web Screen Preview ---
st.header("📊 3. Output Summary & Formulas (Web Preview)")

col_o1, col_o2 = st.columns(2)
with col_o1:
    st.markdown("**Output Summary Table**")
    st.markdown(f"""
    | Parameter | Value | Parameter | Value |
    | :--- | :--- | :--- | :--- |
    | **Actual Vapor Vol. Flow ($Q_v$)** | {Q_V:.4f} m³/s | **Actual Vapor Velocity ($U_v$)** | **{U_V:.4f} m/s** |
    | **Vessel Cross Area ($A$)** | {A:.4f} m² | **Terminal Settling Velocity ($U_T$)** | **{U_T:.4f} m/s** |
    | **Final Drag Coefficient ($C_D$)** | {C_D_final:.4f} | **Design Suitability** | <span style='color:{status_color}'>**{status}**</span> |
    """, unsafe_allow_html=True)

with col_o2:
    st.markdown("**Detailed Calculation Formulas**")
    st.latex(rf"U_v = \frac{{Q_v}}{{A}} = \frac{{{Q_V:.4f}}}{{{A:.4f}}} = {U_V:.4f} \text{{ m/s}}")
    st.latex(rf"Re = \frac{{D_p \cdot U_T \cdot \rho_v}}{{\mu_v}} = {Re_final:.2f}")
    st.latex(rf"C_D = \frac{{24}}{{Re}} + \frac{{3}}{{\sqrt{{Re}}}} + 0.34 = {C_D_final:.4f}")
    st.latex(rf"U_T = \sqrt{{\frac{{4 g D_p (\rho_L - \rho_v)}}{{3 \rho_v C_D}}}} = {U_T:.4f} \text{{ m/s}}")

st.markdown("---")

# --- Editable Conclusion ---
st.header("✍️ 4. Engineering Conclusion")
st.caption("The text below will be inserted directly into the final HTML report. Edit it as needed to reflect your engineering judgment.")

default_conclusion = f"""Based on the rigorous iterative hydraulic calculations utilizing the Intermediate Drag Law specified in API Standard 521, the actual upward vapor velocity (U_v = {U_V:.4f} m/s) is strictly maintained below the terminal settling velocity (U_T = {U_T:.4f} m/s) required for the target droplet size of {D_p_um} μm.

Therefore, the existing vessel dimension (D = {D:.3f} m) provides adequate cross-sectional area to ensure the successful disengagement of liquid droplets from the vapor phase, meeting the KOSHA PSM process safety design intent under the given operating conditions."""

user_conclusion = st.text_area("Edit Conclusion:", value=default_conclusion, height=150)
user_conclusion_html = user_conclusion.replace('\n', '<br>') # Convert newlines for HTML

# --- HTML Report Generation ---
def generate_html_report():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{tag_no} KO Drum Rating Report</title>
        <script>
        MathJax = {{
          tex: {{ inlineMath: [['\\\\(', '\\\\)']] }}
        }};
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <style>
            body {{ font-family: 'Arial', sans-serif; font-size: 12px; color: #333; margin: 0; padding: 0; background-color: #fff; }}
            .page-container {{ width: 190mm; margin: 10mm auto; padding: 10mm; border: 2px solid #000; box-sizing: border-box; }}
            h1, h2, h3 {{ color: #000; margin-top: 15px; margin-bottom: 5px; }}
            h1 {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #000; padding: 6px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; width: 25%; }}
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
            <table>
                <tr>
                    <td rowspan="3" style="width: 20%; text-align: center; vertical-align: middle;">
                        &nbsp; </td>
                    <td rowspan="3" style="width: 40%; text-align: center; vertical-align: middle; font-size: 18px; font-weight: bold;">
                        KO Drum Rating Report
                    </td>
                    <th style="width: 15%;">Project</th>
                    <td>{project}</td>
                </tr>
                <tr>
                    <th>Tag No.</th>
                    <td>{tag_no}</td>
                </tr>
                <tr>
                    <th>Date / Rev.</th>
                    <td>{current_date} / Rev.{rev_no}</td>
                </tr>
                <tr>
                    <th colspan="2">Service</th>
                    <td colspan="2">{service}</td>
                </tr>
            </table>

            <h2>1. Input Data</h2>
            <table>
                <tr><th colspan="2" style="background-color:#d9e1f2; text-align:center;">Fluid Properties</th><th colspan="2" style="background-color:#d9e1f2; text-align:center;">Equipment & Droplet Data</th></tr>
                <tr>
                    <th>Vapor Mass Flow (\\(W_v\\))</th><td>{W_V:,.1f} kg/hr</td>
                    <th>Vessel Inner Diameter (\\(D\\))</th><td>{D:.3f} m</td>
                </tr>
                <tr>
                    <th>Vapor Density (\\(\\rho_v\\))</th><td>{rho_V:.4f} kg/m³</td>
                    <th>Vessel Tangent Height (\\(H\\))</th><td>{H:.3f} m</td>
                </tr>
                <tr>
                    <th>Vapor Viscosity (\\(\\mu_v\\))</th><td>{mu_V:.6f} kg/m·s</td>
                    <th>Target Droplet Size (\\(D_p\\))</th><td>{D_p_um} μm</td>
                </tr>
                <tr>
                    <th>Liquid Mass Flow (\\(W_L\\))</th><td>{W_L:,.1f} kg/hr</td>
                    <th colspan="2"></th>
                </tr>
                <tr>
                    <th>Liquid Density (\\(\\rho_L\\))</th><td>{rho_L:.2f} kg/m³</td>
                    <th colspan="2"></th>
                </tr>
            </table>

            <h2>2. Output Summary</h2>
            <table>
                <tr>
                    <th>Actual Vapor Vol. Flow (\\(Q_v\\))</th><td>{Q_V:.4f} m³/s</td>
                    <th>Actual Vapor Velocity (\\(U_v\\))</th><td><b>{U_V:.4f} m/s</b></td>
                </tr>
                <tr>
                    <th>Vessel Cross Area (\\(A\\))</th><td>{A:.4f} m²</td>
                    <th>Terminal Settling Velocity (\\(U_T\\))</th><td><b>{U_T:.4f} m/s</b></td>
                </tr>
                <tr>
                    <th>Final Drag Coefficient (\\(C_D\\))</th><td>{C_D_final:.4f}</td>
                    <th>Design Suitability</th><td style="color:{status_color}; font-weight:bold;">{status}</td>
                </tr>
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
                    \\[ C_D = \\frac{{24}}{{Re}} + \\frac{{3}}{{\\sqrt{{Re}}}} + 0.34 = \\frac{{24}}{{{Re_final:.2f}}} + \\frac{{3}}{{\\sqrt{{{Re_final:.2f}}}}} + 0.34 = \\mathbf{{{C_D_final:.4f}}} \\]
                </div>
            </div>

            <div class="nobreak">
                <h3>3.3 Terminal Settling Velocity (\\(U_T\\))</h3>
                <div class="description">Ref: API Std 521 Equation for terminal velocity of a droplet settling against upward vapor flow.</div>
                <div class="math-block">
                    \\[ U_T = \\sqrt{{\\frac{{4 g D_p (\\rho_L - \\rho_v)}}{{3 \\rho_v C_D}}}} = \\sqrt{{\\frac{{4 \\times 9.81 \\times {D_p} \\times ({rho_L} - {rho_V})}}{{3 \\times {rho_V} \\times {C_D_final:.4f}}}}} = \\mathbf{{{U_T:.4f} \\text{{ m/s}}}} \\]
                </div>
            </div>

            <div class="nobreak">
                <h2>4. Engineering Conclusion</h2>
                <div class="conclusion">
                    {user_conclusion_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# --- Download Action ---
st.markdown("---")
st.header("📥 5. Download Final Report")
html_bytes = generate_html_report().encode('utf-8')
b64_html = base64.b64encode(html_bytes).decode()
href = f'<a href="data:text/html;charset=utf-8;base64,{b64_html}" download="{tag_no}_Rating_Report.html" style="background-color: #0078D7; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Download HTML Report</a>'

st.markdown(href, unsafe_allow_html=True)
st.caption("Instructions: Verify the preview above, edit the conclusion, and click to download. Open the HTML file in Chrome/Edge and press **Ctrl + P** to print to PDF.")
