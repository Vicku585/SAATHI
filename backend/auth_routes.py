from fastapi import APIRouter
from pydantic import BaseModel

from backend.database import SessionLocal
from backend.models import User
from backend.auth import (
    verify_password,
    create_access_token
)


# ==========================================
# Authentication Router
# ==========================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================================
# Login Input
# ==========================================

class LoginRequest(BaseModel):
    username: str
    password: str


# ==========================================
# Login
# ==========================================

@router.post("/login")
def login(data: LoginRequest):

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Find user
        # ------------------------------------------

        user = (
            db.query(User)
            .filter(
                User.username == data.username
            )
            .first()
        )

        # ------------------------------------------
        # Check username
        # ------------------------------------------

        if not user:
            return {
                "success": False,
                "message": "Invalid username or password"
            }

        # ------------------------------------------
        # Check account status
        # ------------------------------------------

        if not user.is_active:
            return {
                "success": False,
                "message": "User account is inactive"
            }

        # ------------------------------------------
        # Verify password
        # ------------------------------------------

        if not verify_password(
            data.password,
            user.hashed_password
        ):
            return {
                "success": False,
                "message": "Invalid username or password"
            }

        # ------------------------------------------
        # Create JWT token
        # ------------------------------------------

        access_token = create_access_token(
            {
                "sub": str(user.id),
                "username": user.username,
                "role": user.role
            }
        )

        # ------------------------------------------
        # Login successful
        # ------------------------------------------

        return {
            "success": True,
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "personnel_id": user.personnel_id
            }
        }

    finally:

        db.close()