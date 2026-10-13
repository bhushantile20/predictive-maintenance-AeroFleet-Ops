# Databricks notebook source
# MAGIC %md
# MAGIC # Day 1 — CMAPSS profile (FD001 first)
# MAGIC Run this after Bronze is loaded. Catalog/schema come from widgets, not hardcoded cells.

# COMMAND ----------

dbutils.widgets.text("catalog", "pm_dev")
dbutils.widgets.text("schema", "cmapss")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'train' AS src, COUNT(*) AS rows, COUNT(DISTINCT unit_number) AS engines, MAX(time_in_cycles) AS max_cycle
# MAGIC FROM bronze_train WHERE dataset_id = 'FD001'
# MAGIC UNION ALL
# MAGIC SELECT 'test', COUNT(*), COUNT(DISTINCT unit_number), MAX(time_in_cycles)
# MAGIC FROM bronze_test WHERE dataset_id = 'FD001'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Constant sensors look like a single value (C4)
# MAGIC SELECT
# MAGIC   COUNT(DISTINCT sensor_1) AS sensor_1_nunique,
# MAGIC   COUNT(DISTINCT sensor_5) AS sensor_5_nunique,
# MAGIC   COUNT(DISTINCT sensor_6) AS sensor_6_nunique,
# MAGIC   COUNT(DISTINCT sensor_2) AS sensor_2_nunique,
# MAGIC   COUNT(DISTINCT op_setting_3) AS op3_nunique
# MAGIC FROM bronze_train
# MAGIC WHERE dataset_id = 'FD001'

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT unit_number, MAX(time_in_cycles) AS failure_cycle
# MAGIC FROM bronze_train
# MAGIC WHERE dataset_id = 'FD001'
# MAGIC GROUP BY unit_number
# MAGIC ORDER BY unit_number
# MAGIC LIMIT 20
