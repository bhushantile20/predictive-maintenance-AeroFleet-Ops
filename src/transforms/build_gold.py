"""Gold: model-ready features.

C3 — time_in_cycles is NOT a model feature.
C4 — drop sensors with almost no variance on the training set.
C1 — sensors are centered by operating regime so flight condition is not
     mistaken for degradation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from path_setup import add_src_to_path

add_src_to_path()

from pyspark.sql import Window  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from columns import SENSOR_COLS  # noqa: E402
from settings import fq, parse_args  # noqa: E402
from spark_utils import comment_columns, get_spark  # noqa: E402
from transforms.features import keep_sensors, low_variance_sensors  # noqa: E402


def sensor_stds(df) -> dict:
    agg = df.agg(*[F.stddev(c).alias(c) for c in SENSOR_COLS]).collect()[0]
    return {c: agg[c] for c in SENSOR_COLS}


def main() -> None:
    args = parse_args()
    spark = get_spark("pm-gold")

    silver_table = fq(args.catalog, args.schema, "silver_cycles")
    gold_table = fq(args.catalog, args.schema, "gold_features")
    sensor_table = fq(args.catalog, args.schema, "gold_sensor_selection")

    silver = spark.table(silver_table)
    train = silver.where("file_role = 'train'")
    stds = sensor_stds(train)
    kept = keep_sensors(stds)
    dropped = low_variance_sensors(stds)

    sel_rows = [(k, float(stds[k] or 0.0), k in kept) for k in SENSOR_COLS]
    spark.createDataFrame(sel_rows, ["sensor", "train_stddev", "kept"]).write.format(
        "delta"
    ).mode("overwrite").option("overwriteSchema", "true").saveAsTable(sensor_table)

    # Regime mean from TRAIN only, then apply to train and test (no test leakage).
    regime_means = train.groupBy("dataset_id", "regime_id").agg(
        *[F.avg(c).alias(f"{c}_regime_mean") for c in kept]
    )
    featured = silver.join(regime_means, ["dataset_id", "regime_id"], "left")

    for c in kept:
        featured = featured.withColumn(f"{c}_norm", F.col(c) - F.col(f"{c}_regime_mean"))

    engine_w = Window.partitionBy("dataset_id", "file_role", "unit_number").orderBy(
        "time_in_cycles"
    )
    w5 = engine_w.rowsBetween(-4, 0)
    w20 = engine_w.rowsBetween(-19, 0)
    for c in kept:
        n = f"{c}_norm"
        featured = featured.withColumn(f"{n}_mean5", F.avg(n).over(w5))
        featured = featured.withColumn(f"{n}_mean20", F.avg(n).over(w20))

    # Split training engines 80/20 by unit, never by row (time-series leak).
    featured = featured.withColumn(
        "split",
        F.when(F.col("file_role") == "test", F.lit("test"))
        .when(
            F.pmod(F.hash(F.concat_ws("|", F.col("dataset_id"), F.col("unit_number"))), 10) < 8,
            F.lit("train"),
        )
        .otherwise(F.lit("val")),
    )

    keep_cols = (
        [
            "dataset_id",
            "file_role",
            "unit_number",
            "time_in_cycles",
            "regime_id",
            "split",
            "rul",
        ]
        + kept
        + [f"{c}_norm" for c in kept]
        + [f"{c}_norm_mean5" for c in kept]
        + [f"{c}_norm_mean20" for c in kept]
    )
    gold = featured.select(*keep_cols)

    gold.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        gold_table
    )

    comment_columns(
        spark,
        gold_table,
        {
            "split": "train / val / test. test = CMAPSS test files, not a random row split",
            "rul": "Label for train/val. Null on test rows",
            "regime_id": "Operating regime used to normalize sensors",
            "time_in_cycles": "Kept for joining only. Do not train on this column (C3)",
        },
    )
    print(f"Gold ready: {gold_table}")
    print(f"Kept sensors ({len(kept)}): {kept}")
    print(f"Dropped constant sensors: {dropped}")


if __name__ == "__main__":
    main()
