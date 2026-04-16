from modules.rating import RatingInputs, calculate_rating
from modules.reporting import generate_html_report


def test_generate_html_report_contains_residence_time_section():
    inputs = RatingInputs(
        W_V=2239.8,
        rho_V=5.679,
        mu_V_cp=0.0090,
        W_L=25360.4,
        rho_L=824.5,
        D=0.6,
        H=1.53,
        D_p_um=300.0,
        liquid_level_fraction=0.3,
        target_residence_time_s=60.0,
    )
    result = calculate_rating(inputs)

    html = generate_html_report(
        metadata={"project": "Demo", "tag_no": "V-101", "service": "Flare KO Drum", "rev_no": "0", "date_str": "2026-04-15"},
        inputs=inputs,
        result=result,
        conclusion_text="Example conclusion",
    )

    assert "Residence Time Check" in html
    assert "liquid holdup" in html.lower()
    assert "V-101" in html
