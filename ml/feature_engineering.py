"""
SENTINELS - Feature Engineering

This module converts operational/HR information into
behavioral and recovery indicators used by the ML model.

The same functions should be used during:
1. Model training
2. Backend prediction
3. Future real-world data processing
"""


# =========================================================
# Configuration
# =========================================================

# Reference values used to calculate operational strain.
# These are prototype assumptions, NOT clinical thresholds.
REFERENCE_LEAVE_DAYS = 60
REFERENCE_DUTY_HOURS = 40
REFERENCE_NIGHT_DUTIES = 3
REFERENCE_CONSECUTIVE_DAYS = 7
REFERENCE_DEPLOYMENT_DAYS = 90


# =========================================================
# 1. Leave Utilization Gap
# =========================================================

def calculate_leave_utilization_gap(
    days_since_last_leave: float,
) -> float:
    """
    Estimates how far the current leave interval is
    from the prototype reference interval.

    Positive value:
        Longer interval since leave.

    Negative value:
        Shorter interval since leave.

    Example:
        90 days since leave
        reference = 60 days

        (90 - 60) / 30 = 1.0
    """

    return (
        days_since_last_leave - REFERENCE_LEAVE_DAYS
    ) / 30.0


# =========================================================
# 2. Workload Trend
# =========================================================

def calculate_workload_trend(
    duty_hours_per_week: float,
    night_duties: float,
    consecutive_duty_days: float,
    deployment_days: float,
) -> float:
    """
    Creates a prototype workload-pressure indicator.

    It combines:
    - weekly duty hours
    - night duties
    - consecutive duty days
    - deployment duration

    Positive value:
        Workload pressure is above the reference level.

    Negative value:
        Workload pressure is below the reference level.

    This is a behavioral/operational indicator,
    NOT a clinical measurement.
    """

    duty_component = (
        duty_hours_per_week - REFERENCE_DUTY_HOURS
    ) / 10.0

    night_component = (
        night_duties - REFERENCE_NIGHT_DUTIES
    ) / 3.0

    consecutive_component = (
        consecutive_duty_days - REFERENCE_CONSECUTIVE_DAYS
    ) / 7.0

    deployment_component = (
        deployment_days - REFERENCE_DEPLOYMENT_DAYS
    ) / 90.0

    workload_trend = (
        0.45 * duty_component
        + 0.20 * night_component
        + 0.25 * consecutive_component
        + 0.10 * deployment_component
    )

    return workload_trend


# =========================================================
# 3. Recovery Gap
# =========================================================

def calculate_recovery_gap(
    sleep_hours: float,
    duty_hours_per_week: float,
    consecutive_duty_days: float,
    days_since_last_leave: float,
) -> float:
    """
    Estimates recovery pressure from:
    - sleep duration
    - weekly duty workload
    - consecutive duty period
    - time since last leave

    Positive value:
        Greater recovery pressure.

    Negative value:
        Lower recovery pressure.

    This is a prototype operational indicator,
    NOT a medical or clinical measurement.
    """

    sleep_component = (
        7.0 - sleep_hours
    ) / 2.0

    duty_component = (
        duty_hours_per_week - REFERENCE_DUTY_HOURS
    ) / 10.0

    consecutive_component = (
        consecutive_duty_days - REFERENCE_CONSECUTIVE_DAYS
    ) / 7.0

    leave_component = (
        days_since_last_leave - REFERENCE_LEAVE_DAYS
    ) / 60.0

    recovery_gap = (
        0.35 * sleep_component
        + 0.30 * duty_component
        + 0.20 * consecutive_component
        + 0.15 * leave_component
    )

    return recovery_gap


# =========================================================
# 4. Calculate all derived features
# =========================================================

def calculate_behavioral_features(
    days_since_last_leave: float,
    deployment_days: float,
    duty_hours_per_week: float,
    night_duties: float,
    consecutive_duty_days: float,
    sleep_hours: float,
) -> dict:
    """
    Calculates all three SENTINELS derived features.

    Returns a dictionary that can be directly converted
    into a pandas DataFrame.
    """

    leave_utilization_gap = (
        calculate_leave_utilization_gap(
            days_since_last_leave
        )
    )

    workload_trend = (
        calculate_workload_trend(
            duty_hours_per_week,
            night_duties,
            consecutive_duty_days,
            deployment_days,
        )
    )

    recovery_gap = (
        calculate_recovery_gap(
            sleep_hours,
            duty_hours_per_week,
            consecutive_duty_days,
            days_since_last_leave,
        )
    )

    return {
        "leave_utilization_gap": leave_utilization_gap,
        "workload_trend": workload_trend,
        "recovery_gap": recovery_gap,
    }


# =========================================================
# Test
# =========================================================

if __name__ == "__main__":

    print("\n========================================")
    print(" SENTINELS - FEATURE ENGINEERING TEST")
    print("========================================\n")

    result = calculate_behavioral_features(
        days_since_last_leave=100,
        deployment_days=120,
        duty_hours_per_week=60,
        night_duties=7,
        consecutive_duty_days=14,
        sleep_hours=5.0,
    )

    print("Test operational profile:")
    print("Days since last leave : 100")
    print("Deployment days       : 120")
    print("Duty hours/week       : 60")
    print("Night duties          : 7")
    print("Consecutive duties    : 14")
    print("Sleep hours           : 5")
    
    print("\nDerived features:")

    for feature, value in result.items():
        print(f"{feature:<25}: {value:.3f}")

    print("\nFeature engineering test completed.")