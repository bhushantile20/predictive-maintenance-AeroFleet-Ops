"""Silver: typed, de-duplicated cycles, RUL labels on train, regime id on every row.

Resolves:
  C1 — regime_id from the 3 operational settings
  C2 — train RUL = clip(failure_cycle - time_in_cycles)
  C3 — test rows keep rul null here; true RUL stays in bronze_rul for scoring only
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from path_setup import add_src_to_path

add_src_to_path()

from pyspark.sql import Window  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from columns import OP_COLS, SENSOR_COLS  # noqa: E402
from settings import fq, parse_args  # noqa: E402
from spark_utils import comment_columns, get_spark  # noqa: E402
from transforms.quality import run_silver_checks  # noqa: E402


def build_silver_train(spark, train_table: str, clip: int):
    t = spark.table(train_table)
    fail_w = Window.partitionBy("dataset_id", "unit_number")
    t = t.withColumn("failure_cycle", F.max("time_in_cycles").over(fail_w))
    t = t.withColumn("rul_raw", F.col("failure_cycle") - F.col("time_in_cycles"))
    t = t.withColumn("rul", F.least(F.col("rul_raw"), F.lit(clip)))
    t = t.withColumn("file_role", F.lit("train"))
    return t


def build_silver_test(spark, test_table: str):
    t = spark.table(test_table)
    t = t.withColumn("failure_cycle", F.lit(None).cast("int"))
    t = t.withColumn("rul_raw", F.lit(None).cast("int"))
    t = t.withColumn("rul", F.lit(None).cast("int"))
    t = t.withColumn("file_role", F.lit("test"))
    return t


def add_regime(df):
    return df.withColumn(
        "regime_id",
        F.concat_ws(
            "|",
            F.format_number(F.round(F.col("op_setting_1"), 0), 0),
            F.format_number(F.round(F.col("op_setting_2"), 2), 2),
            F.format_number(F.round(F.col("op_setting_3"), 0), 0),
        ),
    )


def main() -> None:
    args = parse_args()
    spark = get_spark("pm-silver")

    train_table = fq(args.catalog, args.schema, "bronze_train")
    test_table = fq(args.catalog, args.schema, "bronze_test")
    silver_table = fq(args.catalog, args.schema, "silver_cycles")

    train = add_regime(build_silver_train(spark, train_table, args.rul_clip))
    test = add_regime(build_silver_test(spark, test_table))
    silver = train.unionByName(test)

    key = ["dataset_id", "file_role", "unit_number", "time_in_cycles"]
    silver = silver.dropDuplicates(key).where("unit_number is not null and time_in_cycles > 0")

    (
        silver.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(silver_table)
    )

    comments = {
        "rul": "Remaining useful life in cycles; clipped; train only",
        "rul_raw": "Unclipped remaining useful life (train only)",
        "failure_cycle": "Last cycle in the training trajectory (failure)",
        "regime_id": "Operating regime from rounded op settings (C1)",
        "file_role": "train or test",
        "dataset_id": "FD001-FD004",
        "unit_number": "Engine id inside this file_role + dataset",
        "time_in_cycles": "Cycle number. Do not use this as an ML feature (C3)",
    }
    for col in OP_COLS + SENSOR_COLS:
        comments.setdefault(col, col)
    comment_columns(spark, silver_table, comments)

    stats = run_silver_checks(spark, silver_table)
    print(f"Silver ready: {silver_table} {stats}")


if __name__ == "__main__":
    main()
