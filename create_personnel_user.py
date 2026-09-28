from getpass import getpass

from backend.database import SessionLocal
from backend.models import User, Personnel
from backend.auth import hash_password


# ==========================================
# Create Personnel User Account
# ==========================================

def main():

    print("==========================================")
    print(" SENTINELS - Personnel Account Setup")
    print("==========================================")

    # ------------------------------------------
    # Personnel database ID
    # ------------------------------------------

    personnel_id_input = input(
        "Enter personnel database ID [1]: "
    ).strip()

    if not personnel_id_input:
        personnel_id = 1
    else:
        try:
            personnel_id = int(personnel_id_input)
        except ValueError:
            print("Personnel database ID must be a number.")
            return

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Check personnel exists
        # ------------------------------------------

        personnel = (
            db.query(Personnel)
            .filter(
                Personnel.id == personnel_id
            )
            .first()
        )

        if not personnel:

            print(
                f"No personnel record found with database ID "
                f"{personnel_id}."
            )

            return

        print()
        print("Personnel found:")
        print(f"Name         : {personnel.name}")
        print(f"Personnel ID : {personnel.personnel_id}")
        print(f"Database ID  : {personnel.id}")
        print()

        # ------------------------------------------
        # Username
        # ------------------------------------------

        username = input(
            "Enter personnel username: "
        ).strip()

        if not username:

            print("Username cannot be empty.")
            return

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
            "Enter personnel password: "
        )

        if not password:

            print("Password cannot be empty.")
            return

        confirm_password = getpass(
            "Confirm personnel password: "
        )

        if password != confirm_password:

            print("Passwords do not match.")
            return

        # ------------------------------------------
        # Create user
        # ------------------------------------------

        personnel_user = User(
            username=username,
            hashed_password=hash_password(password),
            role="personnel",
            personnel_id=personnel.id,
            is_active=True
        )

        db.add(personnel_user)

        db.commit()

        db.refresh(personnel_user)

        print()
        print("==========================================")
        print(" Personnel account created successfully!")
        print("==========================================")
        print(f"Username     : {personnel_user.username}")
        print(f"Role         : {personnel_user.role}")
        print(f"User ID      : {personnel_user.id}")
        print(f"Personnel ID : {personnel.personnel_id}")
        print("==========================================")


    finally:

        db.close()


if __name__ == "__main__":
    main()