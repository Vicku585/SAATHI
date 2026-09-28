from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    Text,
    Boolean
)

from sqlalchemy.sql import func

from backend.database import Base


class Personnel(Base):
    __tablename__ = "personnel"

    id = Column(Integer, primary_key=True, index=True)

    personnel_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(String(100), nullable=False)

    rank = Column(String(50), nullable=True)

    unit = Column(String(100), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# ==========================================
# User / Authentication Model
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(30),
        nullable=False
    )

    personnel_id = Column(
        Integer,
        ForeignKey("personnel.id"),
        nullable=True,
        index=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class WellnessAssessment(Base):
    __tablename__ = "wellness_assessments"

    id = Column(Integer, primary_key=True, index=True)

    personnel_id = Column(
        Integer,
        ForeignKey("personnel.id"),
        nullable=False,
        index=True
    )

    phq9_score = Column(Integer, nullable=True)

    gad7_score = Column(Integer, nullable=True)

    sleep_hours = Column(Float, nullable=True)

    heart_rate = Column(Float, nullable=True)

    hrv = Column(Float, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class OperationalData(Base):
    __tablename__ = "operational_data"

    id = Column(Integer, primary_key=True, index=True)

    personnel_id = Column(
        Integer,
        ForeignKey("personnel.id"),
        nullable=False,
        index=True
    )

    days_since_last_leave = Column(Integer, nullable=True)

    deployment_days = Column(Integer, nullable=True)

    duty_hours_per_week = Column(Float, nullable=True)

    night_duties = Column(Integer, nullable=True)

    consecutive_duty_days = Column(Integer, nullable=True)

    recent_transfer_count = Column(Integer, nullable=True)

    training_days = Column(Integer, nullable=True)

    family_separation_days = Column(Integer, nullable=True)

    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)

    personnel_id = Column(
        Integer,
        ForeignKey("personnel.id"),
        nullable=False,
        index=True
    )

    risk_level = Column(
        String(20),
        nullable=False
    )

    risk_trend = Column(
        String(20),
        nullable=True
    )

    contributing_indicators = Column(
        Text,
        nullable=True
    )

    assessment_source = Column(
        String(50),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class WelfareCase(Base):
    __tablename__ = "welfare_cases"

    id = Column(Integer, primary_key=True, index=True)

    personnel_id = Column(
        Integer,
        ForeignKey("personnel.id"),
        nullable=False,
        index=True
    )

    risk_assessment_id = Column(
        Integer,
        ForeignKey("risk_assessments.id"),
        nullable=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="Attention Required"
    )

    intervention_type = Column(
        String(100),
        nullable=True
    )

    assigned_officer = Column(
        String(100),
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    follow_up_date = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)

    welfare_case_id = Column(
        Integer,
        ForeignKey("welfare_cases.id"),
        nullable=False,
        index=True
    )

    risk_level = Column(
        String(20),
        nullable=True
    )

    risk_trend = Column(
        String(20),
        nullable=True
    )

    outcome = Column(
        String(100),
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    next_follow_up_date = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )