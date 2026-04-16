from __future__ import annotations

from html import escape

from modules.rating import RatingInputs, RatingResult


def _status_text(is_pass: bool) -> str:
    return "PASS" if is_pass else "FAIL"


def generate_html_report(metadata: dict, inputs: RatingInputs, result: RatingResult, conclusion_text: str) -> str:
    status_color = "#0f9d58" if result.overall_pass else "#d93025"
    conclusion_html = escape(conclusion_text).replace("\n", "<br>")
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{escape(metadata.get('tag_no', 'KO Drum'))} Vertical KO Drum Rating Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
    h1, h2, h3 {{ color: #111827; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .status {{ color: {status_color}; font-weight: 700; }}
    .box {{ border: 1px solid #d1d5db; background: #f9fafb; padding: 12px; margin-bottom: 16px; }}
  </style>
</head>
<body>
  <h1>Vertical KO Drum Rating & Liquid Holdup Report</h1>
  <table>
    <tr><th>Project</th><td>{escape(metadata.get('project', ''))}</td><th>Tag No.</th><td>{escape(metadata.get('tag_no', ''))}</td></tr>
    <tr><th>Service</th><td>{escape(metadata.get('service', ''))}</td><th>Revision / Date</th><td>{escape(metadata.get('rev_no', ''))} / {escape(metadata.get('date_str', ''))}</td></tr>
  </table>

  <h2>Input Summary</h2>
  <table>
    <tr><th>Vapor Mass Flow</th><td>{inputs.W_V:,.2f} kg/hr</td><th>Liquid Mass Flow</th><td>{inputs.W_L:,.2f} kg/hr</td></tr>
    <tr><th>Vapor Density</th><td>{inputs.rho_V:.4f} kg/m³</td><th>Liquid Density</th><td>{inputs.rho_L:.2f} kg/m³</td></tr>
    <tr><th>Vapor Viscosity</th><td>{inputs.mu_V_cp:.4f} cP</td><th>Target Droplet</th><td>{inputs.D_p_um:.1f} μm</td></tr>
    <tr><th>Diameter</th><td>{inputs.D:.3f} m</td><th>Tangent Height</th><td>{inputs.H:.3f} m</td></tr>
    <tr><th>Liquid Level Fraction</th><td>{inputs.liquid_level_fraction:.2f}</td><th>Target Residence Time</th><td>{inputs.target_residence_time_s:.1f} s</td></tr>
  </table>

  <h2>Rating Summary</h2>
  <table>
    <tr><th>Vapor Velocity</th><td>{result.vapor_velocity_m_s:.4f} m/s</td><th>Terminal Velocity</th><td>{result.terminal_velocity_m_s:.4f} m/s</td></tr>
    <tr><th>Velocity Check</th><td>{_status_text(result.velocity_pass)}</td><th>Residence Check</th><td>{_status_text(result.residence_pass)}</td></tr>
    <tr><th>Overall Status</th><td class="status">{_status_text(result.overall_pass)}</td><th>Re / Cd</th><td>{result.reynolds_number:.2f} / {result.drag_coefficient:.4f}</td></tr>
  </table>

  <h2>Residence Time Check</h2>
  <div class="box">
    <p>Available liquid holdup volume: <strong>{result.liquid_hold_up_volume_m3:.4f} m³</strong></p>
    <p>Liquid volumetric flow: <strong>{result.liquid_volumetric_flow_m3_s:.6f} m³/s</strong></p>
    <p>Calculated residence time: <strong>{result.residence_time_s:.2f} s</strong></p>
    <p>This liquid holdup check uses vessel cross-sectional area, tangent height, and the configured operating liquid level fraction.</p>
  </div>

  <h2>Engineering Conclusion</h2>
  <div class="box">{conclusion_html}</div>
</body>
</html>
"""
