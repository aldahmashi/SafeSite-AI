"""
Restricted zone detection.
Checks whether a worker center point falls inside any predefined polygon zone.
Implemented in Phase 2.
"""
from typing import NamedTuple


class Zone(NamedTuple):
    name: str
    polygon: list[tuple[int, int]]
    risk_multiplier: float = 1.5


def point_in_polygon(point: tuple[int, int], polygon: list[tuple[int, int]]) -> bool:
    """Ray-casting algorithm."""
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside
