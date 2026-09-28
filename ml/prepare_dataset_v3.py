from pathlib import Path

import pandas as pd

from feature_engineering import calculate_behavioral_features


# =========================================================
# SENTINELS - Prepare Consistent V3 Dataset
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = BASE_DIR / "expanded_dataset_v2.csv"
OUTPUT_PATH = BASE_DIR / "expanded_dataset_v3.csv"


# =========================================================
# Source columns
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


# =========================================================
# Derived columns
# =========================================================

DERIVED_COLUMNS = [
    "leave_utilization_gap",
    "workload_trend",
    "recovery_gap",
]


# =========================================================
# Header
# =========================================================

print("\n========================================")
print(" SENTINELS - V3 DATASET PREPARATION")
print("========================================\n")


# =========================================================
# Load original dataset
# =========================================================

print("Loading Dataset V2...")

data = pd.read_csv(INPUT_PATH)

print("Dataset loaded successfully.")
print(f"Rows    : {len(data)}")
print(f"Columns : {len(data.columns)}")


# =========================================================
# Validate source columns
# =========================================================

missing_columns = [
    column
    for column in SOURCE_COLUMNS
    if column not in data.columns
]

if missing_columns:

    print("\nERROR: Missing required columns:")

    for column in missing_columns:
        print(f" - {column}")

    raise ValueError(
        "Dataset does not contain all required source columns."
    )


# =========================================================
# Recalculate derived features
# =========================================================

print("\n========================================")
print(" REBUILDING DERIVED FEATURES")
print("========================================")

print(
    "\nExisting derived values will be replaced "
    "with values calculated by feature_engineering.py."
)


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


# =========================================================
# Insert recalculated values
# =========================================================

data[DERIVED_COLUMNS] = derived_features


print("\nDerived features recalculated successfully.")


# =========================================================
# Display comparison
# =========================================================

print("\n========================================")
print(" NEW DERIVED FEATURE VALUES")
print("========================================")

print(
    data[
        DERIVED_COLUMNS
    ].head(10).to_string(index=False)
)


# =========================================================
# Check for missing values
# =========================================================

print("\n========================================")
print(" DATA QUALITY CHECK")
print("========================================")

missing_values = data.isnull().sum()

missing_total = missing_values.sum()

if missing_total == 0:

    print("No missing values detected.")

else:

    print("Missing values found:")

    print(
        missing_values[
            missing_values > 0
        ]
    )


# =========================================================
# Check risk distribution
# =========================================================

print("\n========================================")
print(" RISK-LEVEL DISTRIBUTION")
print("========================================")

print(
    data["risk_level"].value_counts()
)


# =========================================================
# Save V3 dataset
# =========================================================

data.to_csv(
    OUTPUT_PATH,
    index=False,
)


# =========================================================
# Final validation
# =========================================================

print("\n========================================")
print(" V3 DATASET CREATED")
print("========================================")

print(f"\nSaved to:")
print(OUTPUT_PATH)

print(f"\nRows    : {len(data)}")
print(f"Columns : {len(data.columns)}")

print("\nFinal feature columns:")

for column in data.columns:
    print(f" - {column}")


print("\n========================================")
print(" DATASET PREPARATION COMPLETE")
print("========================================\n")