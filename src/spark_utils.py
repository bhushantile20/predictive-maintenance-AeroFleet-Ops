"""Spark helpers shared by jobs."""

from pyspark.sql import SparkSession


def get_spark(app_name: str) -> SparkSession:
    return SparkSession.builder.appName(app_name).getOrCreate()


def comment_columns(spark: SparkSession, full_table: str, comments: dict) -> None:
    for col, text in comments.items():
        safe = text.replace("'", "\\'")
        spark.sql(f"ALTER TABLE {full_table} ALTER COLUMN {col} COMMENT '{safe}'")
