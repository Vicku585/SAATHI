from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import (
    GridSearchCV,
    train_test_split,
)


# =========================================================
# SENTINELS - V3 Tuned Risk Model
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "expanded_dataset_v2.csv"
MODEL_PATH = BASE_DIR / "risk_model_v3.pkl"


# =========================================================
# Features
# =========================================================

FEATURE_COLUMNS = [
    # Wellness
    "phq9_score",
    "gad7_score",
    "sleep_hours",
    "heart_rate",
    "hrv",

    # Operational / HR
    "days_since_last_leave",
    "deployment_days",
    "duty_hours_per_week",
    "night_duties",
    "consecutive_duty_days",
    "recent_transfer_count",
    "training_days",
    "family_separation_days",

    # Behavioral / recovery
    "leave_utilization_gap",
    "workload_trend",
    "recovery_gap",
]

TARGET_COLUMN = "risk_level"


# =========================================================
# Load dataset
# =========================================================

print("\n========================================")
print(" SENTINELS - V3 MODEL TUNING")
print("========================================\n")

print("Loading Dataset V2...")

data = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")
print(f"Rows    : {len(data)}")
print(f"Columns : {len(data.columns)}")


# =========================================================
# Validate dataset
# =========================================================

required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

missing_columns = [
    column
    for column in required_columns
    if column not in data.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")

    for column in missing_columns:
        print(f" - {column}")

    raise ValueError(
        "Dataset does not contain all required columns."
    )


# =========================================================
# Prepare X and y
# =========================================================

X = data[FEATURE_COLUMNS]
y = data[TARGET_COLUMN]


# =========================================================
# Train-test split
# =========================================================

print("\nCreating train/test split...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print(f"Training samples : {len(X_train)}")
print(f"Testing samples  : {len(X_test)}")


# =========================================================
# Base Gradient Boosting model
# =========================================================

base_model = GradientBoostingClassifier(
    random_state=42
)


# =========================================================
# Hyperparameter search
# =========================================================
#
# We are testing different configurations.
#
# The test set is NOT used during tuning.
#
# Scoring uses macro F1 so that performance across
# Low, Moderate and High is considered rather than
# optimizing only the largest class.
# =========================================================

parameter_grid = {
    "n_estimators": [100, 150, 200],
    "learning_rate": [0.03, 0.05, 0.08],
    "max_depth": [2, 3, 4],
    "min_samples_leaf": [3, 5],
    "subsample": [0.8, 1.0],
}


print("\n========================================")
print(" SEARCHING FOR BETTER MODEL PARAMETERS")
print("========================================")

print("\nThis may take a little while...")
print("The test set will remain untouched during tuning.")


grid_search = GridSearchCV(
    estimator=base_model,
    param_grid=parameter_grid,
    scoring="f1_macro",
    cv=3,
    n_jobs=-1,
    verbose=1,
)


# =========================================================
# Run tuning
# =========================================================

grid_search.fit(X_train, y_train)


# =========================================================
# Best configuration
# =========================================================

best_model = grid_search.best_estimator_

print("\n========================================")
print(" BEST MODEL FOUND")
print("========================================")

print("\nBest parameters:")

for parameter, value in grid_search.best_params_.items():
    print(f"{parameter}: {value}")

print(
    f"\nBest cross-validation macro F1: "
    f"{grid_search.best_score_:.4f}"
)


# =========================================================
# Final evaluation on untouched test set
# =========================================================

print("\n========================================")
print(" V3 FINAL TEST EVALUATION")
print("========================================")

print("\nEvaluating on untouched test data...")

y_pred = best_model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print(f"\nAccuracy: {accuracy:.4f}")
print(f"Accuracy: {accuracy * 100:.2f}%")


# =========================================================
# Classification report
# =========================================================

print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0,
    )
)


# =========================================================
# Confusion matrix
# =========================================================

print("\nConfusion Matrix:")

labels = [
    "High",
    "Low",
    "Moderate",
]

matrix = confusion_matrix(
    y_test,
    y_pred,
    labels=labels,
)

print("\n              Predicted")
print("              High  Low  Moderate")
print("-----------------------------------")

for label, row in zip(labels, matrix):
    print(
        f"Actual {label:<8}"
        f"{row[0]:>5}"
        f"{row[1]:>5}"
        f"{row[2]:>9}"
    )


# =========================================================
# Save V3 model
# =========================================================

model_package = {
    "model": best_model,
    "features": FEATURE_COLUMNS,
    "dataset_version": "V2",
    "model_version": "V3",
    "tuning_metric": "macro_f1",
    "test_accuracy": float(accuracy),
}


joblib.dump(
    model_package,
    MODEL_PATH,
)


# =========================================================
# Complete
# =========================================================

print("\n========================================")
print(" V3 TRAINING COMPLETE")
print("========================================")

print("\nNew model saved as:")

print(MODEL_PATH)

print("\nExisting models were NOT changed:")

print("- risk_model.pkl")
print("- risk_model_expanded.pkl")
print("- risk_model_v2.pkl")