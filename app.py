from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from modules.rating import RatingInputs, build_default_conclusion, calculate_rating
from modules.reporting import generate_html_report


st.set_page_config(page_title="Vertical KO Drum Rating App", layout="wide")


DEFAULTS = {
    "tag_no": "V-101",
    "rev_no": "0",
    "service": "Flare KO Drum",
    "project": "SK Trichem Project",
    "date_str": datetime.now().strftime("%Y-%m-%d"),
    "W_V": 2239.8,
    "rho_V": 5.679,
    "mu_V_cp": 0.0090,
    "W_L": 25360.4,
    "rho_L": 824.5,
    "D": 0.600,
    "H": 1.530,
    "D_p_um": 300.0,
    "liquid_level_fraction": 0.30,
    "target_residence_time_s": 60.0,
    "conclusion_mode": "Auto",
    "user_conclusion": "",
}

INPUT_EXPORT_KEYS = list(DEFAULTS.keys())


for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def apply_json_payload(payload: dict) -> None:
    for key, value in payload.items():
        if key in DEFAULTS:
            st.session_state[key] = value


def current_inputs() -> RatingInputs:
    return RatingInputs(
        W_V=float(st.session_state["W_V"]),
        rho_V=float(st.session_state["rho_V"]),
        mu_V_cp=float(st.session_state["mu_V_cp"]),
        W_L=float(st.session_state["W_L"]),
        rho_L=float(st.session_state["rho_L"]),
        D=float(st.session_state["D"]),
        H=float(st.session_state["H"]),
        D_p_um=float(st.session_state["D_p_um"]),
        liquid_level_fraction=float(st.session_state["liquid_level_fraction"]),
        target_residence_time_s=float(st.session_state["target_residence_time_s"]),
    )


def current_metadata() -> dict[str, str]:
    return {
        "project": str(st.session_state["project"]),
        "tag_no": str(st.session_state["tag_no"]),
        "service": str(st.session_state["service"]),
        "rev_no": str(st.session_state["rev_no"]),
        "date_str": str(st.session_state["date_str"]),
    }


st.sidebar.header("💾 JSON Data Loader")
json_input = st.sidebar.text_area("JSON Input Text", height=180)
if st.sidebar.button("Load JSON Data"):
    if json_input.strip():
        try:
            payload = json.loads(json_input)
            if not isinstance(payload, dict):
                st.sidebar.error("❌ JSON root must be an object.")
            else:
                apply_json_payload(payload)
                st.sidebar.success("✅ Data applied.")
                st.rerun()
        except json.JSONDecodeError:
            st.sidebar.error("❌ Invalid JSON format.")

saved_payload = {key: st.session_state[key] for key in INPUT_EXPORT_KEYS}
st.sidebar.text_area(
    "Copy JSON to Save",
    value=json.dumps(saved_payload, indent=2, ensure_ascii=False),
    height=220,
)
st.sidebar.caption("Known fields only are applied when loading JSON.")


inputs = current_inputs()
result = calculate_rating(inputs)
auto_conclusion = build_default_conclusion(inputs, result)

st.title("Vertical KO Drum Rating & Liquid Holdup Check")
st.caption(
    "This tool performs a vapor disengagement check and a liquid residence-time / holdup check. "
    "It is not a full separator design package."
)
st.markdown("---")

st.header("📝 1. Document Metadata")
col_m1, col_m2, col_m3 = st.columns(3)
st.session_state["project"] = col_m1.text_input("Project", value=st.session_state["project"])
st.session_state["rev_no"] = col_m2.text_input("Revision", value=st.session_state["rev_no"])
st.session_state["date_str"] = col_m3.text_input("Date", value=st.session_state["date_str"])
col_m4, col_m5 = st.columns(2)
st.session_state["tag_no"] = col_m4.text_input("Tag No.", value=st.session_state["tag_no"])
st.session_state["service"] = col_m5.text_input("Service", value=st.session_state["service"])

st.header("⚙️ 2. Process & Equipment Input Data")
col_i1, col_i2 = st.columns(2)

with col_i1:
    st.subheader("Fluid Properties")
    st.session_state["W_V"] = st.number_input("Vapor Mass Flow, W_v (kg/hr)", min_value=0.0, value=float(st.session_state["W_V"]), step=100.0)
    st.session_state["rho_V"] = st.number_input("Vapor Density, ρ_v (kg/m³)", min_value=0.0001, value=float(st.session_state["rho_V"]), format="%.4f")
    st.session_state["mu_V_cp"] = st.number_input("Vapor Viscosity, μ_v (cP)", min_value=0.0001, value=float(st.session_state["mu_V_cp"]), format="%.4f")
    st.session_state["W_L"] = st.number_input("Liquid Mass Flow, W_L (kg/hr)", min_value=0.0, value=float(st.session_state["W_L"]), step=1000.0)
    st.session_state["rho_L"] = st.number_input("Liquid Density, ρ_L (kg/m³)", min_value=0.0001, value=float(st.session_state["rho_L"]), format="%.2f")

with col_i2:
    st.subheader("Equipment & Rating Targets")
    st.session_state["D"] = st.number_input("Vessel Inner Dia., D (m)", min_value=0.001, value=float(st.session_state["D"]), format="%.3f")
    st.session_state["H"] = st.number_input("Vessel Tangent Height, H (m)", min_value=0.001, value=float(st.session_state["H"]), format="%.3f")
    st.session_state["D_p_um"] = st.number_input("Target Droplet, D_p (μm)", min_value=1.0, value=float(st.session_state["D_p_um"]), step=50.0)
    st.session_state["liquid_level_fraction"] = st.number_input(
        "Operating Liquid Level Fraction, h/H (-)",
        min_value=0.05,
        max_value=0.95,
        value=float(st.session_state["liquid_level_fraction"]),
        step=0.05,
        format="%.2f",
    )
    st.session_state["target_residence_time_s"] = st.number_input(
        "Target Residence Time (s)",
        min_value=1.0,
        value=float(st.session_state["target_residence_time_s"]),
        step=5.0,
        format="%.1f",
    )

with st.expander("ℹ️ Design Notes & Assumptions"):
    st.markdown(
        """
- Vapor disengagement is checked by comparing actual superficial vapor velocity with droplet terminal settling velocity.
- Liquid handling is checked using liquid holdup volume = cross-sectional area × tangent height × operating liquid level fraction.
- Residence time = liquid holdup volume / liquid volumetric flow.
- This is a practical rating aid, not a complete mechanical/process design package.
        """
    )

inputs = current_inputs()
result = calculate_rating(inputs)
metadata = current_metadata()

st.markdown("---")
st.header("📊 3. Rating Results")

if result.validation_errors:
    for error in result.validation_errors:
        st.error(error)
else:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Vapor Velocity, Uv", f"{result.vapor_velocity_m_s:.4f} m/s")
    metric_cols[1].metric("Terminal Velocity, Ut", f"{result.terminal_velocity_m_s:.4f} m/s")
    metric_cols[2].metric("Residence Time", f"{result.residence_time_s:.1f} s")
    metric_cols[3].metric("Holdup Volume", f"{result.liquid_hold_up_volume_m3:.3f} m³")

    status_text = "PASS" if result.overall_pass else "FAIL"
    status_color = "green" if result.overall_pass else "red"
    st.markdown(f"<h3 style='color:{status_color};'>Overall Rating Status: {status_text}</h3>", unsafe_allow_html=True)

    summary_col1, summary_col2 = st.columns(2)
    with summary_col1:
        st.markdown("**Velocity Summary**")
        st.markdown(
            f"""
- Vapor volumetric flow, Qv = {result.vapor_volumetric_flow_m3_s:.6f} m³/s
- Vessel cross-sectional area, A = {result.vessel_cross_area_m2:.6f} m²
- Actual vapor velocity, Uv = {result.vapor_velocity_m_s:.6f} m/s
- Terminal velocity, Ut = {result.terminal_velocity_m_s:.6f} m/s
- Reynolds number = {result.reynolds_number:.2f}
- Drag coefficient = {result.drag_coefficient:.4f}
- Velocity check = {'PASS' if result.velocity_pass else 'FAIL'}
            """
        )
        st.latex(rf"U_v = \frac{{W_v}}{{\rho_v \cdot 3600 \cdot A}} = {result.vapor_velocity_m_s:.4f}\ \mathrm{{m/s}}")
        st.latex(rf"U_T = \sqrt{{\frac{{4 g D_p (\rho_L - \rho_v)}}{{3 \rho_v C_D}}}} = {result.terminal_velocity_m_s:.4f}\ \mathrm{{m/s}}")
    with summary_col2:
        st.markdown("**Liquid Holdup / Residence Summary**")
        st.markdown(
            f"""
- Liquid volumetric flow, QL = {result.liquid_volumetric_flow_m3_s:.6f} m³/s
- Operating liquid height = H × fraction = {inputs.H:.3f} × {inputs.liquid_level_fraction:.2f}
- Available holdup volume = {result.liquid_hold_up_volume_m3:.6f} m³
- Calculated residence time = {result.residence_time_s:.2f} s
- Target residence time = {inputs.target_residence_time_s:.2f} s
- Residence-time check = {'PASS' if result.residence_pass else 'FAIL'}
            """
        )
        st.latex(rf"V_{{hold}} = A \cdot H \cdot f = {result.liquid_hold_up_volume_m3:.4f}\ \mathrm{{m^3}}")
        st.latex(rf"t_{{res}} = \frac{{V_{{hold}}}}{{Q_L}} = {result.residence_time_s:.2f}\ \mathrm{{s}}")

st.markdown("---")
st.header("✍️ 4. Engineering Conclusion")
st.session_state["conclusion_mode"] = st.radio(
    "Conclusion Mode",
    ["Auto", "Manual"],
    index=0 if st.session_state["conclusion_mode"] == "Auto" else 1,
    horizontal=True,
)

if st.session_state["conclusion_mode"] == "Auto":
    conclusion_text = auto_conclusion
    st.text_area("Auto-generated Conclusion", value=conclusion_text, height=180, disabled=True)
else:
    if not st.session_state["user_conclusion"]:
        st.session_state["user_conclusion"] = auto_conclusion
    st.session_state["user_conclusion"] = st.text_area(
        "Manual Conclusion",
        value=st.session_state["user_conclusion"],
        height=180,
    )
    if st.button("Reset manual conclusion from current calculation"):
        st.session_state["user_conclusion"] = auto_conclusion
        st.rerun()
    conclusion_text = st.session_state["user_conclusion"]

st.markdown("---")
st.header("📥 5. Download Final Report")

report_html = generate_html_report(
    metadata=metadata,
    inputs=inputs,
    result=result,
    conclusion_text=conclusion_text,
)

st.download_button(
    label="Download HTML Report",
    data=report_html,
    file_name=f"{metadata['tag_no']}_KO_Drum_Rating_Report.html",
    mime="text/html",
    disabled=bool(result.validation_errors),
)
