from getpass import getpass

from backend.database import SessionLocal
from backend.models import User
from backend.auth import hash_password


# ==========================================
# Create Commander Account
# ==========================================

def main():

    print("==========================================")
    print(" SENTINELS - Commander Account Setup")
    print("==========================================")

    username = input(
        "Enter commander username: "
    ).strip()

    if not username:
        print("Username cannot be empty.")
        return

    password = getpass(
        "Enter commander password: "
    )

    if not password:
        print("Password cannot be empty.")
        return

    confirm_password = getpass(
        "Confirm commander password: "
    )

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Check whether username already exists
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
        # Create commander user
        # ------------------------------------------

        commander_user = User(
            username=username,
            hashed_password=hash_password(password),
            role="commander",
            personnel_id=None,
            is_active=True
        )

        db.add(commander_user)

        db.commit()

        db.refresh(commander_user)

        print()
        print("==========================================")
        print(" Commander account created successfully!")
        print("==========================================")
        print(f"Username : {commander_user.username}")
        print(f"Role     : {commander_user.role}")
        print(f"User ID  : {commander_user.id}")
        print("==========================================")


    finally:

        db.close()


if __name__ == "__main__":
    main()