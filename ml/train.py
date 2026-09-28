from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = BASE_DIR / "expanded_dataset.csv"
MODEL_PATH = BASE_DIR / "risk_model_expanded.pkl"


# ---------------------------------------------------------
# 2. Features used by the SENTINELS risk model
# ---------------------------------------------------------

FEATURE_COLUMNS = [
    # Wellness indicators
    "phq9_score",
    "gad7_score",
    "sleep_hours",
    "heart_rate",
    "hrv",

    # Operational / HR-related indicators
    "days_since_last_leave",
    "deployment_days",
    "duty_hours_per_week",
    "night_duties",
    "consecutive_duty_days",
    "recent_transfer_count",
    "training_days",
    "family_separation_days",

    # Derived behavioral indicators
    "leave_utilization_gap",
    "workload_trend",
    "recovery_gap",
]

TARGET_COLUMN = "risk_level"


# ---------------------------------------------------------
# 3. Load dataset
# ---------------------------------------------------------

print("\n========================================")
print(" SENTINELS - Expanded Risk Model Training")
print("========================================\n")

print("Loading dataset...")

data = pd.read_csv(DATASET_PATH)

print(f"Dataset loaded successfully.")
print(f"Rows    : {len(data)}")
print(f"Columns : {len(data.columns)}")


# ---------------------------------------------------------
# 4. Check required columns
# ---------------------------------------------------------

required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

missing_columns = [
    column for column in required_columns
    if column not in data.columns
]

if missing_columns:
    print("\nERROR: The following columns are missing:")
    for column in missing_columns:
        print(f" - {column}")

    raise ValueError(
        "Dataset does not contain all required columns."
    )


# ---------------------------------------------------------
# 5. Display risk distribution
# ---------------------------------------------------------

print("\nRisk-level distribution:")

print(data[TARGET_COLUMN].value_counts())


# ---------------------------------------------------------
# 6. Prepare X and y
# ---------------------------------------------------------

X = data[FEATURE_COLUMNS]
y = data[TARGET_COLUMN]


# ---------------------------------------------------------
# 7. Train-test split
# ---------------------------------------------------------

print("\nSplitting dataset...")

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
# 8. Create Gradient Boosting model
# ---------------------------------------------------------

print("\nTraining Gradient Boosting Classifier...")

model = GradientBoostingClassifier(
    n_estimators=150,
    learning_rate=0.08,
    max_depth=3,
    random_state=42
)


# ---------------------------------------------------------
# 9. Train model
# ---------------------------------------------------------

model.fit(X_train, y_train)

print("Model training completed.")


# ---------------------------------------------------------
# 10. Evaluate model
# ---------------------------------------------------------

print("\nEvaluating model...")

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("\n========================================")
print(" MODEL EVALUATION")
print("========================================")

print(f"\nAccuracy: {accuracy:.4f}")
print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ---------------------------------------------------------
# 11. Save model + feature information
# ---------------------------------------------------------

model_package = {
    "model": model,
    "features": FEATURE_COLUMNS
}

joblib.dump(model_package, MODEL_PATH)


# ---------------------------------------------------------
# 12. Training completed
# ---------------------------------------------------------

print("\n========================================")
print(" TRAINING COMPLETE")
print("========================================")

print(f"\nModel saved to:")
print(MODEL_PATH)

print("\nNew file created:")
print("risk_model_expanded.pkl")

print("\nYour original risk_model.pkl was NOT changed.")