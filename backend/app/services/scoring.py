"""
Safety score calculator.
SafetyScore = 100 - sum(violation_weight * count)
"""
from app.models.incident import ViolationType

VIOLATION_WEIGHTS: dict[str, float] = {
    ViolationType.no_helmet: 10.0,
    ViolationType.no_vest: 8.0,
    ViolationType.high_risk_zone: 20.0,
    ViolationType.machinery_proximity: 25.0,
    ViolationType.fall_risk: 30.0,
}


def calculate_safety_score(incidents: list) -> float:
    penalty = sum(VIOLATION_WEIGHTS.get(i.violation_type, 5.0) for i in incidents)
    return max(0.0, round(100.0 - penalty, 1))
