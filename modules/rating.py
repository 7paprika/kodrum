from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class RatingInputs:
    W_V: float
    rho_V: float
    mu_V_cp: float
    W_L: float
    rho_L: float
    D: float
    H: float
    D_p_um: float
    liquid_level_fraction: float = 0.30
    target_residence_time_s: float = 60.0


@dataclass
class RatingResult:
    vapor_volumetric_flow_m3_s: float = 0.0
    liquid_volumetric_flow_m3_s: float = 0.0
    vessel_cross_area_m2: float = 0.0
    vapor_velocity_m_s: float = 0.0
    terminal_velocity_m_s: float = 0.0
    reynolds_number: float = 0.0
    drag_coefficient: float = 0.0
    liquid_hold_up_volume_m3: float = 0.0
    residence_time_s: float = 0.0
    velocity_pass: bool = False
    residence_pass: bool = False
    overall_pass: bool = False
    validation_errors: List[str] = field(default_factory=list)


def validate_inputs(inputs: RatingInputs) -> List[str]:
    errors: List[str] = []
    if inputs.W_V < 0:
        errors.append("W_V must be zero or greater.")
    if inputs.W_L < 0:
        errors.append("W_L must be zero or greater.")
    if inputs.rho_V <= 0:
        errors.append("rho_V must be greater than zero.")
    if inputs.rho_L <= 0:
        errors.append("rho_L must be greater than zero.")
    if inputs.rho_L <= inputs.rho_V:
        errors.append("rho_L must be greater than rho_V for gravity separation.")
    if inputs.mu_V_cp <= 0:
        errors.append("mu_V must be greater than zero.")
    if inputs.D <= 0:
        errors.append("D must be greater than zero.")
    if inputs.H <= 0:
        errors.append("H must be greater than zero.")
    if inputs.D_p_um <= 0:
        errors.append("D_p must be greater than zero.")
    if not 0 < inputs.liquid_level_fraction < 1:
        errors.append("liquid_level_fraction must be between 0 and 1.")
    if inputs.target_residence_time_s <= 0:
        errors.append("target_residence_time_s must be greater than zero.")
    return errors


def _calculate_terminal_velocity(inputs: RatingInputs, droplet_diameter_m: float) -> tuple[float, float, float]:
    g = 9.81
    terminal_velocity = 0.5
    mu_v_si = inputs.mu_V_cp / 1000.0
    reynolds_number = 0.0
    drag_coefficient = 0.34

    for _ in range(25):
        reynolds_number = (droplet_diameter_m * terminal_velocity * inputs.rho_V) / mu_v_si
        drag_coefficient = (24 / reynolds_number) + (3 / math.sqrt(reynolds_number)) + 0.34
        terminal_velocity = math.sqrt(
            (4 * g * droplet_diameter_m * (inputs.rho_L - inputs.rho_V))
            / (3 * inputs.rho_V * drag_coefficient)
        )
    return terminal_velocity, reynolds_number, drag_coefficient


def calculate_rating(inputs: RatingInputs) -> RatingResult:
    result = RatingResult()
    result.validation_errors = validate_inputs(inputs)
    if result.validation_errors:
        return result

    droplet_diameter_m = inputs.D_p_um / 1_000_000.0
    result.vapor_volumetric_flow_m3_s = inputs.W_V / (inputs.rho_V * 3600.0)
    result.liquid_volumetric_flow_m3_s = inputs.W_L / (inputs.rho_L * 3600.0)
    result.vessel_cross_area_m2 = math.pi * inputs.D**2 / 4.0
    result.vapor_velocity_m_s = result.vapor_volumetric_flow_m3_s / result.vessel_cross_area_m2
    (
        result.terminal_velocity_m_s,
        result.reynolds_number,
        result.drag_coefficient,
    ) = _calculate_terminal_velocity(inputs, droplet_diameter_m)
    result.liquid_hold_up_volume_m3 = result.vessel_cross_area_m2 * inputs.H * inputs.liquid_level_fraction
    result.residence_time_s = (
        math.inf
        if result.liquid_volumetric_flow_m3_s == 0
        else result.liquid_hold_up_volume_m3 / result.liquid_volumetric_flow_m3_s
    )
    result.velocity_pass = result.vapor_velocity_m_s < result.terminal_velocity_m_s
    result.residence_pass = result.residence_time_s >= inputs.target_residence_time_s
    result.overall_pass = result.velocity_pass and result.residence_pass
    return result


def build_default_conclusion(inputs: RatingInputs, result: RatingResult) -> str:
    if result.validation_errors:
        return (
            "The submitted inputs are not valid for a KO drum rating. "
            "Please correct the validation errors before using the report for engineering decisions."
        )

    velocity_sentence = (
        f"The vapor disengagement check is {'acceptable' if result.velocity_pass else 'not acceptable'} "
        f"because the actual vapor velocity ({result.vapor_velocity_m_s:.4f} m/s) is "
        f"{'below' if result.velocity_pass else 'above'} the terminal droplet settling velocity "
        f"({result.terminal_velocity_m_s:.4f} m/s) for a {inputs.D_p_um:.0f} μm target droplet."
    )
    residence_sentence = (
        f"The liquid residence time is {result.residence_time_s:.1f} s against a target of "
        f"{inputs.target_residence_time_s:.1f} s, so the liquid holdup check is "
        f"{'acceptable' if result.residence_pass else 'not acceptable'} at a liquid level fraction of "
        f"{inputs.liquid_level_fraction:.2f}."
    )
    overall_sentence = (
        "Overall, the current vessel geometry is suitable for the checked service."
        if result.overall_pass
        else "Overall, the current vessel geometry requires improvement before it can be considered acceptable."
    )
    return f"{velocity_sentence}\n\n{residence_sentence}\n\n{overall_sentence}"
