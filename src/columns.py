"""CMAPSS column names. One row = one engine, one operating cycle."""

OP_COLS = ["op_setting_1", "op_setting_2", "op_setting_3"]
SENSOR_COLS = [f"sensor_{i}" for i in range(1, 22)]
ID_COLS = ["dataset_id", "unit_number", "time_in_cycles"]

# NASA C-MAPSS sensor names (for comments / stakeholder notes only)
SENSOR_COMMENTS = {
    "sensor_1": "T2 total temperature fan inlet",
    "sensor_2": "T24 total temperature LPC outlet",
    "sensor_3": "T30 total temperature HPC outlet",
    "sensor_4": "T50 total temperature LPT outlet",
    "sensor_5": "P2 pressure fan inlet",
    "sensor_6": "P15 bypass-duct pressure",
    "sensor_7": "P30 HPC outlet pressure",
    "sensor_8": "Nf physical fan speed",
    "sensor_9": "Nc physical core speed",
    "sensor_10": "epr engine pressure ratio",
    "sensor_11": "Ps30 HPC outlet static pressure",
    "sensor_12": "phi ratio of fuel flow to Ps30",
    "sensor_13": "NRf corrected fan speed",
    "sensor_14": "NRc corrected core speed",
    "sensor_15": "BPR bypass ratio",
    "sensor_16": "farB burner fuel-air ratio",
    "sensor_17": "htBleed bleed enthalpy",
    "sensor_18": "Nf_dmd demanded fan speed",
    "sensor_19": "PCNR_dmd demanded corrected fan speed",
    "sensor_20": "W31 HPT coolant bleed",
    "sensor_21": "W32 LPT coolant bleed",
}

TRAIN_TEST_NAMES = [
    "unit_number",
    "time_in_cycles",
    *OP_COLS,
    *SENSOR_COLS,
]
