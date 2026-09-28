from pathlib import Path

import joblib
import pandas as pd


# =========================================================
# SENTINELS - V3 Risk Prediction
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "risk_model_v3.pkl"


# =========================================================
# 1. Load V3 model
# =========================================================

print("\n========================================")
print(" SENTINELS - V3 RISK PREDICTION")
print("========================================\n")

print("Loading V3 model...")

model_package = joblib.load(MODEL_PATH)

model = model_package["model"]
features = model_package["features"]

print("V3 model loaded successfully.")


# =========================================================
# 2. Collect wellness information
# =========================================================

print("\n----------------------------------------")
print(" WELLNESS INFORMATION")
print("----------------------------------------")

phq9 = float(
    input("Enter PHQ-9 score (0-27): ")
)

gad7 = float(
    input("Enter GAD-7 score (0-21): ")
)

sleep = float(
    input("Enter sleep hours: ")
)

heart_rate = float(
    input("Enter heart rate (BPM): ")
)

hrv = float(
    input("Enter HRV (ms): ")
)


# =========================================================
# 3. Collect operational / HR information
# =========================================================

print("\n----------------------------------------")
print(" OPERATIONAL / HR INFORMATION")
print("----------------------------------------")

days_since_last_leave = float(
    input("Days since last leave: ")
)

deployment_days = float(
    input("Deployment days: ")
)

duty_hours_per_week = float(
    input("Duty hours per week: ")
)

night_duties = float(
    input("Night duties: ")
)

consecutive_duty_days = float(
    input("Consecutive duty days: ")
)

recent_transfer_count = float(
    input("Recent transfer count: ")
)

training_days = float(
    input("Training days: ")
)

family_separation_days = float(
    input("Family separation days: ")
)


# =========================================================
# 4. Collect derived behavioral / recovery information
# =========================================================

print("\n----------------------------------------")
print(" BEHAVIORAL / RECOVERY INFORMATION")
print("----------------------------------------")

leave_utilization_gap = float(
    input("Leave utilization gap: ")
)

workload_trend = float(
    input("Workload trend: ")
)

recovery_gap = float(
    input("Recovery gap: ")
)


# =========================================================
# 5. Create model input
# =========================================================

new_person = pd.DataFrame([{
    "phq9_score": phq9,
    "gad7_score": gad7,
    "sleep_hours": sleep,
    "heart_rate": heart_rate,
    "hrv": hrv,

    "days_since_last_leave": days_since_last_leave,
    "deployment_days": deployment_days,
    "duty_hours_per_week": duty_hours_per_week,
    "night_duties": night_duties,
    "consecutive_duty_days": consecutive_duty_days,
    "recent_transfer_count": recent_transfer_count,
    "training_days": training_days,
    "family_separation_days": family_separation_days,

    "leave_utilization_gap": leave_utilization_gap,
    "workload_trend": workload_trend,
    "recovery_gap": recovery_gap,
}])


# =========================================================
# 6. Make sure feature order matches training
# =========================================================

new_person = new_person[features]


# =========================================================
# 7. Predict risk
# =========================================================

prediction = model.predict(new_person)

risk_level = prediction[0]


# =========================================================
# 8. Display result
# =========================================================

print("\n========================================")
print(" SENTINELS RISK ASSESSMENT")
print("========================================")

print(f"\nPredicted Risk Level: {risk_level}")

print("\n----------------------------------------")
print("Assessment completed.")
print("----------------------------------------\n")