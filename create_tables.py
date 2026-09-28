from backend.database import Base, engine
from backend.models import User


print("Creating missing database tables...")

Base.metadata.create_all(bind=engine)

print("Database table check completed.")
print("The users table is now available if it did not already exist.")