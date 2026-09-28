from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split

from feature_engineering import calculate_behavioral_features


# =========================================================
# SENTINELS - V4 Risk Model
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "expanded_dataset_v2.csv"
MODEL_PATH = BASE_DIR / "risk_model_v4.pkl"


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

    # Derived behavioral / recovery
    "leave_utilization_gap",
    "workload_trend",
    "recovery_gap",
]

TARGET_COLUMN = "risk_level"


# =========================================================
# V3 best model parameters
# =========================================================
#
# We use the configuration discovered during V3 tuning.
# This allows a cleaner V3 vs V4 comparison.
# =========================================================

MODEL_PARAMETERS = {
    "learning_rate": 0.08,
    "max_depth": 4,
    "min_samples_leaf": 5,
    "n_estimators": 150,
    "subsample": 0.8,
    "random_state": 42,
}


# =========================================================
# Load dataset
# =========================================================

print("\n========================================")
print(" SENTINELS - V4 MODEL TRAINING")
print("========================================\n")

print("Loading Dataset V2...")

data = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")
print(f"Rows    : {len(data)}")
print(f"Columns : {len(data.columns)}")


# =========================================================
# Validate source columns
# =========================================================

SOURCE_COLUMNS = [
    "phq9_score",
    "gad7_score",
    "sleep_hours",
    "heart_rate",
    "hrv",

    "days_since_last_leave",
    "deployment_days",
    "duty_hours_per_week",
    "night_duties",
    "consecutive_duty_days",
    "recent_transfer_count",
    "training_days",
    "family_separation_days",

    "risk_level",
]


missing_columns = [
    column
    for column in SOURCE_COLUMNS
    if column not in data.columns
]

if missing_columns:

    print("\nERROR: Missing required source columns:")

    for column in missing_columns:
        print(f" - {column}")

    raise ValueError(
        "Dataset does not contain all required source columns."
    )


# =========================================================
# Recalculate derived features
# =========================================================
#
# IMPORTANT:
# We do NOT use the existing values of:
#
# leave_utilization_gap
# workload_trend
# recovery_gap
#
# Instead, V4 calculates them using the shared
# feature_engineering.py module.
# =========================================================

print("\n========================================")
print(" CALCULATING DERIVED FEATURES")
print("========================================")

print("\nUsing shared feature_engineering.py...")

derived_features = data.apply(
    lambda row: calculate_behavioral_features(
        days_since_last_leave=row["days_since_last_leave"],
        deployment_days=row["deployment_days"],
        duty_hours_per_week=row["duty_hours_per_week"],
        night_duties=row["night_duties"],
        consecutive_duty_days=row["consecutive_duty_days"],
        sleep_hours=row["sleep_hours"],
    ),
    axis=1,
    result_type="expand",
)


# Add the newly calculated values to the dataset.

data[
    [
        "leave_utilization_gap",
        "workload_trend",
        "recovery_gap",
    ]
] = derived_features


print("Derived features calculated successfully.")

print("\nExample derived values:")

print(
    data[
        [
            "leave_utilization_gap",
            "workload_trend",
            "recovery_gap",
        ]
    ].head()
)


# =========================================================
# Prepare X and y
# =========================================================

X = data[FEATURE_COLUMNS]
y = data[TARGET_COLUMN]


# =========================================================
# Risk distribution
# =========================================================

print("\n========================================")
print(" RISK DISTRIBUTION")
print("========================================")

print(y.value_counts())


# =========================================================
# Train / Test split
# =========================================================

print("\n========================================")
print(" CREATING TRAIN / TEST SPLIT")
print("========================================")

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
# Create V4 model
# =========================================================

print("\n========================================")
print(" TRAINING V4 MODEL")
print("========================================")

print("\nUsing V3's best model configuration:")

for parameter, value in MODEL_PARAMETERS.items():
    print(f"{parameter}: {value}")


model = GradientBoostingClassifier(
    **MODEL_PARAMETERS
)


# =========================================================
# Train
# =========================================================

print("\nTraining Gradient Boosting Classifier...")

model.fit(
    X_train,
    y_train,
)

print("V4 model training completed.")


# =========================================================
# Prediction
# =========================================================

print("\n========================================")
print(" V4 MODEL EVALUATION")
print("========================================")

print("\nEvaluating on untouched test data...")

y_pred = model.predict(X_test)


# =========================================================
# Metrics
# =========================================================

accuracy = accuracy_score(
    y_test,
    y_pred,
)

macro_f1 = f1_score(
    y_test,
    y_pred,
    average="macro",
)


print(f"\nAccuracy : {accuracy:.4f}")
print(f"Accuracy : {accuracy * 100:.2f}%")

print(f"\nMacro F1 : {macro_f1:.4f}")


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
# Feature importance
# =========================================================

print("\n========================================")
print(" FEATURE IMPORTANCE")
print("========================================")

feature_importance = sorted(
    zip(
        FEATURE_COLUMNS,
        model.feature_importances_,
    ),
    key=lambda item: item[1],
    reverse=True,
)

for feature, importance in feature_importance:

    print(
        f"{feature:<30}: "
        f"{importance:.4f}"
    )


# =========================================================
# Save V4 model
# =========================================================

model_package = {
    "model": model,
    "features": FEATURE_COLUMNS,
    "dataset_version": "V2",
    "model_version": "V4",
    "feature_engineering_version": "FE-V1",
    "test_accuracy": float(accuracy),
    "test_macro_f1": float(macro_f1),
}


joblib.dump(
    model_package,
    MODEL_PATH,
)


# =========================================================
# Complete
# =========================================================

print("\n========================================")
print(" V4 TRAINING COMPLETE")
print("========================================")

print("\nNew model saved as:")

print(MODEL_PATH)

print("\nExisting models were NOT changed:")

print("- risk_model.pkl")
print("- risk_model_expanded.pkl")
print("- risk_model_v2.pkl")
print("- risk_model_v3.pkl")

print("\nV3 baseline accuracy : 76.65%")
print(
    f"V4 test accuracy    : "
    f"{accuracy * 100:.2f}%"
)

difference = (
    accuracy * 100
) - 76.65

print(
    f"Difference           : "
    f"{difference:+.2f} percentage points"
)

print("\n========================================")
print(" END")
print("========================================\n")