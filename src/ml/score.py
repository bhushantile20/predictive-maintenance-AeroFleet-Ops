"""Batch score the last cycle of each test engine. Write planner-friendly tables."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from path_setup import add_src_to_path

add_src_to_path()

import mlflow  # noqa: E402
import numpy as np  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

from settings import fq, parse_args  # noqa: E402
from spark_utils import comment_columns, get_spark  # noqa: E402

ID_COLS = ["dataset_id", "file_role", "unit_number", "time_in_cycles", "regime_id", "split", "rul"]


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.array(y_true) - np.array(y_pred)) ** 2)))


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))


def main() -> None:
    args = parse_args()
    spark = get_spark("pm-score")

    gold_table = fq(args.catalog, args.schema, "gold_features")
    rul_table = fq(args.catalog, args.schema, "bronze_rul")
    pred_table = fq(args.catalog, args.schema, "gold_predictions")
    queue_table = fq(args.catalog, args.schema, "gold_maintenance_queue")
    model_name = f"{args.catalog}.{args.schema}.{args.model_name}"

    gold = spark.table(gold_table).where("file_role = 'test'")
    last_cycle = gold.groupBy("dataset_id", "unit_number").agg(
        F.max("time_in_cycles").alias("time_in_cycles")
    )
    score_df = gold.join(last_cycle, ["dataset_id", "unit_number", "time_in_cycles"], "inner")
    pdf = score_df.toPandas()

    feature_cols = [c for c in pdf.columns if c not in ID_COLS]
    mlflow.set_registry_uri("databricks-uc")
    model = mlflow.sklearn.load_model(f"models:/{model_name}@champion")
    pdf["predicted_rul"] = model.predict(pdf[feature_cols])
    pdf["predicted_rul"] = pdf["predicted_rul"].clip(lower=0)

    true_rul = spark.table(rul_table).select(
        "dataset_id", "unit_number", F.col("rul").alias("true_rul")
    )
    pred = spark.createDataFrame(
        pdf[["dataset_id", "unit_number", "time_in_cycles", "predicted_rul"]]
    )
    pred = pred.join(true_rul, ["dataset_id", "unit_number"], "left")
    pred = pred.withColumn("abs_error", F.abs(F.col("predicted_rul") - F.col("true_rul")))
    pred = pred.withColumn(
        "action",
        F.when(F.col("predicted_rul") <= 30, F.lit("inspect_now"))
        .when(F.col("predicted_rul") <= 60, F.lit("plan_soon"))
        .otherwise(F.lit("ok")),
    )

    pred.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        pred_table
    )

    queue = pred.select(
        "dataset_id",
        "unit_number",
        "time_in_cycles",
        "predicted_rul",
        "true_rul",
        "abs_error",
        "action",
    ).orderBy("predicted_rul")
    queue.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
        queue_table
    )

    comment_columns(
        spark,
        pred_table,
        {
            "predicted_rul": "Model estimate of remaining cycles",
            "true_rul": "NASA ground truth (evaluation only, not available in production)",
            "action": "inspect_now (<=30), plan_soon (<=60), ok",
        },
    )

    scored = pred.where("true_rul is not null").toPandas()
    if len(scored) > 0:
        print(f"Test RMSE={rmse(scored['true_rul'], scored['predicted_rul']):.3f}")
        print(f"Test MAE={mae(scored['true_rul'], scored['predicted_rul']):.3f}")
        print(scored["abs_error"].describe())

    print("Planner queue (lowest predicted RUL first):")
    spark.table(queue_table).show(20, truncate=False)


if __name__ == "__main__":
    main()
