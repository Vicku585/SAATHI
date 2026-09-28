from getpass import getpass

from backend.database import SessionLocal
from backend.models import User
from backend.auth import hash_password


# ==========================================
# Create Welfare Officer User Account
# ==========================================

def main():

    print("==========================================")
    print(" SENTINELS - Welfare Officer Account Setup")
    print("==========================================")

    # ------------------------------------------
    # Username
    # ------------------------------------------

    username = input(
        "Enter welfare officer username: "
    ).strip()

    if not username:

        print("Username cannot be empty.")
        return

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Check username already exists
        # ------------------------------------------

        existing_user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if existing_user:

            print(
                f"User '{username}' already exists."
            )

            return

        # ------------------------------------------
        # Password
        # ------------------------------------------

        password = getpass(
            "Enter welfare officer password: "
        )

        if not password:

            print("Password cannot be empty.")
            return

        confirm_password = getpass(
            "Confirm welfare officer password: "
        )

        if password != confirm_password:

            print("Passwords do not match.")
            return

        # ------------------------------------------
        # Create Welfare Officer user
        # ------------------------------------------

        welfare_officer_user = User(
            username=username,
            hashed_password=hash_password(password),
            role="welfare_officer",
            personnel_id=None,
            is_active=True
        )

        db.add(welfare_officer_user)

        db.commit()

        db.refresh(welfare_officer_user)

        print()
        print("==========================================")
        print(" Welfare Officer account created!")
        print("==========================================")
        print(f"Username : {welfare_officer_user.username}")
        print(f"Role     : {welfare_officer_user.role}")
        print(f"User ID  : {welfare_officer_user.id}")
        print("==========================================")


    finally:

        db.close()


if __name__ == "__main__":
    main()