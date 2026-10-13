"""RUL labeling (BRD C2). Pure Python so it can be unit-tested without Spark.

Training files run every engine until failure. Last cycle = failure.
RUL at a cycle = (failure cycle - current cycle).

We clip RUL at 125 cycles (common C-MAPSS practice). While the engine is
still healthy, extra remaining life does not change the sensor pattern much,
so a huge RUL label just adds noise.
"""


def remaining_useful_life(time_in_cycles: int, failure_cycle: int, clip: int = 125) -> int:
    raw = failure_cycle - time_in_cycles
    if raw < 0:
        return 0
    if clip is not None and raw > clip:
        return clip
    return raw


def add_rul_to_records(rows: list[dict], clip: int = 125) -> list[dict]:
    """rows need unit_number and time_in_cycles. failure_cycle = max cycle per unit."""
    max_cycle = {}
    for row in rows:
        unit = row["unit_number"]
        cycle = row["time_in_cycles"]
        if unit not in max_cycle or cycle > max_cycle[unit]:
            max_cycle[unit] = cycle

    labeled = []
    for row in rows:
        out = dict(row)
        out["rul"] = remaining_useful_life(
            row["time_in_cycles"], max_cycle[row["unit_number"]], clip
        )
        out["failure_cycle"] = max_cycle[row["unit_number"]]
        labeled.append(out)
    return labeled
