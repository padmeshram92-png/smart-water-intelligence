from dataclasses import asdict
from detector import Reading, detect_issue

SCENARIOS = {
    "normal": Reading(
        scenario="normal",
        flow_lpm=0.3,
        tank_level_pct=55,
        minutes_observed=10,
        baseline_liters=20,
        observed_liters=18,
    ),
    "continuous_flow": Reading(
        scenario="continuous_flow",
        flow_lpm=1.4,
        tank_level_pct=60,
        minutes_observed=45,
        baseline_liters=30,
        observed_liters=55,
    ),
    "tank_overflow": Reading(
        scenario="tank_overflow",
        flow_lpm=2.0,
        tank_level_pct=98,
        minutes_observed=8,
        baseline_liters=15,
        observed_liters=16,
    ),
    "usage_spike": Reading(
        scenario="usage_spike",
        flow_lpm=0.4,
        tank_level_pct=70,
        minutes_observed=20,
        baseline_liters=25,
        observed_liters=65,
    ),
}

def run_scenario(name: str) -> dict:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}. Choose from {', '.join(SCENARIOS)}")
    reading = SCENARIOS[name]
    result = detect_issue(reading)
    return {
        "reading": asdict(reading),
        "detection": asdict(result),
    }

if __name__ == "__main__":
    for name in SCENARIOS:
        output = run_scenario(name)
        print(f"\n=== {name.upper()} ===")
        print("Reading:", output["reading"])
        print("Detection:", output["detection"])
