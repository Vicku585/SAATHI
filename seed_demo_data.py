from datetime import datetime, timedelta

from backend.database import SessionLocal
from backend.models import (
    Personnel,
    WellnessAssessment,
    OperationalData,
    RiskAssessment,
    WelfareCase,
    FollowUp,
)


# ============================================================
# SENTINELS - Synthetic Demo Unit Seeder
# ============================================================
# IMPORTANT:
# This script creates synthetic demonstration data only.
# It does NOT represent real CRPF or real personnel data.
#
# Existing P1001 data is preserved.
# The script is safe to run more than once because it checks
# whether the demo personnel IDs already exist.
# ============================================================


DEMO_UNIT = "SENTINELS Demo Unit"


DEMO_PERSONNEL = [
    {
        "personnel_id": "DEMO1001",
        "name": "Demo Personnel 01",
        "rank": "Constable",
        "risk": "Low",
        "trend": "Improving",
        "days_since_leave": 25,
        "deployment_days": 35,
        "duty_hours": 42,
        "night_duties": 3,
        "consecutive_days": 5,
        "transfers": 0,
        "training_days": 8,
        "family_separation": 20,
        "phq9": 4,
        "gad7": 3,
        "sleep": 7.2,
        "heart_rate": 72,
        "hrv": 58,
        "indicators": "Balanced workload, adequate recovery, regular leave",
        "welfare": False,
    },
    {
        "personnel_id": "DEMO1002",
        "name": "Demo Personnel 02",
        "rank": "Constable",
        "risk": "Low",
        "trend": "Stable",
        "days_since_leave": 32,
        "deployment_days": 40,
        "duty_hours": 44,
        "night_duties": 4,
        "consecutive_days": 6,
        "transfers": 0,
        "training_days": 10,
        "family_separation": 25,
        "phq9": 5,
        "gad7": 4,
        "sleep": 7.0,
        "heart_rate": 74,
        "hrv": 55,
        "indicators": "Stable workload and adequate recovery pattern",
        "welfare": False,
    },
    {
        "personnel_id": "DEMO1003",
        "name": "Demo Personnel 03",
        "rank": "Head Constable",
        "risk": "Low",
        "trend": "Stable",
        "days_since_leave": 38,
        "deployment_days": 45,
        "duty_hours": 46,
        "night_duties": 4,
        "consecutive_days": 6,
        "transfers": 1,
        "training_days": 7,
        "family_separation": 30,
        "phq9": 6,
        "gad7": 4,
        "sleep": 6.9,
        "heart_rate": 76,
        "hrv": 53,
        "indicators": "Moderate operational exposure with acceptable recovery",
        "welfare": False,
    },
    {
        "personnel_id": "DEMO1004",
        "name": "Demo Personnel 04",
        "rank": "Constable",
        "risk": "Low",
        "trend": "Improving",
        "days_since_leave": 28,
        "deployment_days": 30,
        "duty_hours": 43,
        "night_duties": 2,
        "consecutive_days": 5,
        "transfers": 0,
        "training_days": 12,
        "family_separation": 18,
        "phq9": 3,
        "gad7": 3,
        "sleep": 7.5,
        "heart_rate": 70,
        "hrv": 61,
        "indicators": "Improving recovery and low workload pressure",
        "welfare": False,
    },
    {
        "personnel_id": "DEMO1005",
        "name": "Demo Personnel 05",
        "rank": "Constable",
        "risk": "Moderate",
        "trend": "Stable",
        "days_since_leave": 55,
        "deployment_days": 65,
        "duty_hours": 50,
        "night_duties": 6,
        "consecutive_days": 8,
        "transfers": 1,
        "training_days": 6,
        "family_separation": 42,
        "phq9": 9,
        "gad7": 8,
        "sleep": 6.2,
        "heart_rate": 81,
        "hrv": 44,
        "indicators": "Elevated workload, reduced sleep and recovery gap",
        "welfare": True,
        "welfare_status": "Follow-up Scheduled",
        "intervention": "Welfare check-in",
        "followup_days": 20,
        "outcome": "Initial welfare review completed; follow-up planned.",
    },
    {
        "personnel_id": "DEMO1006",
        "name": "Demo Personnel 06",
        "rank": "Head Constable",
        "risk": "Moderate",
        "trend": "Improving",
        "days_since_leave": 50,
        "deployment_days": 60,
        "duty_hours": 49,
        "night_duties": 5,
        "consecutive_days": 8,
        "transfers": 1,
        "training_days": 8,
        "family_separation": 40,
        "phq9": 8,
        "gad7": 7,
        "sleep": 6.4,
        "heart_rate": 79,
        "hrv": 46,
        "indicators": "Moderate workload with improving recovery trend",
        "welfare": True,
        "welfare_status": "Improving",
        "intervention": "Confidential welfare check-in",
        "followup_days": 30,
        "outcome": "Wellbeing indicators showing improvement after support.",
    },
    {
        "personnel_id": "DEMO1007",
        "name": "Demo Personnel 07",
        "rank": "Constable",
        "risk": "Moderate",
        "trend": "Stable",
        "days_since_leave": 62,
        "deployment_days": 70,
        "duty_hours": 52,
        "night_duties": 7,
        "consecutive_days": 9,
        "transfers": 1,
        "training_days": 5,
        "family_separation": 48,
        "phq9": 10,
        "gad7": 8,
        "sleep": 6.0,
        "heart_rate": 83,
        "hrv": 42,
        "indicators": "Sustained duty load, night duties and recovery gap",
        "welfare": True,
        "welfare_status": "Attention Required",
        "intervention": "Welfare officer review",
        "followup_days": 14,
        "outcome": "Follow-up required to reassess workload and wellbeing.",
    },
    {
        "personnel_id": "DEMO1008",
        "name": "Demo Personnel 08",
        "rank": "Constable",
        "risk": "Moderate",
        "trend": "Stable",
        "days_since_leave": 58,
        "deployment_days": 62,
        "duty_hours": 51,
        "night_duties": 6,
        "consecutive_days": 8,
        "transfers": 0,
        "training_days": 7,
        "family_separation": 45,
        "phq9": 9,
        "gad7": 9,
        "sleep": 6.1,
        "heart_rate": 82,
        "hrv": 43,
        "indicators": "Elevated workload and reduced recovery opportunity",
        "welfare": False,
    },
    {
        "personnel_id": "DEMO1009",
        "name": "Demo Personnel 09",
        "rank": "Head Constable",
        "risk": "Moderate",
        "trend": "Improving",
        "days_since_leave": 48,
        "deployment_days": 55,
        "duty_hours": 48,
        "night_duties": 5,
        "consecutive_days": 7,
        "transfers": 1,
        "training_days": 9,
        "family_separation": 35,
        "phq9": 8,
        "gad7": 7,
        "sleep": 6.5,
        "heart_rate": 78,
        "hrv": 47,
        "indicators": "Moderate workload with improving recovery",
        "welfare": False,
    },
    {
        "personnel_id": "DEMO1010",
        "name": "Demo Personnel 10",
        "rank": "Constable",
        "risk": "Moderate",
        "trend": "Worsening",
        "days_since_leave": 68,
        "deployment_days": 78,
        "duty_hours": 54,
        "night_duties": 8,
        "consecutive_days": 10,
        "transfers": 2,
        "training_days": 4,
        "family_separation": 55,
        "phq9": 11,
        "gad7": 10,
        "sleep": 5.8,
        "heart_rate": 86,
        "hrv": 39,
        "indicators": "Increasing workload pressure and insufficient recovery",
        "welfare": True,
        "welfare_status": "Attention Required",
        "intervention": "Workload and welfare review",
        "followup_days": 10,
        "outcome": "Requires closer welfare monitoring and reassessment.",
    },
    {
        "personnel_id": "DEMO1011",
        "name": "Demo Personnel 11",
        "rank": "Constable",
        "risk": "High",
        "trend": "Stable",
        "days_since_leave": 78,
        "deployment_days": 90,
        "duty_hours": 58,
        "night_duties": 10,
        "consecutive_days": 12,
        "transfers": 2,
        "training_days": 3,
        "family_separation": 65,
        "phq9": 15,
        "gad7": 13,
        "sleep": 5.2,
        "heart_rate": 91,
        "hrv": 32,
        "indicators": "High workload exposure, prolonged deployment and recovery gap",
        "welfare": True,
        "welfare_status": "Follow-up Scheduled",
        "intervention": "Priority welfare review",
        "followup_days": 7,
        "outcome": "Priority welfare follow-up scheduled.",
    },
    {
        "personnel_id": "DEMO1012",
        "name": "Demo Personnel 12",
        "rank": "Head Constable",
        "risk": "High",
        "trend": "Worsening",
        "days_since_leave": 85,
        "deployment_days": 100,
        "duty_hours": 61,
        "night_duties": 12,
        "consecutive_days": 14,
        "transfers": 2,
        "training_days": 2,
        "family_separation": 72,
        "phq9": 17,
        "gad7": 15,
        "sleep": 4.9,
        "heart_rate": 94,
        "hrv": 28,
        "indicators": "Sustained operational load, reduced sleep and prolonged recovery gap",
        "welfare": True,
        "welfare_status": "Attention Required",
        "intervention": "Priority welfare officer review",
        "followup_days": 5,
        "outcome": "Requires priority follow-up and workload review.",
    },
    {
        "personnel_id": "DEMO1013",
        "name": "Demo Personnel 13",
        "rank": "Constable",
        "risk": "High",
        "trend": "Stable",
        "days_since_leave": 72,
        "deployment_days": 88,
        "duty_hours": 59,
        "night_duties": 11,
        "consecutive_days": 13,
        "transfers": 1,
        "training_days": 3,
        "family_separation": 68,
        "phq9": 16,
        "gad7": 14,
        "sleep": 5.1,
        "heart_rate": 92,
        "hrv": 30,
        "indicators": "High deployment exposure and persistent workload pressure",
        "welfare": True,
        "welfare_status": "Improving",
        "intervention": "Confidential welfare support",
        "followup_days": 25,
        "outcome": "Early improvement observed after welfare support.",
    },
    {
        "personnel_id": "DEMO1014",
        "name": "Demo Personnel 14",
        "rank": "Constable",
        "risk": "High",
        "trend": "Worsening",
        "days_since_leave": 90,
        "deployment_days": 110,
        "duty_hours": 63,
        "night_duties": 13,
        "consecutive_days": 15,
        "transfers": 2,
        "training_days": 2,
        "family_separation": 80,
        "phq9": 18,
        "gad7": 16,
        "sleep": 4.7,
        "heart_rate": 96,
        "hrv": 26,
        "indicators": "Very high operational load and prolonged recovery gap",
        "welfare": True,
        "welfare_status": "Attention Required",
        "intervention": "Priority welfare intervention",
        "followup_days": 5,
        "outcome": "Priority reassessment required.",
    },
]


def create_demo_data():
    db = SessionLocal()

    created_personnel = 0
    created_operational = 0
    created_wellness = 0
    created_risk = 0
    created_cases = 0
    created_followups = 0

    try:
        print()
        print("==========================================")
        print(" SENTINELS - Synthetic Demo Data Seeder")
        print("==========================================")
        print()
        print("Creating synthetic demonstration data...")
        print("Existing P1001 data will be preserved.")
        print()

        for item in DEMO_PERSONNEL:

            # ------------------------------------------------
            # 1. Personnel
            # ------------------------------------------------
            personnel = (
                db.query(Personnel)
                .filter(
                    Personnel.personnel_id == item["personnel_id"]
                )
                .first()
            )

            if personnel:
                print(
                    f"Skipping existing personnel: "
                    f"{item['personnel_id']}"
                )
                continue

            personnel = Personnel(
                personnel_id=item["personnel_id"],
                name=item["name"],
                rank=item["rank"],
                unit=DEMO_UNIT,
            )

            db.add(personnel)
            db.flush()

            created_personnel += 1

            # ------------------------------------------------
            # 2. Operational / HR data
            # ------------------------------------------------
            operational = OperationalData(
                personnel_id=personnel.id,
                days_since_last_leave=item["days_since_leave"],
                deployment_days=item["deployment_days"],
                duty_hours_per_week=item["duty_hours"],
                night_duties=item["night_duties"],
                consecutive_duty_days=item["consecutive_days"],
                recent_transfer_count=item["transfers"],
                training_days=item["training_days"],
                family_separation_days=item["family_separation"],
            )

            db.add(operational)
            created_operational += 1

            # ------------------------------------------------
            # 3. Voluntary wellness assessment
            # ------------------------------------------------
            wellness = WellnessAssessment(
                personnel_id=personnel.id,
                phq9_score=item["phq9"],
                gad7_score=item["gad7"],
                sleep_hours=item["sleep"],
                heart_rate=item["heart_rate"],
                hrv=item["hrv"],
            )

            db.add(wellness)
            db.flush()

            created_wellness += 1

            # ------------------------------------------------
            # 4. Risk assessment
            # ------------------------------------------------
            risk = RiskAssessment(
                personnel_id=personnel.id,
                risk_level=item["risk"],
                risk_trend=item["trend"],
                contributing_indicators=item["indicators"],
                assessment_source="Synthetic Demo Data",
            )

            db.add(risk)
            db.flush()

            created_risk += 1

            # ------------------------------------------------
            # 5. Welfare case
            # ------------------------------------------------
            if item["welfare"]:

                follow_up_date = datetime.now() + timedelta(
                    days=item["followup_days"]
                )

                welfare_case = WelfareCase(
                    personnel_id=personnel.id,
                    risk_assessment_id=risk.id,
                    status=item["welfare_status"],
                    intervention_type=item["intervention"],
                    assigned_officer="Demo Welfare Officer",
                    notes=(
                        "Synthetic demonstration case. "
                        "Not real personnel data."
                    ),
                    follow_up_date=follow_up_date,
                )

                db.add(welfare_case)
                db.flush()

                created_cases += 1

                # ------------------------------------------------
                # 6. Follow-up record
                # ------------------------------------------------
                follow_up = FollowUp(
                    welfare_case_id=welfare_case.id,
                    risk_level=item["risk"],
                    risk_trend=item["trend"],
                    outcome=item["outcome"],
                    notes=(
                        "Synthetic demonstration follow-up. "
                        "Not a clinical record."
                    ),
                    next_follow_up_date=follow_up_date,
                )

                db.add(follow_up)
                created_followups += 1

        db.commit()

        print()
        print("==========================================")
        print(" Demo data created successfully!")
        print("==========================================")
        print(f"Personnel created       : {created_personnel}")
        print(f"Operational records     : {created_operational}")
        print(f"Wellness assessments    : {created_wellness}")
        print(f"Risk assessments        : {created_risk}")
        print(f"Welfare cases           : {created_cases}")
        print(f"Follow-up records       : {created_followups}")
        print("==========================================")
        print()
        print("Demo unit:")
        print(f"  {DEMO_UNIT}")
        print()
        print("Risk distribution among new demo personnel:")
        print("  Low      : 4")
        print("  Moderate : 6")
        print("  High     : 4")
        print()
        print("IMPORTANT:")
        print("These records are synthetic demonstration data.")
        print("They must not be presented as real CRPF statistics.")
        print("==========================================")

    except Exception as e:
        db.rollback()
        print()
        print("==========================================")
        print(" ERROR - Demo data was not created")
        print("==========================================")
        print(str(e))
        print("==========================================")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_demo_data()