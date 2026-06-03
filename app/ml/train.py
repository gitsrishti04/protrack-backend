import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error
import joblib

## we have to load the csv
df = pd.read_csv("app/ml/synthetic_completion.csv")

## define the features and targets
FEATURES = [
    "total_tasks",
    "completed_tasks",
    "delayed_tasks",
    "team_size",
    "completion_pct",
    "task_completion_rate",
    "delayed_task_rate"
]

X = df[FEATURES]
y_delay = df["is_delayed"]        # for classifier
y_days  = df["days_remaining"]    # for regressor

## we have to Train/test split — do it once, use for both models:

X_train, X_test, y_delay_train, y_delay_test, y_days_train, y_days_test = train_test_split(
    X, y_delay, y_days, test_size=0.2, random_state=42
)

## now model A delay risk classifier
delay_model = RandomForestClassifier(n_estimators=100, random_state=42)
delay_model.fit(X_train, y_delay_train)

y_pred_delay = delay_model.predict(X_test)
print("=== Delay Risk Classifier ===")
print(f"Accuracy : {accuracy_score(y_delay_test, y_pred_delay):.2f}")
print(f"F1 Score : {f1_score(y_delay_test, y_pred_delay):.2f}")

joblib.dump(delay_model, "app/ml/delay_model.pkl")
print("Saved → delay_model.pkl")

## Model B — Days Remaining Regressor:


completion_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
completion_model.fit(X_train, y_days_train)

y_pred_days = completion_model.predict(X_test)
print("\n=== Completion Time Regressor ===")
print(f"MAE : {mean_absolute_error(y_days_test, y_pred_days):.1f} days")

joblib.dump(completion_model, "app/ml/completion_model.pkl")
print("Saved → completion_model.pkl")


