from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------
# SENTINELS - Dataset V2 Model Training
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "expanded_dataset_v2.csv"
MODEL_PATH = BASE_DIR / "risk_model_v2.pkl"


# ---------------------------------------------------------
# Features used by the model
# ---------------------------------------------------------

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

    # Behavioral / derived
    "leave_utilization_gap",
    "workload_trend",
    "recovery_gap",
]

TARGET_COLUMN = "risk_level"


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

print("\n========================================")
print(" SENTINELS - V2 Risk Model Training")
print("========================================\n")

print("Loading Dataset V2...")

data = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully.")
print(f"Rows    : {len(data)}")
print(f"Columns : {len(data.columns)}")


# ---------------------------------------------------------
# Validate columns
# ---------------------------------------------------------

required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

missing_columns = [
    column for column in required_columns
    if column not in data.columns
]

if missing_columns:
    print("\nERROR: Missing columns:")

    for column in missing_columns:
        print(f" - {column}")

    raise ValueError(
        "Dataset V2 does not contain all required columns."
    )


# ---------------------------------------------------------
# Risk distribution
# ---------------------------------------------------------

print("\nRisk-level distribution:")

print(data[TARGET_COLUMN].value_counts())


# ---------------------------------------------------------
# Prepare data
# ---------------------------------------------------------

X = data[FEATURE_COLUMNS]
y = data[TARGET_COLUMN]


# ---------------------------------------------------------
# Train-test split
# ---------------------------------------------------------

print("\nSplitting Dataset V2...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Training samples : {len(X_train)}")
print(f"Testing samples  : {len(X_test)}")


# ---------------------------------------------------------
# Create model
# ---------------------------------------------------------

print("\nTraining Gradient Boosting Classifier...")

model = GradientBoostingClassifier(
    n_estimators=150,
    learning_rate=0.08,
    max_depth=3,
    random_state=42
)


# ---------------------------------------------------------
# Train
# ---------------------------------------------------------

model.fit(X_train, y_train)

print("Model training completed.")


# ---------------------------------------------------------
# Predictions
# ---------------------------------------------------------

print("\nEvaluating Dataset V2 model...")

y_pred = model.predict(X_test)


# ---------------------------------------------------------
# Accuracy
# ---------------------------------------------------------

accuracy = accuracy_score(y_test, y_pred)

print("\n========================================")
print(" V2 MODEL EVALUATION")
print("========================================")

print(f"\nAccuracy: {accuracy:.4f}")
print(f"Accuracy: {accuracy * 100:.2f}%")


# ---------------------------------------------------------
# Classification report
# ---------------------------------------------------------

print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ---------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------

print("\nConfusion Matrix:")

labels = ["High", "Low", "Moderate"]

matrix = confusion_matrix(
    y_test,
    y_pred,
    labels=labels
)

print("\n              Predicted")
print("              High  Low  Moderate")
print("-----------------------------------")

for label, row in zip(labels, matrix):
    print(
        f"Actual {label:<8} "
        f"{row[0]:>4} "
        f"{row[1]:>4} "
        f"{row[2]:>8}"
    )


# ---------------------------------------------------------
# Save model
# ---------------------------------------------------------

model_package = {
    "model": model,
    "features": FEATURE_COLUMNS,
    "dataset_version": "V2"
}

joblib.dump(model_package, MODEL_PATH)


# ---------------------------------------------------------
# Complete
# ---------------------------------------------------------

print("\n========================================")
print(" V2 TRAINING COMPLETE")
print("========================================")

print("\nNew model saved as:")
print(MODEL_PATH)

print("\nExisting models were NOT changed:")
print("- risk_model.pkl")
print("- risk_model_expanded.pkl")