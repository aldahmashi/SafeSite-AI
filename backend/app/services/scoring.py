"""
Safety score calculator.

Score = 100 - penalty, clamped to [0, 100].

Penalty is based on DISTINCT (worker, violation_type) pairs so that a
worker who violates for 30 seconds (generating 3 cooldown-gated incidents)
counts the same as one who violates for 10 seconds.
Untracked persons (worker_id=None) are deduplicated by violation_type only
— conservatively counted as one "unknown worker" per type.
"""
from app.models.incident import ViolationType

# Weight per unique violating-worker per violation type
VIOLATION_WEIGHTS: dict[str, float] = {
    ViolationType.no_helmet:        5.0,
    ViolationType.no_vest:          4.0,
    ViolationType.high_risk_zone:   10.0,
    ViolationType.machinery_proximity: 12.0,
    ViolationType.fall_risk:        15.0,
}


def calculate_safety_score(incidents: list) -> float:
    """
    Return a safety score in [0, 100].
    Each (worker_id, violation_type) pair is counted once regardless of
    how many repeated incidents were recorded for that worker.
    """
    tracked_seen:   set[tuple] = set()
    untracked_seen: set[str]   = set()
    penalty = 0.0

    for i in incidents:
        vt = i.violation_type
        weight = VIOLATION_WEIGHTS.get(vt, 5.0)

        if i.worker_id is not None:
            key = (i.worker_id, vt)
            if key not in tracked_seen:
                tracked_seen.add(key)
                penalty += weight
        else:
            # Untracked: count once per violation type
            vt_str = str(vt)
            if vt_str not in untracked_seen:
                untracked_seen.add(vt_str)
                penalty += weight

    return max(0.0, round(100.0 - penalty, 1))
