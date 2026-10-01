from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
from datetime import datetime

from backend.database import SessionLocal
from backend.auth_routes import router as auth_router
from backend.auth import get_current_user, require_role
from ml.feature_engineering import calculate_behavioral_features
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
app.include_router(auth_router)


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

model_package = joblib.load("ml/risk_model_expanded.pkl")

model = model_package["model"]
MODEL_FEATURES = model_package["features"]


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
    frontend_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    return FileResponse(frontend_path)


# Serve frontend assets alongside the FastAPI application.
# The HTML references these files from the site root, so Render must expose
# them explicitly in addition to serving index.html.
@app.get("/style.css")
def frontend_stylesheet():
    stylesheet_path = Path(__file__).resolve().parent.parent / "frontend" / "style.css"
    return FileResponse(stylesheet_path, media_type="text/css")


@app.get("/app.js")
def frontend_javascript():
    javascript_path = Path(__file__).resolve().parent.parent / "frontend" / "app.js"
    return FileResponse(javascript_path, media_type="application/javascript")


# ==========================================
# 8. Protected Authentication Test
# ==========================================

@app.get("/auth/test-protected")
def test_protected(current_user=Depends(get_current_user)):
    return {
        "success": True,
        "message": "Authentication successful.",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "personnel_id": current_user.personnel_id
        }
    }


# ==========================================
# 8A. Personnel Access Helper
# ==========================================

def check_personnel_access(current_user, personnel_id: int):
    """
    Personnel users can access only their own personnel record.
    Welfare officers and administrators can access authorized records.
    """

    if current_user.role == "personnel":
        if (
            current_user.personnel_id is None
            or current_user.personnel_id != personnel_id
        ):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Personnel users can access only their own records."
            )


# ==========================================
# 8. Risk Prediction
# ==========================================

@app.post("/predict")
def predict_risk(
    data: AssessmentData,
    current_user=Depends(
        require_role("personnel", "welfare_officer", "admin")
    )
):

    if data.personnel_id is None:
        if current_user.role == "personnel":
            data.personnel_id = current_user.personnel_id
        else:
            return {
                "success": False,
                "message": "personnel_id is required for authorized risk prediction."
            }

    check_personnel_access(
        current_user,
        data.personnel_id
    )

    # The expanded model needs operational data in addition to
    # the five wellness indicators.
    if data.personnel_id is None:
        return {
            "success": False,
            "message": (
                "personnel_id is required for expanded risk prediction "
                "because operational/HR data is part of the model input."
            )
        }

    db = SessionLocal()

    try:
        operational_data = (
            db.query(OperationalData)
            .filter(
                OperationalData.personnel_id == data.personnel_id
            )
            .order_by(OperationalData.recorded_at.desc())
            .first()
        )

        if operational_data is None:
            return {
                "success": False,
                "message": (
                    "No operational data found for this personnel. "
                    "Add operational data before running the expanded risk model."
                )
            }

        required_operational_values = {
            "days_since_last_leave": operational_data.days_since_last_leave,
            "deployment_days": operational_data.deployment_days,
            "duty_hours_per_week": operational_data.duty_hours_per_week,
            "night_duties": operational_data.night_duties,
            "consecutive_duty_days": operational_data.consecutive_duty_days,
            "recent_transfer_count": operational_data.recent_transfer_count,
            "training_days": operational_data.training_days,
            "family_separation_days": operational_data.family_separation_days,
        }

        missing_fields = [
            field
            for field, value in required_operational_values.items()
            if value is None
        ]

        if missing_fields:
            return {
                "success": False,
                "message": "Required operational data is incomplete.",
                "missing_operational_fields": missing_fields
            }

        behavioral_features = calculate_behavioral_features(
            days_since_last_leave=operational_data.days_since_last_leave,
            deployment_days=operational_data.deployment_days,
            duty_hours_per_week=operational_data.duty_hours_per_week,
            night_duties=operational_data.night_duties,
            consecutive_duty_days=operational_data.consecutive_duty_days,
            sleep_hours=data.sleep_hours,
        )

        input_data = pd.DataFrame([{
            "phq9_score": data.phq9_score,
            "gad7_score": data.gad7_score,
            "sleep_hours": data.sleep_hours,
            "heart_rate": data.heart_rate,
            "hrv": data.hrv,
            "days_since_last_leave": operational_data.days_since_last_leave,
            "deployment_days": operational_data.deployment_days,
            "duty_hours_per_week": operational_data.duty_hours_per_week,
            "night_duties": operational_data.night_duties,
            "consecutive_duty_days": operational_data.consecutive_duty_days,
            "recent_transfer_count": operational_data.recent_transfer_count,
            "training_days": operational_data.training_days,
            "family_separation_days": operational_data.family_separation_days,
            "leave_utilization_gap": behavioral_features["leave_utilization_gap"],
            "workload_trend": behavioral_features["workload_trend"],
            "recovery_gap": behavioral_features["recovery_gap"],
        }])

        input_data = input_data[MODEL_FEATURES]
        prediction = model.predict(input_data)

        return {
            "success": True,
            "risk_level": str(prediction[0]),
            "model": "expanded_16_feature_model",
            "behavioral_features": behavioral_features
        }

    finally:
        db.close()


# ==========================================
# 9. Personnel Registration
# ==========================================

@app.post("/personnel")
def create_personnel(
    data: PersonnelCreate,
    current_user=Depends(
        require_role("admin")
    )
):

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
def create_operational_data(
    data: OperationalDataCreate,
    current_user=Depends(
        require_role("admin", "commander")
    )
):

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
def get_operational_data(
    personnel_id: int,
    current_user=Depends(
        require_role("personnel", "welfare_officer", "commander", "admin")
    )
):

    check_personnel_access(
        current_user,
        personnel_id
    )

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
# 13. Risk Trend Normalization
# ==========================================

def normalize_risk_trend(risk_trend):

    # Older demo records used "Increasing".
    # SAATHI now presents the same meaning as "Worsening".
    if risk_trend == "Worsening":
        return "Worsening"

    return risk_trend


# ==========================================
# 14. Welfare Recommendation Engine
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

    elif risk_level == "Moderate" and risk_trend == "Worsening":

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
def wellness_assessment(
    data: AssessmentData,
    current_user=Depends(
        require_role("personnel", "welfare_officer", "admin")
    )
):

    if data.personnel_id is None:
        if current_user.role == "personnel":
            data.personnel_id = current_user.personnel_id
        else:
            return {
                "success": False,
                "message": "personnel_id is required for authorized wellness assessment."
            }

    check_personnel_access(
        current_user,
        data.personnel_id
    )

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Operational data required by expanded model
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

        if operational_data is None:
            return {
                "success": False,
                "message": (
                    "Operational data is required for the expanded risk model. "
                    "Please provide personnel_id and ensure operational data exists."
                )
            }

        required_operational_values = {
            "days_since_last_leave": operational_data.days_since_last_leave,
            "deployment_days": operational_data.deployment_days,
            "duty_hours_per_week": operational_data.duty_hours_per_week,
            "night_duties": operational_data.night_duties,
            "consecutive_duty_days": operational_data.consecutive_duty_days,
            "recent_transfer_count": operational_data.recent_transfer_count,
            "training_days": operational_data.training_days,
            "family_separation_days": operational_data.family_separation_days,
        }

        missing_operational_fields = [
            field
            for field, value in required_operational_values.items()
            if value is None
        ]

        if missing_operational_fields:
            return {
                "success": False,
                "message": "Required operational data is incomplete.",
                "missing_operational_fields": missing_operational_fields
            }

        behavioral_features = calculate_behavioral_features(
            days_since_last_leave=operational_data.days_since_last_leave,
            deployment_days=operational_data.deployment_days,
            duty_hours_per_week=operational_data.duty_hours_per_week,
            night_duties=operational_data.night_duties,
            consecutive_duty_days=operational_data.consecutive_duty_days,
            sleep_hours=data.sleep_hours,
        )

        input_data = pd.DataFrame([{
            "phq9_score": data.phq9_score,
            "gad7_score": data.gad7_score,
            "sleep_hours": data.sleep_hours,
            "heart_rate": data.heart_rate,
            "hrv": data.hrv,
            "days_since_last_leave": operational_data.days_since_last_leave,
            "deployment_days": operational_data.deployment_days,
            "duty_hours_per_week": operational_data.duty_hours_per_week,
            "night_duties": operational_data.night_duties,
            "consecutive_duty_days": operational_data.consecutive_duty_days,
            "recent_transfer_count": operational_data.recent_transfer_count,
            "training_days": operational_data.training_days,
            "family_separation_days": operational_data.family_separation_days,
            "leave_utilization_gap": behavioral_features["leave_utilization_gap"],
            "workload_trend": behavioral_features["workload_trend"],
            "recovery_gap": behavioral_features["recovery_gap"],
        }])

        input_data = input_data[MODEL_FEATURES]
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
        # Operational indicators
        # ------------------------------------------

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
                        risk_trend = "Worsening"

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
        # Reassessment context
        # ------------------------------------------

        previous_risk_level = (
            previous_assessment.risk_level
            if previous_assessment
            else None
        )

        reassessment = previous_assessment is not None

        if previous_risk_level is None:
            risk_change = "Initial assessment"
        elif risk_level == previous_risk_level:
            risk_change = "No change"
        elif risk_order.get(risk_level, 0) < risk_order.get(previous_risk_level, 0):
            risk_change = "Improved"
        else:
            risk_change = "Worsened"

        # ------------------------------------------
        # Save risk assessment
        # ------------------------------------------

        assessment = None

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
            db.flush()

            # --------------------------------------
            # Keep an existing welfare case linked to
            # the newest ML assessment. The case itself
            # is NOT automatically closed or changed;
            # welfare officers retain human control over
            # case status and intervention decisions.
            # --------------------------------------

            latest_welfare_case = (
                db.query(WelfareCase)
                .filter(
                    WelfareCase.personnel_id
                    == data.personnel_id
                )
                .order_by(
                    WelfareCase.updated_at.desc(),
                    WelfareCase.created_at.desc()
                )
                .first()
            )

            if latest_welfare_case:
                latest_welfare_case.risk_assessment_id = assessment.id

            db.commit()
            db.refresh(assessment)

        return {

            "success": True,

            "risk_level": risk_level,

            "risk_trend": risk_trend,

            "reassessment": reassessment,

            "previous_risk_level": previous_risk_level,

            "risk_change": risk_change,

            "wellness_indicators":
                wellness_indicators,

            "operational_indicators":
                operational_indicators,

            "contributing_indicators":
                contributing_indicators,

            "welfare_recommendation":
                welfare_recommendation,

            "message": (
                "Wellness reassessment completed successfully"
                if reassessment
                else "Wellness assessment completed successfully"
            )
        }

    finally:

        db.close()


# ==========================================
# 15. Personnel "My Welfare" View
# ==========================================

@app.get("/my-welfare")
def get_my_welfare(
    current_user=Depends(
        require_role("personnel")
    )
):
    # Return only the authenticated personnel user's own
    # welfare information. The endpoint does not accept
    # personnel_id from the client.

    personnel_id = current_user.personnel_id

    if personnel_id is None:
        return {
            "success": False,
            "message": "No personnel record is linked to this account."
        }

    db = SessionLocal()

    try:

        personnel = (
            db.query(Personnel)
            .filter(
                Personnel.id == personnel_id
            )
            .first()
        )

        if not personnel:
            return {
                "success": False,
                "message": "Linked personnel record was not found."
            }

        latest_assessment = (
            db.query(RiskAssessment)
            .filter(
                RiskAssessment.personnel_id == personnel_id
            )
            .order_by(
                RiskAssessment.created_at.desc()
            )
            .first()
        )

        latest_case = (
            db.query(WelfareCase)
            .filter(
                WelfareCase.personnel_id == personnel_id
            )
            .order_by(
                WelfareCase.updated_at.desc(),
                WelfareCase.created_at.desc()
            )
            .first()
        )

        follow_up_results = []

        if latest_case:

            follow_ups = (
                db.query(FollowUp)
                .filter(
                    FollowUp.welfare_case_id == latest_case.id
                )
                .order_by(
                    FollowUp.created_at.desc()
                )
                .all()
            )

            for follow_up in follow_ups:

                follow_up_results.append({
                    "follow_up_id": follow_up.id,
                    "risk_level": follow_up.risk_level,
                    "risk_trend": follow_up.risk_trend,
                    "outcome": follow_up.outcome,
                    "next_follow_up_date":
                        follow_up.next_follow_up_date,
                    "created_at": follow_up.created_at
                })

        risk_level = (
            latest_assessment.risk_level
            if latest_assessment
            else None
        )

        risk_trend = (
            latest_assessment.risk_trend
            if latest_assessment
            else None
        )

        contributing_indicators = (
            latest_assessment.contributing_indicators
            if latest_assessment
            else None
        )

        welfare_recommendation = None

        if latest_assessment:

            indicators = []

            if contributing_indicators:
                indicators = [
                    item.strip()
                    for item in contributing_indicators.split(",")
                ]

            welfare_recommendation = (
                generate_welfare_recommendation(
                    risk_level,
                    risk_trend,
                    indicators
                )
            )

        return {
            "success": True,

            "personnel": {
                "personnel_id": personnel.personnel_id,
                "name": personnel.name,
                "rank": personnel.rank,
                "unit": personnel.unit
            },

            "current_welfare": {
                "risk_level": risk_level,
                "risk_trend": risk_trend,
                "contributing_indicators":
                    contributing_indicators,
                "welfare_recommendation":
                    welfare_recommendation,
                "assessment_date": (
                    latest_assessment.created_at
                    if latest_assessment
                    else None
                )
            },

            "welfare_case": (
                {
                    "case_id": latest_case.id,
                    "status": latest_case.status,
                    "intervention_type":
                        latest_case.intervention_type,
                    "follow_up_date":
                        latest_case.follow_up_date,
                    "created_at":
                        latest_case.created_at,
                    "updated_at":
                        latest_case.updated_at,
                    "follow_ups":
                        follow_up_results
                }
                if latest_case
                else None
            )
        }

    finally:
        db.close()


# ==========================================
# 16. Welfare Case Input
# ==========================================

class WelfareCaseCreate(BaseModel):

    personnel_id: int
    risk_assessment_id: int
    intervention_type: str | None = None
    assigned_officer: str | None = None
    notes: str | None = None
    follow_up_date: str | None = None


# ==========================================
# 17. Create Welfare Case
# ==========================================

@app.post("/welfare-cases")
def create_welfare_case(
    data: WelfareCaseCreate,
    current_user=Depends(
        require_role("welfare_officer", "admin")
    )
):

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
# 18. Commander Unit Welfare Overview
# ==========================================

@app.get("/commander/overview")
def get_commander_overview(
    unit: str | None = None,
    current_user=Depends(
        require_role("commander", "admin")
    )
):
    """
    Aggregate welfare and operational overview for commanders.

    Individual PHQ-9/GAD-7 scores, individual names, and individual
    welfare cases are intentionally not returned here.
    """

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Personnel scope
        # ------------------------------------------

        personnel_query = db.query(Personnel)

        if unit:
            personnel_query = personnel_query.filter(
                Personnel.unit == unit
            )

        personnel_records = personnel_query.all()

        personnel_ids = [
            personnel.id
            for personnel in personnel_records
        ]

        # ------------------------------------------
        # Empty unit / no personnel
        # ------------------------------------------

        if not personnel_ids:
            return {
                "success": True,
                "scope": {
                    "unit": unit,
                    "personnel_count": 0
                },
                "risk_distribution": {
                    "Low": 0,
                    "Moderate": 0,
                    "High": 0
                },
                "operational_summary": {
                    "average_duty_hours_per_week": 0,
                    "average_deployment_days": 0,
                    "average_days_since_last_leave": 0,
                    "average_night_duties": 0,
                    "average_consecutive_duty_days": 0,
                    "average_family_separation_days": 0
                },
                "welfare_summary": {
                    "active_welfare_cases": 0,
                    "follow_up_scheduled": 0,
                    "improving": 0
                }
            }

        # ------------------------------------------
        # Latest risk assessment per personnel
        # ------------------------------------------

        latest_assessments = []

        for personnel_id in personnel_ids:

            assessment = (
                db.query(RiskAssessment)
                .filter(
                    RiskAssessment.personnel_id
                    == personnel_id
                )
                .order_by(
                    RiskAssessment.created_at.desc()
                )
                .first()
            )

            if assessment:
                latest_assessments.append(assessment)

        # ------------------------------------------
        # Risk distribution
        # ------------------------------------------

        risk_distribution = {
            "Low": 0,
            "Moderate": 0,
            "High": 0
        }

        for assessment in latest_assessments:

            if assessment.risk_level in risk_distribution:
                risk_distribution[
                    assessment.risk_level
                ] += 1

        # ------------------------------------------
        # Latest operational data per personnel
        # ------------------------------------------

        operational_records = []

        for personnel_id in personnel_ids:

            operational_data = (
                db.query(OperationalData)
                .filter(
                    OperationalData.personnel_id
                    == personnel_id
                )
                .order_by(
                    OperationalData.recorded_at.desc()
                )
                .first()
            )

            if operational_data:
                operational_records.append(
                    operational_data
                )

        def average(values):
            values = [
                value
                for value in values
                if value is not None
            ]

            if not values:
                return 0

            return round(
                sum(values) / len(values),
                2
            )

        # ------------------------------------------
        # Operational summary
        # ------------------------------------------

        operational_summary = {
            "average_duty_hours_per_week": average([
                item.duty_hours_per_week
                for item in operational_records
            ]),
            "average_deployment_days": average([
                item.deployment_days
                for item in operational_records
            ]),
            "average_days_since_last_leave": average([
                item.days_since_last_leave
                for item in operational_records
            ]),
            "average_night_duties": average([
                item.night_duties
                for item in operational_records
            ]),
            "average_consecutive_duty_days": average([
                item.consecutive_duty_days
                for item in operational_records
            ]),
            "average_family_separation_days": average([
                item.family_separation_days
                for item in operational_records
            ])
        }

        # ------------------------------------------
        # Welfare summary
        # ------------------------------------------

        welfare_cases = (
            db.query(WelfareCase)
            .filter(
                WelfareCase.personnel_id.in_(
                    personnel_ids
                )
            )
            .all()
        )

        active_welfare_cases = len(welfare_cases)

        follow_up_scheduled = sum(
            1
            for case in welfare_cases
            if case.status
            == "Follow-up Scheduled"
            or case.follow_up_date is not None
        )

        improving = sum(
            1
            for case in welfare_cases
            if case.status == "Improving"
        )

        welfare_summary = {
            "active_welfare_cases":
                active_welfare_cases,
            "follow_up_scheduled":
                follow_up_scheduled,
            "improving":
                improving
        }

        # ------------------------------------------
        # Return aggregate information only
        # ------------------------------------------

        return {
            "success": True,
            "scope": {
                "unit": unit,
                "personnel_count":
                    len(personnel_records)
            },
            "risk_distribution":
                risk_distribution,
            "operational_summary":
                operational_summary,
            "welfare_summary":
                welfare_summary
        }

    finally:

        db.close()


# ==========================================
# 19. Get Welfare Cases
# ==========================================

@app.get("/welfare-cases")
def get_welfare_cases(
    current_user=Depends(
        require_role("welfare_officer", "admin")
    )
):

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
                        normalize_risk_trend(
                            risk_assessment.risk_trend
                        )
                        if risk_assessment else None,

                    "contributing_indicators":
                        risk_assessment.contributing_indicators
                        if risk_assessment else None,

                    "assessment_date":
                        risk_assessment.created_at
                        if risk_assessment else None
                },

                "reassessment_history": [
                    {
                        "risk_level": item.risk_level,
                        "risk_trend": normalize_risk_trend(item.risk_trend),
                        "created_at": item.created_at,
                        "assessment_source": item.assessment_source
                    }
                    for item in (
                        db.query(RiskAssessment)
                        .filter(
                            RiskAssessment.personnel_id == personnel.id
                        )
                        .order_by(
                            RiskAssessment.created_at.desc()
                        )
                        .limit(5)
                        .all()
                    )
                ],

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
# 19. Welfare Case Update Input
# ==========================================

class WelfareCaseUpdate(BaseModel):

    status: str | None = None
    intervention_type: str | None = None
    assigned_officer: str | None = None
    notes: str | None = None
    follow_up_date: str | None = None


# ==========================================
# 20. Update Welfare Case
# ==========================================

@app.put("/welfare-cases/{case_id}")
def update_welfare_case(
    case_id: int,
    data: WelfareCaseUpdate,
    current_user=Depends(
        require_role("welfare_officer", "admin")
    )
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
# 21. Follow-Up Input
# ==========================================

class FollowUpCreate(BaseModel):

    welfare_case_id: int

    risk_level: str | None = None

    risk_trend: str | None = None

    outcome: str | None = None

    notes: str | None = None

    next_follow_up_date: str | None = None


# ==========================================
# 22. Create Follow-Up
# ==========================================

@app.post("/follow-ups")
def create_follow_up(
    data: FollowUpCreate,
    current_user=Depends(
        require_role("welfare_officer", "admin")
    )
):

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

        allowed_risk_trends = [
            "Improving",
            "Stable",
            "Worsening"
        ]

        if (
            data.risk_trend is not None
            and normalize_risk_trend(data.risk_trend)
                not in allowed_risk_trends
        ):

            return {
                "success": False,
                "message": "Invalid risk trend",
                "allowed_risk_trends":
                    allowed_risk_trends
            }

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
                normalize_risk_trend(
                    data.risk_trend
                ),

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
# 23. Get Follow-Ups
# ==========================================

@app.get("/follow-ups/{welfare_case_id}")
def get_follow_ups(
    welfare_case_id: int,
    current_user=Depends(
        require_role("welfare_officer", "admin")
    )
):

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
                    normalize_risk_trend(
                        follow_up.risk_trend
                    ),

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