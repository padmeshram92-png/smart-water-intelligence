from dataclasses import dataclass
from typing import Literal

Scenario = Literal["normal", "continuous_flow", "tank_overflow", "usage_spike"]

@dataclass
class Reading:
    scenario: Scenario
    flow_lpm: float
    tank_level_pct: float
    minutes_observed: int
    baseline_liters: float
    observed_liters: float

@dataclass
class DetectionResult:
    status: str
    alert_type: str
    message: str
    severity: str

def detect_issue(reading: Reading) -> DetectionResult:
    """
    Rule-based demo detector for SIMULATED readings.
    This is not a validated real-world leak detector.
    """
    if not 0 <= reading.tank_level_pct <= 100:
        return DetectionResult(
            status="Invalid reading",
            alert_type="data_error",
            message="Tank level must be between 0 and 100%.",
            severity="error",
        )

    if reading.minutes_observed <= 0:
        return DetectionResult(
            status="Invalid reading",
            alert_type="data_error",
            message="Observation duration must be greater than zero.",
            severity="error",
        )

    # Tank overflow risk: high tank level while water continues flowing.
    if reading.tank_level_pct >= 95 and reading.flow_lpm > 0:
        return DetectionResult(
            status="Alert",
            alert_type="tank_overflow_risk",
            message="Tank is nearly full while flow continues. Inspect the inlet.",
            severity="high",
        )

    # Continuous flow: demo rule. In a real system, this should be calibrated
    # to a household's expected usage and should account for legitimate use.
    if reading.flow_lpm >= 1.0 and reading.minutes_observed >= 30:
        return DetectionResult(
            status="Alert",
            alert_type="possible_continuous_flow",
            message="Flow has continued for 30 minutes or more. Check whether this is expected.",
            severity="medium",
        )

    # Abnormal consumption compared with a supplied baseline.
    if reading.baseline_liters > 0 and reading.observed_liters >= 2 * reading.baseline_liters:
        return DetectionResult(
            status="Warning",
            alert_type="unusual_consumption",
            message="Observed consumption is at least twice the baseline. Verify the reading.",
            severity="medium",
        )

    return DetectionResult(
        status="Normal",
        alert_type="none",
        message="No configured rule was triggered for this simulated reading.",
        severity="low",
    )
