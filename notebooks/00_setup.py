# Databricks notebook source
# MAGIC %md
# MAGIC # Day 1 — Create catalog objects
# MAGIC Run once. Widgets keep catalog names out of the code.

# COMMAND ----------

dbutils.widgets.text("catalog", "pm_dev")
dbutils.widgets.text("schema", "cmapss")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`landing`")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`checkpoints`")

print("Create these folders in the landing Volume, then upload the NASA files:")
print(f"  /Volumes/{catalog}/{schema}/landing/train/train_FD001.txt")
print(f"  /Volumes/{catalog}/{schema}/landing/test/test_FD001.txt")
print(f"  /Volumes/{catalog}/{schema}/landing/rul/RUL_FD001.txt")
