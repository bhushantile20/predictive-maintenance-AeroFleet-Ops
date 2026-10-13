# Predictive Maintenance Analytics Platform

Training exercise for **AeroFleet Ops**: NASA C-MAPSS turbofan data → Databricks medallion tables → RUL model → maintenance planner queue.

[![CI](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_ORG/YOUR_REPO/actions/workflows/ci.yml)

## Project flow (read this first)

```
NASA txt files
      │  upload to Unity Catalog Volume
      ▼
 BRONZE   bronze_train, bronze_test, bronze_rul     (raw, typed only)
      │  RUL labels + regime_id + quality checks
      ▼
 SILVER   silver_cycles
      │  drop constant sensors, regime-normalize, rolling means
      ▼
 GOLD     gold_features, gold_sensor_selection
      │  LinearRegression + MLflow + UC Model Registry
      ▼
 ML       model: pm_dev.cmapss.rul_regressor @ champion
      │  score last cycle of each test engine
      ▼
 OUTPUT   gold_predictions, gold_maintenance_queue
```

Jobs (Databricks Asset Bundle):

1. `pm-ingest-bronze`
2. `pm-transform-silver-gold`
3. `pm-train-model`
4. `pm-batch-score`
5. `pm-end-to-end` (all of the above, in order)

Catalogs: **dev** = `pm_dev`, **prod** = `pm_prod`. Same code. Names come from `databricks.yml`, not from notebooks.

---

## What you do, in order (5 days)

Do **not** start with GitHub Actions. Get Bronze working on FD001 first (guardrails Phase 1).

### Day 1 — laptop + Databricks + Bronze (FD001 only)

1. Create a GitHub repo (empty). Clone it, copy **this whole folder** into it.
2. Install Python 3.11 locally. In this folder:

   ```text
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-dev.txt
   pytest tests/ -v
   ```

3. In Databricks, create (or ask an admin for) catalog `pm_dev` and a cluster on **ML runtime 15.4**.
4. Edit **only** `databricks.yml`:
   - `targets.dev.workspace.host` = your workspace URL
   - `node_type_id` = your cloud’s small VM (`i3.xlarge` on AWS, `Standard_DS3_v2` on Azure)
5. Install [Databricks CLI](https://docs.databricks.com/dev-tools/cli/databricks-cli.html), run `databricks auth login`, then:

   ```text
   databricks bundle validate -t dev
   databricks bundle deploy -t dev
   ```

6. Put NASA files on the Volume (see `data/README.md`). Start with:

   - `train_FD001.txt`
   - `test_FD001.txt`
   - `RUL_FD001.txt`

   Paths:

   ```text
   /Volumes/pm_dev/cmapss/landing/train/train_FD001.txt
   /Volumes/pm_dev/cmapss/landing/test/test_FD001.txt
   /Volumes/pm_dev/cmapss/landing/rul/RUL_FD001.txt
   ```

7. Run job **pm-ingest-bronze**. Confirm row counts in notebook `notebooks/01_profile.py`.

### Day 2 — Silver (C1, C2, C3)

8. Run job **pm-transform-silver-gold** (or only the silver task if you run tasks by hand).
9. Read `docs/assumptions.md`. Open `notebooks/03_silver_checks.py`.
10. Check: train `rul` is 0 on the last cycle of each engine; test `rul` is null.

### Day 3 — Gold + GitHub habits

11. Confirm `gold_sensor_selection` and `notebooks/04_gold_sensors.py`.
12. Create branch `feature/bronze-ingestion` (later: one branch per change). Open a PR using `.github/pull_request_template.md`.
13. Protect `main` (PR required). Never put tokens in git.

### Day 4 — Train + CI

14. Run **pm-train-model**. Open MLflow experiment `/Shared/pm-rul-pm_dev`. Copy validation RMSE into `docs/findings.md`.
15. Add GitHub secrets: `DATABRICKS_HOST`, `DATABRICKS_TOKEN`. CI on every PR: ruff, pytest, `databricks bundle validate -t dev`.

### Day 5 — Score, register, prod gate

16. Run **pm-batch-score**. Open `notebooks/02_planner_queue.py`. Finish `docs/findings.md`.
17. Add GitHub Environment named **production** (this is the approval click). Secrets: `DATABRICKS_PROD_HOST`, `DATABRICKS_PROD_TOKEN`. Merge to `main` deploys **dev**. Prod job waits for approval.
18. Optional: copy FD002–FD004 into the same three landing folders, set `ingest_mode: autoloader` in `databricks.yml`, re-run ingest.

---

## Where each file lives

| Path | Why it is there |
| --- | --- |
| `databricks.yml` | Bundle: hosts, catalog, Volume paths, `dev` / `prod` |
| `resources/jobs.yml` | The four jobs + end-to-end job |
| `resources/pipelines.yml` | Empty on purpose (no DLT; data is small) |
| `src/settings.py` | Catalog, schema, clip=125 — **one place** |
| `src/columns.py` | 3 settings + 21 sensor names |
| `src/ingestion/parse.py` | Split space-separated NASA lines |
| `src/ingestion/load_bronze.py` | **Put NASA files → Bronze tables** |
| `src/transforms/rul.py` | RUL math (unit-tested, no Spark) |
| `src/transforms/features.py` | Drop constant sensors + regime key |
| `src/transforms/quality.py` | Silver assertions |
| `src/transforms/build_silver.py` | **Bronze → silver_cycles** |
| `src/transforms/build_gold.py` | **Silver → gold_features** |
| `src/ml/train.py` | **Fit model, MLflow, register champion** |
| `src/ml/score.py` | **Batch score + planner queue** |
| `tests/` | pytest for RUL and sensor drop |
| `notebooks/` | Profile + planner SQL only (no hardcoded catalogs) |
| `sql/planner_queue.sql` | Same planner query for a SQL warehouse |
| `docs/assumptions.md` | BRD in our words |
| `docs/findings.md` | 1-page stakeholder note |
| `.github/workflows/ci.yml` | PR: lint, test, bundle validate |
| `.github/workflows/deploy.yml` | `main` → dev; prod needs approval |
| `data/raw/` | Local copy of NASA files (not committed) |

Do **not** put catalog names or Volume paths inside `src/` functions. Pass `--catalog` from the job (already wired in `jobs.yml`).

---

## Local commands (no Spark)

```text
ruff check src/ tests/
pytest tests/ -v
```

## Databricks commands

```text
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run pm_ingest -t dev
databricks bundle run pm_transform -t dev
databricks bundle run pm_train -t dev
databricks bundle run pm_score -t dev
```

Or one go: `databricks bundle run pm_e2e -t dev`

---

## Tables you should see in `pm_dev.cmapss`

| Table | Layer |
| --- | --- |
| `bronze_train` | Bronze |
| `bronze_test` | Bronze |
| `bronze_rul` | Bronze |
| `silver_cycles` | Silver |
| `gold_features` | Gold |
| `gold_sensor_selection` | Gold |
| `gold_predictions` | ML output |
| `gold_maintenance_queue` | Planner |

Registered model: `pm_dev.cmapss.rul_regressor` alias `champion`.

---

## How we handled BRD challenges

| ID | Approach in this repo |
| --- | --- |
| C1 Hidden regimes | `regime_id` + subtract train regime mean |
| C2 No RUL in raw train | Last cycle = failure; clip 125 |
| C3 Right-censored test | No `time_in_cycles` in the model; true RUL only at score time |
| C4 Noisy sensors | Drop near-zero stddev on train |
| C5 Small data | Single-node job cluster; pandas + sklearn for ML |
| C6 Incremental FD00x | Same folders; `ingest_mode=autoloader` when you are ready |
| C7 Governance | UC catalog/schema, Volume, column comments |
| C8 Model lifecycle | MLflow + registry + RMSE gate + batch score job |

---

## Secrets (never in git)

| Place | What |
| --- | --- |
| GitHub Actions | `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, prod pair |
| Databricks | none needed for this NASA dump |

Rotate the token when the exercise ends.
