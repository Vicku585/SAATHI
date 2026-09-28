from pathlib import Path

import joblib
import pandas as pd


# ---------------------------------------------------------
# SENTINELS - V2 Feature Importance Analysis
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "risk_model_v2.pkl"


# ---------------------------------------------------------
# Load trained V2 model
# ---------------------------------------------------------

print("\n========================================")
print(" SENTINELS - V2 FEATURE IMPORTANCE")
print("========================================\n")

print("Loading V2 model...")

model_package = joblib.load(MODEL_PATH)

model = model_package["model"]
features = model_package["features"]

print("V2 model loaded successfully.")


# ---------------------------------------------------------
# Get feature importance
# ---------------------------------------------------------

importance = model.feature_importances_

feature_importance = pd.DataFrame({
    "feature": features,
    "importance": importance
})


# ---------------------------------------------------------
# Sort from most important to least important
# ---------------------------------------------------------

feature_importance = feature_importance.sort_values(
    by="importance",
    ascending=False
)


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\n========================================")
print(" FEATURE IMPORTANCE")
print("========================================\n")

for index, row in feature_importance.iterrows():

    print(
        f"{row['feature']:<30} "
        f"{row['importance']:.4f}"
    )


# ---------------------------------------------------------
# Group features by SENTINELS category
# ---------------------------------------------------------

wellness_features = [
    "phq9_score",
    "gad7_score",
    "sleep_hours",
    "heart_rate",
    "hrv",
]

operational_features = [
    "days_since_last_leave",
    "deployment_days",
    "duty_hours_per_week",
    "night_duties",
    "consecutive_duty_days",
    "recent_transfer_count",
    "training_days",
    "family_separation_days",
]

behavioral_features = [
    "leave_utilization_gap",
    "workload_trend",
    "recovery_gap",
]


# ---------------------------------------------------------
# Calculate category contribution
# ---------------------------------------------------------

importance_dict = dict(
    zip(
        feature_importance["feature"],
        feature_importance["importance"]
    )
)

wellness_total = sum(
    importance_dict.get(feature, 0)
    for feature in wellness_features
)

operational_total = sum(
    importance_dict.get(feature, 0)
    for feature in operational_features
)

behavioral_total = sum(
    importance_dict.get(feature, 0)
    for feature in behavioral_features
)


# ---------------------------------------------------------
# Display category contribution
# ---------------------------------------------------------

print("\n========================================")
print(" FEATURE CATEGORY CONTRIBUTION")
print("========================================\n")

print(
    f"Wellness features     : "
    f"{wellness_total:.4f} "
    f"({wellness_total * 100:.2f}%)"
)

print(
    f"Operational features  : "
    f"{operational_total:.4f} "
    f"({operational_total * 100:.2f}%)"
)

print(
    f"Behavioral features   : "
    f"{behavioral_total:.4f} "
    f"({behavioral_total * 100:.2f}%)"
)


# ---------------------------------------------------------
# Complete
# ---------------------------------------------------------

print("\n========================================")
print(" ANALYSIS COMPLETE")
print("========================================")