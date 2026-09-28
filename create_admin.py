from getpass import getpass

from backend.database import SessionLocal
from backend.models import User
from backend.auth import hash_password


# ==========================================
# Create Initial Admin Account
# ==========================================

def main():

    print("==========================================")
    print(" SENTINELS - Admin Account Setup")
    print("==========================================")

    username = input("Enter admin username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    password = getpass("Enter admin password: ")

    if not password:
        print("Password cannot be empty.")
        return

    confirm_password = getpass("Confirm admin password: ")

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
        # Hash password
        # ------------------------------------------

        hashed_password = hash_password(password)

        # ------------------------------------------
        # Create admin user
        # ------------------------------------------

        admin_user = User(
            username=username,
            hashed_password=hashed_password,
            role="admin",
            personnel_id=None,
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print()
        print("==========================================")
        print(" Admin account created successfully!")
        print("==========================================")
        print(f"Username : {admin_user.username}")
        print(f"Role     : {admin_user.role}")
        print(f"User ID  : {admin_user.id}")
        print("==========================================")

    finally:

        db.close()


if __name__ == "__main__":
    main()