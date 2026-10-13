from transforms.rul import add_rul_to_records, remaining_useful_life


def test_rul_at_failure_is_zero():
    assert remaining_useful_life(192, 192, clip=125) == 0


def test_rul_is_clipped():
    assert remaining_useful_life(10, 300, clip=125) == 125


def test_rul_unclipped_when_below_cap():
    assert remaining_useful_life(80, 100, clip=125) == 20


def test_negative_rul_becomes_zero():
    assert remaining_useful_life(50, 40, clip=125) == 0


def test_add_rul_uses_max_cycle_per_unit():
    rows = [
        {"unit_number": 1, "time_in_cycles": 1},
        {"unit_number": 1, "time_in_cycles": 2},
        {"unit_number": 1, "time_in_cycles": 3},
        {"unit_number": 2, "time_in_cycles": 1},
        {"unit_number": 2, "time_in_cycles": 2},
    ]
    labeled = add_rul_to_records(rows, clip=125)
    by_key = {(r["unit_number"], r["time_in_cycles"]): r["rul"] for r in labeled}
    assert by_key[(1, 1)] == 2
    assert by_key[(1, 3)] == 0
    assert by_key[(2, 1)] == 1
    assert by_key[(2, 2)] == 0
