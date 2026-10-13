"""Train a simple linear model, log it with MLflow, register in Unity Catalog.

Small data on purpose (BRD C5): pull Gold to pandas and use scikit-learn.
Do not use time_in_cycles as a feature (BRD C3).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from path_setup import add_src_to_path

add_src_to_path()

import mlflow  # noqa: E402
import mlflow.sklearn  # noqa: E402
import numpy as np  # noqa: E402
from mlflow.models import infer_signature  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from settings import fq, parse_args  # noqa: E402
from spark_utils import get_spark  # noqa: E402


ID_COLS = ["dataset_id", "file_role", "unit_number", "time_in_cycles", "regime_id", "split", "rul"]


def feature_cols(pdf) -> list[str]:
    blocked = set(ID_COLS)
    return [c for c in pdf.columns if c not in blocked]


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.array(y_true) - np.array(y_pred)) ** 2)))


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))


def main() -> None:
    args = parse_args()
    spark = get_spark("pm-train")

    gold_table = fq(args.catalog, args.schema, "gold_features")
    pdf = spark.table(gold_table).where("file_role = 'train'").toPandas()
    cols = feature_cols(pdf)

    train = pdf[pdf["split"] == "train"]
    val = pdf[pdf["split"] == "val"]
    x_train, y_train = train[cols], train["rul"]
    x_val, y_val = val[cols], val["rul"]

    model_name = f"{args.catalog}.{args.schema}.{args.model_name}"
    experiment_name = f"/Shared/pm-rul-{args.catalog}"

    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(experiment_name)

    pipe = Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )

    with mlflow.start_run(run_name="linear-rul") as run:
        pipe.fit(x_train, y_train)
        pred_val = pipe.predict(x_val)
        val_rmse = rmse(y_val, pred_val)
        val_mae = mae(y_val, pred_val)

        mlflow.log_param("algorithm", "LinearRegression")
        mlflow.log_param("rul_clip", args.rul_clip)
        mlflow.log_param("n_features", len(cols))
        mlflow.log_param("features", ",".join(cols))
        mlflow.log_metric("val_rmse", val_rmse)
        mlflow.log_metric("val_mae", val_mae)
        mlflow.log_metric("val_rows", float(len(val)))
        mlflow.log_metric("train_rows", float(len(train)))

        signature = infer_signature(x_train, pipe.predict(x_train))
        mlflow.sklearn.log_model(pipe, artifact_path="model", signature=signature)

        print(f"Validation RMSE={val_rmse:.3f} MAE={val_mae:.3f}")

        promote = val_rmse <= args.rmse_gate
        champion_rmse = None
        client = mlflow.tracking.MlflowClient()
        try:
            champ = client.get_model_version_by_alias(model_name, "champion")
            champ_run = client.get_run(champ.run_id)
            champion_rmse = champ_run.data.metrics.get("val_rmse")
            if champion_rmse is not None and val_rmse > champion_rmse:
                promote = False
                print(
                    f"RMSE {val_rmse:.3f} worse than champion {champion_rmse:.3f}. Skip register."
                )
        except Exception:
            print("No champion yet. This run can be registered.")

        if not promote:
            print("Model logged but not registered (gate failed).")
            return

        mv = mlflow.register_model(f"runs:/{run.info.run_id}/model", model_name)
        client.set_registered_model_alias(model_name, "champion", mv.version)
        print(f"Registered {model_name} version {mv.version} as champion")


if __name__ == "__main__":
    main()
