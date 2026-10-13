# BRD restated + assumptions

Read this before you change code. This is the “clarify requirements” step from the BRD.

## What AeroFleet Ops asked for (in plain words)

Unplanned engine failures are expensive. Today they either wait for a failure or service on a calendar. We build a **batch** Databricks pipeline that:

1. Loads NASA C-MAPSS engine sensor files as-is (Bronze).
2. Cleans keys, adds Remaining Useful Life (RUL) on **training** engines, and tags the flight condition (Silver).
3. Builds a simple feature table (Gold).
4. Trains a **linear regression** to predict RUL, logs it in MLflow, registers the best one.
5. Scores each **test** engine on its **last** observed cycle and writes a planner table: inspect now / plan soon / ok.

## Data we use

NASA C-MAPSS (FD001–FD004). Start with **FD001**. Add FD002–FD004 later as extra files in the same Volume folders (challenge C6).

| File | Meaning |
| --- | --- |
| `train_FD00x.txt` | Engines run until failure. Last cycle = failure. |
| `test_FD00x.txt` | Engines stop **before** failure. |
| `RUL_FD00x.txt` | One true RUL per test engine, **same row order** as unit 1, 2, 3… |

Each train/test row: engine id, cycle, 3 operating settings, 21 sensors. No header row. Spaces separate columns.

## Assumptions (write these in your findings if you keep them)

| ID | Assumption | Why |
| --- | --- | --- |
| A1 | RUL on train = `failure_cycle - time_in_cycles`, then **clip at 125**. | Healthy engines look similar; huge RUL labels add noise. Common C-MAPSS practice. |
| A2 | Test RUL is **never** used as a training feature. It is only for the score-card RMSE. | Production would not have the answer. |
| A3 | We score the **last cycle** of each test engine only. | That is the moment a planner would ask “how long is left?” |
| A4 | `time_in_cycles` is **not** a model feature. | Test engines are right-censored (C3). Cycle count would leak “how long we already watched.” |
| A5 | Operating regime = rounded `(op1, op2, op3)`, not a clustering model. | FD001 is one condition; FD002/FD004 have six. Rounding is enough. |
| A6 | Drop sensors whose **train** standard deviation is ~0. | They do not change; they cannot predict degradation (C4). |
| A7 | Sensor values are **minus the train mean of that regime**. | Stops “different flight condition” looking like “broken engine” (C1). |
| A8 | Train/val split is by **engine id**, 80/20, not by row. | Random row split leaks the future of the same engine into validation. |
| A9 | Model is LinearRegression + StandardScaler. | BRD asks for a baseline, not LSTM. Dataset is small (C5). |
| A10 | Catalog/schema/paths come from job parameters (`databricks.yml`), never from notebook hardcoding. | Guardrails + BRD §12. |

## Questions you could still ask a BA (good to list in the write-up)

- What RUL threshold means “ground the aircraft” vs “inspect at next night stop”? We used 30 / 60 as a starting point.
- Should FD001–FD004 be one model or one model per fleet family? We train one model on whatever is in Gold.
- Who is allowed to create the Unity Catalog catalog `pm_dev`? If you cannot, use a catalog your admin already gave you and put that name in `databricks.yml`.
