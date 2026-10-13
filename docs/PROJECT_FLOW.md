# Project flow (one page)

```mermaid
flowchart TD
  files["NASA files in Volume<br/>train / test / rul"]
  bronze["Bronze Delta<br/>typed columns + ingest_ts"]
  silver["Silver<br/>RUL clip 125 + regime_id"]
  gold["Gold<br/>kept sensors + rolling means"]
  train["MLflow LinearRegression<br/>register champion"]
  score["Batch score last test cycle"]
  queue["gold_maintenance_queue<br/>inspect_now / plan_soon / ok"]

  files --> bronze --> silver --> gold --> train --> score --> queue
```

| Day | You do | Artifact |
| --- | --- | --- |
| 1 | Upload FD001, run ingest, profile | `bronze_*` |
| 2 | Silver + quality | `silver_cycles` |
| 3 | Gold + GitHub PR | `gold_features` |
| 4 | Train + CI | MLflow run + RMSE |
| 5 | Score + findings + prod approval | planner table + `docs/findings.md` |
