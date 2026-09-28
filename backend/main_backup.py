from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
from datetime import datetime

from backend.database import SessionLocal
from backend.models import (
    Personnel,
    RiskAssessment,
    WelfareCase,
    OperationalData,
    FollowUp
)


# ==========================================
# 1. FastAPI Application
# ==========================================

app = FastAPI(
    title="Sentinels API",
    description="Sentinels Personnel Wellness & ML Risk Assessment API"
)


# ==========================================
# 2. CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 3. Load ML Model
# ==========================================

model = joblib.load("ml/risk_model.pkl")


# ==========================================
# 4. Assessment Input
# ==========================================

class AssessmentData(BaseModel):
    personnel_id: int | None = None
    phq9_score: float
    gad7_score: float
    sleep_hours: float
    heart_rate: float
    hrv: float


# ==========================================
# 5. Personnel Input
# ==========================================

class PersonnelCreate(BaseModel):
    personnel_id: str
    name: str
    rank: str | None = None
    unit: str | None = None


# ==========================================
# 6. Operational Data Input
# ==========================================

class OperationalDataCreate(BaseModel):
    personnel_id: int
    days_since_last_leave: int | None = None
    deployment_days: int | None = None
    duty_hours_per_week: float | None = None
    night_duties: int | None = None
    consecutive_duty_days: int | None = None
    recent_transfer_count: int | None = None
    training_days: int | None = None
    family_separation_days: int | None = None


# ==========================================
# 7. Home
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Sentinels API is running!"
    }


# ==========================================
# 8. Risk Prediction
# ==========================================

@app.post("/predict")
def predict_risk(data: AssessmentData):

    input_data = pd.DataFrame([{
        "phq9_score": data.phq9_score,
        "gad7_score": data.gad7_score,
        "sleep_hours": data.sleep_hours,
        "heart_rate": data.heart_rate,
        "hrv": data.hrv
    }])

    prediction = model.predict(input_data)

    return {
        "risk_level": str(prediction[0])
    }


# ==========================================
# 9. Personnel Registration
# ==========================================

@app.post("/personnel")
def create_personnel(data: PersonnelCreate):

    db = SessionLocal()

    try:

        existing_personnel = (
            db.query(Personnel)
            .filter(
                Personnel.personnel_id == data.personnel_id
            )
            .first()
        )

        if existing_personnel:
            return {
                "success": False,
                "message": "Personnel ID already exists"
            }

        personnel = Personnel(
            personnel_id=data.personnel_id,
            name=data.name,
            rank=data.rank,
            unit=data.unit
        )

        db.add(personnel)
        db.commit()
        db.refresh(personnel)

        return {
            "success": True,
            "message": "Personnel registered successfully",
            "personnel_id": personnel.personnel_id
        }

    finally:
        db.close()


# ==========================================
# 10. Create Operational Data
# ==========================================

@app.post("/operational-data")
def create_operational_data(data: OperationalDataCreate):

    db = SessionLocal()

    try:

        personnel = (
            db.query(Personnel)
            .filter(Personnel.id == data.personnel_id)
            .first()
        )

        if not personnel:
            return {
                "success": False,
                "message": "Personnel not found"
            }

        operational_data = OperationalData(
            personnel_id=data.personnel_id,
            days_since_last_leave=data.days_since_last_leave,
            deployment_days=data.deployment_days,
            duty_hours_per_week=data.duty_hours_per_week,
            night_duties=data.night_duties,
            consecutive_duty_days=data.consecutive_duty_days,
            recent_transfer_count=data.recent_transfer_count,
            training_days=data.training_days,
            family_separation_days=data.family_separation_days
        )

        db.add(operational_data)
        db.commit()
        db.refresh(operational_data)

        return {
            "success": True,
            "message": "Operational data saved successfully",
            "operational_data_id": operational_data.id,
            "personnel_id": operational_data.personnel_id
        }

    finally:
        db.close()


# ==========================================
# 11. Get Operational Data
# ==========================================

@app.get("/operational-data/{personnel_id}")
def get_operational_data(personnel_id: int):

    db = SessionLocal()

    try:

        personnel = (
            db.query(Personnel)
            .filter(Personnel.id == personnel_id)
            .first()
        )

        if not personnel:
            return {
                "success": False,
                "message": "Personnel not found"
            }

        operational_data = (
            db.query(OperationalData)
            .filter(
                OperationalData.personnel_id == personnel_id
            )
            .order_by(
                OperationalData.recorded_at.desc()
            )
            .first()
        )

        if not operational_data:
            return {
                "success": False,
                "message": "No operational data found for this personnel"
            }

        return {
            "success": True,
            "personnel_id": personnel_id,
            "operational_data": {
                "days_since_last_leave":
                    operational_data.days_since_last_leave,
                "deployment_days":
                    operational_data.deployment_days,
                "duty_hours_per_week":
                    operational_data.duty_hours_per_week,
                "night_duties":
                    operational_data.night_duties,
                "consecutive_duty_days":
                    operational_data.consecutive_duty_days,
                "recent_transfer_count":
                    operational_data.recent_transfer_count,
                "training_days":
                    operational_data.training_days,
                "family_separation_days":
                    operational_data.family_separation_days,
                "recorded_at":
                    operational_data.recorded_at
            }
        }

    finally:
        db.close()


# ==========================================
# 12. Operational Pattern Analyzer
# ==========================================

def analyze_operational_indicators(operational_data):

    indicators = []

    if operational_data is None:
        return indicators

    if (
        operational_data.duty_hours_per_week is not None
        and operational_data.duty_hours_per_week > 48
    ):
        indicators.append(
            "Elevated weekly duty workload"
        )

    if (
        operational_data.consecutive_duty_days is not None
        and operational_data.consecutive_duty_days > 10
    ):
        indicators.append(
            "Extended consecutive duty period"
        )

    if (
        operational_data.deployment_days is not None
        and operational_data.deployment_days > 60
    ):
        indicators.append(
            "Extended deployment duration"
        )

    if (
        operational_data.days_since_last_leave is not None
        and operational_data.days_since_last_leave > 45
    ):
        indicators.append(
            "Extended interval since last leave"
        )

    if (
        operational_data.night_duties is not None
        and operational_data.night_duties > 8
    ):
        indicators.append(
            "Frequent night duties"
        )

    if (
        operational_data.recent_transfer_count is not None
        and operational_data.recent_transfer_count >= 2
    ):
        indicators.append(
            "Recent transfer activity"
        )

    if (
        operational_data.family_separation_days is not None
        and operational_data.family_separation_days > 30
    ):
        indicators.append(
            "Extended family separation"
        )

    if not indicators:
        indicators.append(
            "No major operational indicators detected"
        )

    return indicators


# ==========================================
# 13. Welfare Recommendation Engine
# ==========================================

def generate_welfare_recommendation(
    risk_level,
    risk_trend,
    indicators
):

    if risk_level == "High":

        return (
            "Confidential welfare review recommended. "
            "Prioritize human review and consider workload, "
            "recovery, leave, and available support resources."
        )

    elif risk_level == "Moderate" and risk_trend == "Increasing":

        return (
            "Confidential welfare check-in recommended. "
            "Review workload, recovery, sleep, leave patterns, "
            "and operational indicators and consider appropriate "
            "welfare support."
        )

    elif risk_level == "Moderate":

        return (
            "Welfare follow-up recommended. "
            "Continue monitoring wellbeing and review relevant "
            "workload, recovery, and operational factors."
        )

    elif risk_level == "Low" and risk_trend == "Improving":

        return (
            "Wellbeing appears to be improving. "
            "Continue routine monitoring and available "
            "wellness support."
        )

    else:

        return (
            "Routine wellness monitoring recommended."
        )


# ==========================================
# 14. Wellness Assessment
# ==========================================

@app.post("/wellness")
def wellness_assessment(data: AssessmentData):

    db = SessionLocal()

    try:

        input_data = pd.DataFrame([{
            "phq9_score": data.phq9_score,
            "gad7_score": data.gad7_score,
            "sleep_hours": data.sleep_hours,
            "heart_rate": data.heart_rate,
            "hrv": data.hrv
        }])

        prediction = model.predict(input_data)

        risk_level = str(prediction[0])

        # ------------------------------------------
        # Wellness indicators
        # ------------------------------------------

        wellness_indicators = []

        if data.phq9_score >= 10:
            wellness_indicators.append(
                "Elevated PHQ-9 score"
            )

        if data.gad7_score >= 10:
            wellness_indicators.append(
                "Elevated GAD-7 score"
            )

        if data.sleep_hours < 6:
            wellness_indicators.append(
                "Reduced sleep"
            )

        if data.heart_rate > 100:
            wellness_indicators.append(
                "Elevated heart rate"
            )

        if data.hrv < 30:
            wellness_indicators.append(
                "Reduced HRV"
            )

        # ------------------------------------------
        # Operational data
        # ------------------------------------------

        operational_data = None

        if data.personnel_id is not None:

            operational_data = (
                db.query(OperationalData)
                .filter(
                    OperationalData.personnel_id
                    == data.personnel_id
                )
                .order_by(
                    OperationalData.recorded_at.desc()
                )
                .first()
            )

        operational_indicators = (
            analyze_operational_indicators(
                operational_data
            )
        )

        # ------------------------------------------
        # Combine indicators
        # ------------------------------------------

        combined_indicators = []

        if wellness_indicators:
            combined_indicators.extend(
                wellness_indicators
            )

        if (
            operational_indicators
            and operational_indicators[0]
            != "No major operational indicators detected"
        ):
            combined_indicators.extend(
                operational_indicators
            )

        if not combined_indicators:
            combined_indicators.append(
                "No major indicators detected"
            )

        contributing_indicators = ", ".join(
            combined_indicators
        )

        # ------------------------------------------
        # Risk trend
        # ------------------------------------------

        risk_trend = "Initial"

        if data.personnel_id is not None:

            previous_assessment = (
                db.query(RiskAssessment)
                .filter(
                    RiskAssessment.personnel_id
                    == data.personnel_id
                )
                .order_by(
                    RiskAssessment.created_at.desc()
                )
                .first()
            )

            if previous_assessment:

                risk_order = {
                    "Low": 1,
                    "Moderate": 2,
                    "High": 3
                }

                previous_score = risk_order.get(
                    previous_assessment.risk_level
                )

                current_score = risk_order.get(
                    risk_level
                )

                if (
                    previous_score is not None
                    and current_score is not None
                ):

                    if current_score < previous_score:
                        risk_trend = "Improving"

                    elif current_score > previous_score:
                        risk_trend = "Increasing"

                    else:
                        risk_trend = "Stable"

        # ------------------------------------------
        # Recommendation
        # ------------------------------------------

        welfare_recommendation = (
            generate_welfare_recommendation(
                risk_level,
                risk_trend,
                combined_indicators
            )
        )

        # ------------------------------------------
        # Save risk assessment
        # ------------------------------------------

        if data.personnel_id is not None:

            assessment = RiskAssessment(
                personnel_id=data.personnel_id,
                risk_level=risk_level,
                risk_trend=risk_trend,
                contributing_indicators=(
                    contributing_indicators
                ),
                assessment_source="Wellness Assessment"
            )

            db.add(assessment)
            db.commit()
            db.refresh(assessment)

        return {

            "success": True,

            "risk_level": risk_level,

            "risk_trend": risk_trend,

            "wellness_indicators":
                wellness_indicators,

            "operational_indicators":
                operational_indicators,

            "contributing_indicators":
                contributing_indicators,

            "welfare_recommendation":
                welfare_recommendation,

            "message":
                "Wellness assessment completed successfully"
        }

    finally:

        db.close()


# ==========================================
# 15. Welfare Case Input
# ==========================================

class WelfareCaseCreate(BaseModel):

    personnel_id: int
    risk_assessment_id: int
    intervention_type: str | None = None
    assigned_officer: str | None = None
    notes: str | None = None
    follow_up_date: str | None = None


# ==========================================
# 16. Create Welfare Case
# ==========================================

@app.post("/welfare-cases")
def create_welfare_case(data: WelfareCaseCreate):

    db = SessionLocal()

    try:

        personnel = (
            db.query(Personnel)
            .filter(
                Personnel.id == data.personnel_id
            )
            .first()
        )

        if not personnel:
            return {
                "success": False,
                "message": "Personnel not found"
            }

        risk_assessment = (
            db.query(RiskAssessment)
            .filter(
                RiskAssessment.id == data.risk_assessment_id,
                RiskAssessment.personnel_id == data.personnel_id
            )
            .first()
        )

        if not risk_assessment:
            return {
                "success": False,
                "message":
                    "Risk assessment not found for this personnel"
            }

        welfare_case = WelfareCase(
            personnel_id=data.personnel_id,
            risk_assessment_id=data.risk_assessment_id,
            status="Attention Required",
            intervention_type=data.intervention_type,
            assigned_officer=data.assigned_officer,
            notes=data.notes
        )

        if data.follow_up_date:

            welfare_case.follow_up_date = (
                datetime.fromisoformat(
                    data.follow_up_date
                )
            )

        db.add(welfare_case)
        db.commit()
        db.refresh(welfare_case)

        return {

            "success": True,

            "message":
                "Welfare case created successfully",

            "welfare_case_id":
                welfare_case.id,

            "personnel_id":
                welfare_case.personnel_id,

            "risk_assessment_id":
                welfare_case.risk_assessment_id,

            "status":
                welfare_case.status,

            "intervention_type":
                welfare_case.intervention_type,

            "assigned_officer":
                welfare_case.assigned_officer,

            "follow_up_date":
                welfare_case.follow_up_date
        }

    finally:

        db.close()


# ==========================================
# 17. Get Welfare Cases
# ==========================================

@app.get("/welfare-cases")
def get_welfare_cases():

    db = SessionLocal()

    try:

        cases = (
            db.query(
                WelfareCase,
                Personnel,
                RiskAssessment
            )
            .join(
                Personnel,
                WelfareCase.personnel_id == Personnel.id
            )
            .outerjoin(
                RiskAssessment,
                WelfareCase.risk_assessment_id
                == RiskAssessment.id
            )
            .order_by(
                WelfareCase.created_at.desc()
            )
            .all()
        )

        results = []

        for welfare_case, personnel, risk_assessment in cases:

            results.append({

                "welfare_case_id":
                    welfare_case.id,

                "personnel": {
                    "id":
                        personnel.id,

                    "personnel_id":
                        personnel.personnel_id,

                    "name":
                        personnel.name,

                    "rank":
                        personnel.rank,

                    "unit":
                        personnel.unit
                },

                "risk": {

                    "risk_level":
                        risk_assessment.risk_level
                        if risk_assessment else None,

                    "risk_trend":
                        risk_assessment.risk_trend
                        if risk_assessment else None,

                    "contributing_indicators":
                        risk_assessment.contributing_indicators
                        if risk_assessment else None
                },

                "status":
                    welfare_case.status,

                "intervention_type":
                    welfare_case.intervention_type,

                "assigned_officer":
                    welfare_case.assigned_officer,

                "notes":
                    welfare_case.notes,

                "follow_up_date":
                    welfare_case.follow_up_date,

                "created_at":
                    welfare_case.created_at,

                "updated_at":
                    welfare_case.updated_at
            })

        return {
            "success": True,
            "total_cases": len(results),
            "welfare_cases": results
        }

    finally:

        db.close()


# ==========================================
# 18. Welfare Case Update Input
# ==========================================

class WelfareCaseUpdate(BaseModel):

    status: str | None = None
    intervention_type: str | None = None
    assigned_officer: str | None = None
    notes: str | None = None
    follow_up_date: str | None = None


# ==========================================
# 19. Update Welfare Case
# ==========================================

@app.put("/welfare-cases/{case_id}")
def update_welfare_case(
    case_id: int,
    data: WelfareCaseUpdate
):

    db = SessionLocal()

    try:

        welfare_case = (
            db.query(WelfareCase)
            .filter(
                WelfareCase.id == case_id
            )
            .first()
        )

        if not welfare_case:

            return {
                "success": False,
                "message": "Welfare case not found"
            }

        allowed_statuses = [
            "Attention Required",
            "Intervention Initiated",
            "Follow-up Scheduled",
            "Improving",
            "Routine Monitoring"
        ]

        if (
            data.status is not None
            and data.status not in allowed_statuses
        ):

            return {
                "success": False,
                "message": "Invalid welfare case status",
                "allowed_statuses": allowed_statuses
            }

        if data.status is not None:
            welfare_case.status = data.status

        if data.intervention_type is not None:
            welfare_case.intervention_type = (
                data.intervention_type
            )

        if data.assigned_officer is not None:
            welfare_case.assigned_officer = (
                data.assigned_officer
            )

        if data.notes is not None:
            welfare_case.notes = data.notes

        if data.follow_up_date is not None:

            welfare_case.follow_up_date = (
                datetime.fromisoformat(
                    data.follow_up_date
                )
            )

        db.commit()
        db.refresh(welfare_case)

        return {

            "success": True,

            "message":
                "Welfare case updated successfully",

            "welfare_case_id":
                welfare_case.id,

            "personnel_id":
                welfare_case.personnel_id,

            "status":
                welfare_case.status,

            "intervention_type":
                welfare_case.intervention_type,

            "assigned_officer":
                welfare_case.assigned_officer,

            "notes":
                welfare_case.notes,

            "follow_up_date":
                welfare_case.follow_up_date,

            "updated_at":
                welfare_case.updated_at
        }

    finally:

        db.close()


# ==========================================
# 20. Follow-Up Input
# ==========================================

class FollowUpCreate(BaseModel):

    welfare_case_id: int

    risk_level: str | None = None

    risk_trend: str | None = None

    outcome: str | None = None

    notes: str | None = None

    next_follow_up_date: str | None = None


# ==========================================
# 21. Create Follow-Up
# ==========================================

@app.post("/follow-ups")
def create_follow_up(data: FollowUpCreate):

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Check welfare case
        # ------------------------------------------

        welfare_case = (
            db.query(WelfareCase)
            .filter(
                WelfareCase.id == data.welfare_case_id
            )
            .first()
        )

        if not welfare_case:

            return {
                "success": False,
                "message": "Welfare case not found"
            }

        # ------------------------------------------
        # Validate risk level
        # ------------------------------------------

        allowed_risk_levels = [
            "Low",
            "Moderate",
            "High"
        ]

        if (
            data.risk_level is not None
            and data.risk_level not in allowed_risk_levels
        ):

            return {
                "success": False,
                "message": "Invalid risk level",
                "allowed_risk_levels":
                    allowed_risk_levels
            }

        # ------------------------------------------
        # Create follow-up record
        # ------------------------------------------

        follow_up = FollowUp(

            welfare_case_id=
                data.welfare_case_id,

            risk_level=
                data.risk_level,

            risk_trend=
                data.risk_trend,

            outcome=
                data.outcome,

            notes=
                data.notes
        )

        # ------------------------------------------
        # Next follow-up date
        # ------------------------------------------

        if data.next_follow_up_date:

            follow_up.next_follow_up_date = (
                datetime.fromisoformat(
                    data.next_follow_up_date
                )
            )

        db.add(follow_up)

        # ------------------------------------------
        # Update welfare case status
        # ------------------------------------------

        if data.risk_level == "Low":

            welfare_case.status = (
                "Improving"
            )

        elif data.risk_level in ["Moderate", "High"]:

            welfare_case.status = (
                "Follow-up Scheduled"
            )

        elif data.next_follow_up_date:

            welfare_case.status = (
                "Follow-up Scheduled"
            )

        # ------------------------------------------
        # Save
        # ------------------------------------------

        db.commit()

        db.refresh(follow_up)

        db.refresh(welfare_case)

        # ------------------------------------------
        # Return result
        # ------------------------------------------

        return {

            "success": True,

            "message":
                "Follow-up recorded successfully",

            "follow_up_id":
                follow_up.id,

            "welfare_case_id":
                follow_up.welfare_case_id,

            "risk_level":
                follow_up.risk_level,

            "risk_trend":
                follow_up.risk_trend,

            "outcome":
                follow_up.outcome,

            "notes":
                follow_up.notes,

            "next_follow_up_date":
                follow_up.next_follow_up_date,

            "welfare_case_status":
                welfare_case.status
        }

    finally:

        db.close()


# ==========================================
# 22. Get Follow-Ups
# ==========================================

@app.get("/follow-ups/{welfare_case_id}")
def get_follow_ups(welfare_case_id: int):

    db = SessionLocal()

    try:

        welfare_case = (
            db.query(WelfareCase)
            .filter(
                WelfareCase.id == welfare_case_id
            )
            .first()
        )

        if not welfare_case:

            return {
                "success": False,
                "message": "Welfare case not found"
            }

        follow_ups = (
            db.query(FollowUp)
            .filter(
                FollowUp.welfare_case_id
                == welfare_case_id
            )
            .order_by(
                FollowUp.created_at.desc()
            )
            .all()
        )

        results = []

        for follow_up in follow_ups:

            results.append({

                "follow_up_id":
                    follow_up.id,

                "risk_level":
                    follow_up.risk_level,

                "risk_trend":
                    follow_up.risk_trend,

                "outcome":
                    follow_up.outcome,

                "notes":
                    follow_up.notes,

                "next_follow_up_date":
                    follow_up.next_follow_up_date,

                "created_at":
                    follow_up.created_at
            })

        return {

            "success": True,

            "welfare_case_id":
                welfare_case_id,

            "total_follow_ups":
                len(results),

            "follow_ups":
                results
        }

    finally:

        db.close()