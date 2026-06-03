"""
Train Resource Allocation Prediction models.

Model A — required_developers  : XGBoost Regressor  (uses XGBoost as required by spec)
Model B — estimated_days       : XGBoost Regressor

Run:
    python -m app.ml.train_resource_model
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
import joblib

# ── Load data ─────────────────────────────────────────────────────────────
df = pd.read_csv("app/ml/synthetic_resources.csv")

FEATURES = [
    "project_type",
    "complexity",
    "total_tasks",
    "deadline_days",
    "has_frontend",
    "has_backend",
    "has_ml",
    "has_mobile",
    "has_devops",
    "has_database",
]

X          = df[FEATURES]
y_devs     = df["required_developers"]
y_days     = df["estimated_days"]

# ── Train / test split ────────────────────────────────────────────────────
X_train, X_test, y_devs_train, y_devs_test, y_days_train, y_days_test = train_test_split(
    X, y_devs, y_days, test_size=0.2, random_state=42
)

# ── Model A: Required Developers (XGBoost) ────────────────────────────────
devs_model = XGBRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    random_state=42,
    verbosity=0
)
devs_model.fit(X_train, y_devs_train)

y_pred_devs = devs_model.predict(X_test)
print("=== Required Developers Model (XGBoost) ===")
print(f"MAE : {mean_absolute_error(y_devs_test, y_pred_devs):.2f} developers")
print(f"R²  : {r2_score(y_devs_test, y_pred_devs):.2f}")

joblib.dump(devs_model, "app/ml/resource_devs_model.pkl")
print("Saved → resource_devs_model.pkl")

# ── Model B: Estimated Days (XGBoost) ─────────────────────────────────────
days_model = XGBRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    random_state=42,
    verbosity=0
)
days_model.fit(X_train, y_days_train)

y_pred_days = days_model.predict(X_test)
print("\n=== Estimated Timeline Model (XGBoost) ===")
print(f"MAE : {mean_absolute_error(y_days_test, y_pred_days):.1f} days")
print(f"R²  : {r2_score(y_days_test, y_pred_days):.2f}")

joblib.dump(days_model, "app/ml/resource_days_model.pkl")
print("Saved → resource_days_model.pkl")

print("\n✅ Resource allocation models trained and saved.")
