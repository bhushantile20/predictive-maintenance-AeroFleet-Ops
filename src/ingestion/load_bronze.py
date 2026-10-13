"""Bronze load. Raw files in, typed Delta tables out. No business cleaning here.

Landing folder (Unity Catalog Volume):
  /Volumes/<catalog>/cmapss/landing/train/train_FD001.txt
  /Volumes/<catalog>/cmapss/landing/test/test_FD001.txt
  /Volumes/<catalog>/cmapss/landing/rul/RUL_FD001.txt

Later drops: add train_FD002.txt (and test/RUL) into the same folders.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from path_setup import add_src_to_path

add_src_to_path()

import glob  # noqa: E402

import pandas as pd  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from columns import SENSOR_COMMENTS, TRAIN_TEST_NAMES  # noqa: E402
from ingestion.parse import parse_train_test, with_ingest_meta  # noqa: E402
from settings import fq, parse_args  # noqa: E402
from spark_utils import comment_columns, get_spark  # noqa: E402


def ensure_objects(spark, catalog: str, schema: str) -> None:
    spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`landing`")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.`{schema}`.`checkpoints`")


def read_text_batch(spark, path: str):
    return spark.read.text(path).withColumn("_source_file", F.input_file_name())


def read_text_autoloader(spark, path: str, checkpoint: str):
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "text")
        .option("cloudFiles.schemaLocation", checkpoint + "/schema")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(path)
        .withColumn("_source_file", F.col("_metadata.file_path"))
    )


def write_autoloader(df, table: str, checkpoint: str) -> None:
    (
        df.writeStream.format("delta")
        .option("checkpointLocation", checkpoint)
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .toTable(table)
        .awaitTermination()
    )


def overwrite_table(df, table: str) -> None:
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)


def load_rul_preserving_order(spark, rul_path: str):
    """RUL files are one number per line in unit order. Pandas keeps that order."""
    files = sorted(glob.glob(rul_path.rstrip("/") + "/*"))
    if not files:
        raise FileNotFoundError(f"No RUL files under {rul_path}")
    frames = []
    for path in files:
        pdf = pd.read_csv(path, header=None, names=["rul"], sep=r"\s+")
        pdf["unit_number"] = range(1, len(pdf) + 1)
        pdf["_source_file"] = path
        frames.append(pdf)
    df = spark.createDataFrame(pd.concat(frames, ignore_index=True))
    return with_ingest_meta(df).drop("_source_file")


def bronze_comments() -> dict:
    comments = {
        "unit_number": "Engine id inside this FD00x file (train unit 1 is not test unit 1)",
        "time_in_cycles": "Operating cycle since start of this trajectory",
        "op_setting_1": "Operational setting 1 (altitude-related)",
        "op_setting_2": "Operational setting 2 (Mach-related)",
        "op_setting_3": "Operational setting 3 (throttle-resolver angle)",
        "dataset_id": "FD001, FD002, FD003, or FD004",
        "source_file": "Volume path of the ingested file",
        "ingest_ts": "When this row was loaded into Bronze",
        "rul": "Ground-truth remaining useful life for a test engine (RUL file only)",
        "file_role": "train, test, or rul",
    }
    comments.update(SENSOR_COMMENTS)
    return comments


def main() -> None:
    args = parse_args()
    spark = get_spark("pm-bronze")
    ensure_objects(spark, args.catalog, args.schema)

    landing = args.landing_path.rstrip("/")
    ckpt = args.checkpoint_path.rstrip("/")

    train_path = f"{landing}/train/"
    test_path = f"{landing}/test/"
    rul_path = f"{landing}/rul/"

    train_table = fq(args.catalog, args.schema, "bronze_train")
    test_table = fq(args.catalog, args.schema, "bronze_test")
    rul_table = fq(args.catalog, args.schema, "bronze_rul")

    if args.mode == "autoloader":
        raw_train = read_text_autoloader(spark, train_path, f"{ckpt}/train")
        raw_test = read_text_autoloader(spark, test_path, f"{ckpt}/test")
        write_autoloader(parse_train_test(raw_train), train_table, f"{ckpt}/train_out")
        write_autoloader(parse_train_test(raw_test), test_table, f"{ckpt}/test_out")
        overwrite_table(load_rul_preserving_order(spark, rul_path), rul_table)
    else:
        train_df = parse_train_test(read_text_batch(spark, train_path))
        test_df = parse_train_test(read_text_batch(spark, test_path))
        rul_df = load_rul_preserving_order(spark, rul_path)
        overwrite_table(train_df, train_table)
        overwrite_table(test_df, test_table)
        overwrite_table(rul_df, rul_table)

    for table in (train_table, test_table):
        comment_columns(
            spark,
            table,
            {k: v for k, v in bronze_comments().items() if k in TRAIN_TEST_NAMES or k in {
                "dataset_id", "source_file", "ingest_ts"
            }},
        )
    comment_columns(
        spark,
        rul_table,
        {
            "unit_number": bronze_comments()["unit_number"],
            "rul": bronze_comments()["rul"],
            "dataset_id": bronze_comments()["dataset_id"],
            "source_file": bronze_comments()["source_file"],
            "ingest_ts": bronze_comments()["ingest_ts"],
        },
    )

    print("Bronze tables ready:")
    for name in (train_table, test_table, rul_table):
        print(f"  {name}: {spark.table(name).count()} rows")


if __name__ == "__main__":
    main()
