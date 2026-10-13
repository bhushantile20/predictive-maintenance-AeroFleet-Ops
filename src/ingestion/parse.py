"""Turn space-separated CMAPSS text into typed columns. No cleaning beyond types."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from columns import TRAIN_TEST_NAMES


def with_ingest_meta(df: DataFrame) -> DataFrame:
    path = F.col("_source_file")
    return (
        df.withColumn("ingest_ts", F.current_timestamp())
        .withColumn("source_file", path)
        .withColumn("dataset_id", F.upper(F.regexp_extract(path, r"(FD00[1-4])", 1)))
    )


def parse_train_test(raw_text_df: DataFrame) -> DataFrame:
    """raw_text_df must have columns: value, _source_file."""
    parts = F.split(F.trim(F.col("value")), r"\s+")
    parsed = raw_text_df
    for i, name in enumerate(TRAIN_TEST_NAMES):
        parsed = parsed.withColumn(name, parts.getItem(i))

    parsed = with_ingest_meta(parsed).drop("value")

    int_cols = ["unit_number", "time_in_cycles"]
    double_cols = [c for c in TRAIN_TEST_NAMES if c not in int_cols]
    for col in int_cols:
        parsed = parsed.withColumn(col, F.col(col).cast("int"))
    for col in double_cols:
        parsed = parsed.withColumn(col, F.col(col).cast("double"))
    return parsed.where(F.col("unit_number").isNotNull())
