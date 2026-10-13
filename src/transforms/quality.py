"""Data quality checks run after Silver is written (BRD success criteria)."""

from pyspark.sql import SparkSession


def run_silver_checks(spark: SparkSession, silver_table: str) -> dict:
    df = spark.table(silver_table)
    row_count = df.count()
    if row_count == 0:
        raise ValueError(f"{silver_table} is empty")

    nulls = df.filter("unit_number is null or time_in_cycles is null").count()
    if nulls > 0:
        raise ValueError(f"{silver_table} has {nulls} rows with null ids")

    dupes = (
        df.groupBy("dataset_id", "file_role", "unit_number", "time_in_cycles")
        .count()
        .filter("count > 1")
        .count()
    )
    if dupes > 0:
        raise ValueError(f"{silver_table} has {dupes} duplicate cycle keys")

    bad_cycle = df.filter("time_in_cycles <= 0").count()
    if bad_cycle > 0:
        raise ValueError(f"{silver_table} has {bad_cycle} non-positive cycles")

    train_neg_rul = df.filter("file_role = 'train' and rul < 0").count()
    if train_neg_rul > 0:
        raise ValueError("Training RUL must be >= 0")

    return {"row_count": row_count, "duplicate_keys": dupes, "null_ids": nulls}
