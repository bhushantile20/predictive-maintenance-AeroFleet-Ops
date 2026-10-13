"""One place for catalog, schema, and paths. Jobs pass these as CLI args from the bundle."""

import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser(description="Predictive maintenance job settings")
    parser.add_argument("--catalog", default=os.environ.get("PM_CATALOG", "pm_dev"))
    parser.add_argument("--schema", default=os.environ.get("PM_SCHEMA", "cmapss"))
    parser.add_argument(
        "--landing-path",
        default=os.environ.get("PM_LANDING_PATH", "/Volumes/pm_dev/cmapss/landing"),
    )
    parser.add_argument(
        "--checkpoint-path",
        default=os.environ.get("PM_CHECKPOINT_PATH", "/Volumes/pm_dev/cmapss/checkpoints"),
    )
    parser.add_argument("--rul-clip", type=int, default=int(os.environ.get("PM_RUL_CLIP", "125")))
    parser.add_argument(
        "--model-name",
        default=os.environ.get("PM_MODEL_NAME", "rul_regressor"),
    )
    parser.add_argument(
        "--mode",
        choices=["batch", "autoloader"],
        default=os.environ.get("PM_INGEST_MODE", "batch"),
        help="batch is easiest on day 1. autoloader is the C6 pattern for later drops.",
    )
    parser.add_argument(
        "--rmse-gate",
        type=float,
        default=float(os.environ.get("PM_RMSE_GATE", "9999")),
        help="Skip register if RMSE is worse than this value or the current champion.",
    )
    return parser.parse_args()


def fq(catalog: str, schema: str, table: str) -> str:
    return f"`{catalog}`.`{schema}`.`{table}`"
