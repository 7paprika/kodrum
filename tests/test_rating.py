import math

import pytest

from modules.rating import RatingInputs, build_default_conclusion, calculate_rating, validate_inputs


def sample_inputs(**overrides):
    data = {
        "W_V": 2239.8,
        "rho_V": 5.679,
        "mu_V_cp": 0.0090,
        "W_L": 25360.4,
        "rho_L": 824.5,
        "D": 0.6,
        "H": 1.53,
        "D_p_um": 300.0,
        "liquid_level_fraction": 0.30,
        "target_residence_time_s": 60.0,
    }
    data.update(overrides)
    return RatingInputs(**data)


def test_validate_inputs_rejects_nonphysical_values():
    inputs = sample_inputs(rho_V=0.0, mu_V_cp=0.0, D=0.0, H=0.0, D_p_um=0.0)

    errors = validate_inputs(inputs)

    assert any("rho_V" in err for err in errors)
    assert any("mu_V" in err for err in errors)
    assert any("D" in err for err in errors)
    assert any("H" in err for err in errors)
    assert any("D_p" in err for err in errors)


def test_validate_inputs_requires_liquid_density_to_exceed_vapor_density():
    inputs = sample_inputs(rho_V=12.0, rho_L=10.0)

    errors = validate_inputs(inputs)

    assert any("rho_L" in err and "rho_V" in err for err in errors)


def test_calculate_rating_uses_height_and_liquid_flow_for_residence_time():
    inputs = sample_inputs(H=2.0, W_L=3600.0, rho_L=900.0, liquid_level_fraction=0.5)

    result = calculate_rating(inputs)

    area = math.pi * inputs.D**2 / 4.0
    expected_volume = area * inputs.H * inputs.liquid_level_fraction
    expected_q_l = inputs.W_L / (inputs.rho_L * 3600.0)
    expected_residence = expected_volume / expected_q_l

    assert result.liquid_hold_up_volume_m3 == pytest.approx(expected_volume)
    assert result.liquid_volumetric_flow_m3_s == pytest.approx(expected_q_l)
    assert result.residence_time_s == pytest.approx(expected_residence)


def test_overall_status_fails_when_residence_time_is_below_target_even_if_velocity_passes():
    inputs = sample_inputs(target_residence_time_s=600.0)

    result = calculate_rating(inputs)

    assert result.velocity_pass is True
    assert result.residence_pass is False
    assert result.overall_pass is False


def test_default_conclusion_mentions_both_velocity_and_residence_results():
    inputs = sample_inputs(target_residence_time_s=600.0)
    result = calculate_rating(inputs)

    conclusion = build_default_conclusion(inputs, result)

    assert "vapor disengagement" in conclusion.lower()
    assert "residence time" in conclusion.lower()
    assert "not acceptable" in conclusion.lower() or "improvement" in conclusion.lower()
