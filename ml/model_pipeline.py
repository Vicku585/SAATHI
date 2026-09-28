from pathlib import Path

import joblib
import pandas as pd

try:
    # Used when imported as part of the ml package
    from .feature_engineering import calculate_behavioral_features
except ImportError:
    # Used when running this file directly
    from feature_engineering import calculate_behavioral_features


# =========================================================
# SENTINELS - Shared ML Model Pipeline
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "risk_model_v4.pkl"


# =========================================================
# Features expected by the V4 model
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

    # Behavioral / Recovery
    "leave_utilization_gap",
    "workload_trend",
    "recovery_gap",
]


# =========================================================
# Load model
# =========================================================

_model_package = joblib.load(MODEL_PATH)


# V4 was saved as a model package.
# Extract the actual trained model if available.

if isinstance(_model_package, dict):
    MODEL = _model_package["model"]
else:
    MODEL = _model_package


# =========================================================
# Build model input
# =========================================================

def build_model_input(
    phq9_score,
    gad7_score,
    sleep_hours,
    heart_rate,
    hrv,
    days_since_last_leave,
    deployment_days,
    duty_hours_per_week,
    night_duties,
    consecutive_duty_days,
    recent_transfer_count,
    training_days,
    family_separation_days,
):
    """
    Build the exact feature structure expected by SENTINELS V4.
    """

    # -----------------------------------------------------
    # Calculate derived behavioral/recovery features
    # -----------------------------------------------------

    derived = calculate_behavioral_features(
        days_since_last_leave=days_since_last_leave,
        deployment_days=deployment_days,
        duty_hours_per_week=duty_hours_per_week,
        night_duties=night_duties,
        consecutive_duty_days=consecutive_duty_days,
        sleep_hours=sleep_hours,
    )

    # -----------------------------------------------------
    # Create one-person DataFrame
    # -----------------------------------------------------

    model_input = pd.DataFrame([
        {
            # Wellness
            "phq9_score": phq9_score,
            "gad7_score": gad7_score,
            "sleep_hours": sleep_hours,
            "heart_rate": heart_rate,
            "hrv": hrv,

            # Operational
            "days_since_last_leave": days_since_last_leave,
            "deployment_days": deployment_days,
            "duty_hours_per_week": duty_hours_per_week,
            "night_duties": night_duties,
            "consecutive_duty_days": consecutive_duty_days,
            "recent_transfer_count": recent_transfer_count,
            "training_days": training_days,
            "family_separation_days": family_separation_days,

            # Derived
            "leave_utilization_gap": derived["leave_utilization_gap"],
            "workload_trend": derived["workload_trend"],
            "recovery_gap": derived["recovery_gap"],
        }
    ])

    # -----------------------------------------------------
    # Force exact feature order
    # -----------------------------------------------------

    model_input = model_input[FEATURE_COLUMNS]

    return model_input


# =========================================================
# Predict risk
# =========================================================

def predict_risk(
    phq9_score,
    gad7_score,
    sleep_hours,
    heart_rate,
    hrv,
    days_since_last_leave,
    deployment_days,
    duty_hours_per_week,
    night_duties,
    consecutive_duty_days,
    recent_transfer_count,
    training_days,
    family_separation_days,
):
    """
    Generate a SENTINELS risk prediction.
    """

    model_input = build_model_input(
        phq9_score=phq9_score,
        gad7_score=gad7_score,
        sleep_hours=sleep_hours,
        heart_rate=heart_rate,
        hrv=hrv,
        days_since_last_leave=days_since_last_leave,
        deployment_days=deployment_days,
        duty_hours_per_week=duty_hours_per_week,
        night_duties=night_duties,
        consecutive_duty_days=consecutive_duty_days,
        recent_transfer_count=recent_transfer_count,
        training_days=training_days,
        family_separation_days=family_separation_days,
    )

    prediction = MODEL.predict(model_input)

    return prediction[0]


# =========================================================
# Test
# =========================================================

if __name__ == "__main__":

    print("\n========================================")
    print(" SENTINELS - MODEL PIPELINE TEST")
    print("========================================\n")

    print("V4 model loaded successfully.")

    test_input = build_model_input(
        phq9_score=12,
        gad7_score=10,
        sleep_hours=5.5,
        heart_rate=92,
        hrv=28,
        days_since_last_leave=100,
        deployment_days=120,
        duty_hours_per_week=60,
        night_duties=7,
        consecutive_duty_days=14,
        recent_transfer_count=2,
        training_days=8,
        family_separation_days=120,
    )

    print("\nModel input created successfully.")

    print("\nFeature values:")
    print(test_input.to_string(index=False))

    risk = predict_risk(
        phq9_score=12,
        gad7_score=10,
        sleep_hours=5.5,
        heart_rate=92,
        hrv=28,
        days_since_last_leave=100,
        deployment_days=120,
        duty_hours_per_week=60,
        night_duties=7,
        consecutive_duty_days=14,
        recent_transfer_count=2,
        training_days=8,
        family_separation_days=120,
    )

    print("\n========================================")
    print(" SENTINELS RISK ASSESSMENT")
    print("========================================")

    print(f"\nPredicted Risk Level: {risk}")

    print("\n========================================")
    print(" MODEL PIPELINE TEST COMPLETE")
    print("========================================\n")