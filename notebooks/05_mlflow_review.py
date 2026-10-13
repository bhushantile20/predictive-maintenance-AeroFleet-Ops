# Databricks notebook source
# MAGIC %md
# MAGIC # Day 4–5 — Model and planner output
# MAGIC After pm-train-model and pm-batch-score.

# COMMAND ----------

dbutils.widgets.text("catalog", "pm_dev")
dbutils.widgets.text("schema", "cmapss")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT action, COUNT(*) AS engines, ROUND(AVG(predicted_rul), 1) AS avg_pred
# MAGIC FROM gold_maintenance_queue
# MAGIC GROUP BY action

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT dataset_id, unit_number, ROUND(predicted_rul, 1) AS predicted_rul, true_rul, action
# MAGIC FROM gold_maintenance_queue
# MAGIC ORDER BY predicted_rul ASC
# MAGIC LIMIT 25

# COMMAND ----------

# MAGIC %md
# MAGIC Open MLflow: experiment `/Shared/pm-rul-pm_dev`. Model name `catalog.schema.rul_regressor`, alias `champion`.
