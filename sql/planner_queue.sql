-- Maintenance planner output. Run in a Databricks SQL warehouse after scoring.
SELECT
  dataset_id,
  unit_number,
  ROUND(predicted_rul, 1) AS predicted_rul,
  true_rul,
  action
FROM ${catalog}.${schema}.gold_maintenance_queue
ORDER BY predicted_rul ASC;
