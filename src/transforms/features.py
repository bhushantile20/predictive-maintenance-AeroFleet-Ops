"""Feature helpers that do not need Spark (BRD C4)."""

from columns import SENSOR_COLS


def low_variance_sensors(std_by_sensor: dict, threshold: float = 1e-6) -> list[str]:
    """Return sensor names that are almost constant and should be dropped."""
    dropped = []
    for name in SENSOR_COLS:
        std = std_by_sensor.get(name, 0.0)
        if std is None or std <= threshold:
            dropped.append(name)
    return dropped


def keep_sensors(std_by_sensor: dict, threshold: float = 1e-6) -> list[str]:
    dropped = set(low_variance_sensors(std_by_sensor, threshold))
    return [name for name in SENSOR_COLS if name not in dropped]


def regime_key(op1: float, op2: float, op3: float) -> str:
    """Simple operating-regime id from the 3 settings (BRD C1).

    FD001 has one flight condition. FD002/FD004 have six. Rounding is enough
    to group similar conditions without a clustering model.
    """
    return f"{round(op1, 0):.0f}|{round(op2, 2):.2f}|{round(op3, 0):.0f}"
