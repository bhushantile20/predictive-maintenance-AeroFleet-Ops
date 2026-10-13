# Databricks notebook source
# MAGIC %md
# MAGIC # Maintenance planner view
# MAGIC Simple table: which engines to inspect soon. This is the stakeholder output, not raw model dumps.

# COMMAND ----------

dbutils.widgets.text("catalog", "pm_dev")
dbutils.widgets.text("schema", "cmapss")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   dataset_id,
# MAGIC   unit_number,
# MAGIC   ROUND(predicted_rul, 1) AS predicted_rul,
# MAGIC   true_rul,
# MAGIC   ROUND(abs_error, 1) AS abs_error,
# MAGIC   action
# MAGIC FROM gold_maintenance_queue
# MAGIC ORDER BY predicted_rul ASC
