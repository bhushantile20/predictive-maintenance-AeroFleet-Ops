# Changelog

## 0.1.0 — training exercise

- Bronze ingestion for NASA C-MAPSS train / test / RUL files.
- Silver RUL labels (clipped linear) and operating-regime id.
- Gold features: drop constant sensors, regime-normalize, rolling means.
- Linear regression baseline in MLflow, Unity Catalog registry, batch scoring.
- GitHub CI (lint, tests, bundle validate) and gated prod deploy.
