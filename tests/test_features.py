from transforms.features import keep_sensors, low_variance_sensors, regime_key


def test_constant_sensors_are_dropped():
    stds = {f"sensor_{i}": 1.0 for i in range(1, 22)}
    stds["sensor_1"] = 0.0
    stds["sensor_5"] = 1e-9
    dropped = low_variance_sensors(stds, threshold=1e-6)
    assert "sensor_1" in dropped
    assert "sensor_5" in dropped
    assert "sensor_2" not in dropped


def test_keep_sensors_matches_drop_list():
    stds = {f"sensor_{i}": 0.0 for i in range(1, 22)}
    stds["sensor_4"] = 3.2
    stds["sensor_7"] = 1.1
    kept = keep_sensors(stds)
    assert kept == ["sensor_4", "sensor_7"]


def test_regime_key_groups_similar_settings():
    a = regime_key(0.0023, 0.0003, 100.0)
    b = regime_key(0.0019, 0.0002, 100.0)
    c = regime_key(42.0, 0.84, 100.0)
    assert a == b
    assert a != c
