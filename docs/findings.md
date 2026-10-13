# Findings for Reliability Engineering (1 page)

Fill the **numbers** after you run `pm-train-model` and `pm-batch-score`. The method is already decided (see `docs/assumptions.md`).

## What we built

A governed medallion pipeline on Databricks:

`landing Volume → bronze_train / bronze_test / bronze_rul → silver_cycles → gold_features → MLflow model → gold_predictions / gold_maintenance_queue`

Planners should open **`gold_maintenance_queue`**, not the raw sensors.

## RUL labeling

On training engines, last cycle is failure. RUL = remaining cycles until that last cycle, **clipped at 125**. We clip because early-life sensors look the same whether 200 or 400 cycles remain. Test engines have no failure in the file; we predict RUL at the last observed cycle and compare to `RUL_FD00x.txt` only for evaluation.

## Sensors we drop (C4)

On **FD001**, these channels are typically constant (or nearly so) and are dropped automatically by the Gold job:

- `sensor_1` (fan inlet temperature)
- `sensor_5` (fan inlet pressure)
- `sensor_6` (bypass-duct pressure — often almost constant on FD001)
- `sensor_10` (engine pressure ratio)
- `sensor_16` (fuel-air ratio)
- `sensor_18`, `sensor_19` (demanded speeds)

Confirm the live list in table `gold_sensor_selection` (`kept = false`). We keep the rest, then subtract the **training** mean for that operating regime, plus 5-cycle and 20-cycle rolling means. We do **not** train on `time_in_cycles`.

## Operating regimes (C1)

`regime_id` is rounded operational settings. FD001 is one regime. When you later drop FD002/FD004 into the Volume, the same code groups six flight conditions so a high-altitude reading is not treated as degradation.

## Model and error

- Algorithm: scaled linear regression (baseline).
- Validation RMSE (from MLflow): **_____**
- Test RMSE (from scoring job): **_____**
- Test MAE: **_____**

Error is usually larger when true RUL is still high (healthy engines). Short-RUL engines matter more to the planner; use the `action` column (`inspect_now` ≤ 30, `plan_soon` ≤ 60).

## What we would monitor in production (C8)

1. **Prediction drift** — weekly mean `predicted_rul` vs last month.
2. **Feature drift** — regime mix and sensor means vs training (`gold_sensor_selection` + Gold sample).
3. **Data quality** — duplicate `(dataset_id, unit_number, time_in_cycles)`, null ids, empty Bronze (already asserted in Silver).
4. **RMSE gate** — do not register a new champion if validation RMSE is worse than the current champion (`pm-train-model`).
5. **Freshness** — ingest job last success time; no new landing files for N days.

## What is not in this cut

No streaming from aircraft, no LSTM, no real aircraft IDs. NASA `unit_number` is only unique **inside** one FD file + train/test split.
