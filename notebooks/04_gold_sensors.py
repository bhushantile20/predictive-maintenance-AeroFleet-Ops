# Databricks notebook source
# MAGIC %md
# MAGIC # Day 3 — Which sensors we kept
# MAGIC Constant sensors are dropped. Copy this list into docs/findings.md.

# COMMAND ----------

dbutils.widgets.text("catalog", "pm_dev")
dbutils.widgets.text("schema", "cmapss")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT sensor, ROUND(train_stddev, 6) AS train_stddev, kept
# MAGIC FROM gold_sensor_selection
# MAGIC ORDER BY kept, sensor

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT split, COUNT(*) AS rows, COUNT(DISTINCT unit_number) AS engines
# MAGIC FROM gold_features
# MAGIC GROUP BY split
