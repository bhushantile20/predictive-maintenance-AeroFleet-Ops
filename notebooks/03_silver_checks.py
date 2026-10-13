# Databricks notebook source
# MAGIC %md
# MAGIC # Day 2 — Silver checks
# MAGIC Train engines must have RUL. Test engines must not. Last train cycle RUL = 0.

# COMMAND ----------

dbutils.widgets.text("catalog", "pm_dev")
dbutils.widgets.text("schema", "cmapss")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT file_role, COUNT(*) AS rows, COUNT(DISTINCT unit_number) AS engines,
# MAGIC        COUNT(rul) AS rul_not_null, MIN(rul) AS min_rul, MAX(rul) AS max_rul
# MAGIC FROM silver_cycles
# MAGIC GROUP BY file_role

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Last training cycle of each engine should have rul = 0
# MAGIC SELECT dataset_id, unit_number, time_in_cycles, rul
# MAGIC FROM silver_cycles
# MAGIC WHERE file_role = 'train'
# MAGIC   AND time_in_cycles = failure_cycle
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT dataset_id, regime_id, COUNT(*) AS rows
# MAGIC FROM silver_cycles
# MAGIC GROUP BY dataset_id, regime_id
# MAGIC ORDER BY dataset_id, rows DESC
