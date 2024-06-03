from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import MANAGEMENT_DATABASE_URL_SYNC
from app.models.management import ManagementBase, MSSPOperator
from app.security import hash_password
from app.utils.reset_database import reset_database

engine = create_engine(MANAGEMENT_DATABASE_URL_SYNC)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_admin_user():
    db = SessionLocal()
    admin_username = "mssp"
    admin_password = "XYZ"  # Use a secure password or read from an environment variable
    admin_email = "mssp@ridgesecurity.com"

    hashed_password = hash_password(admin_password)

    admin_user = MSSPOperator(
        username=admin_username, hashed_password=hashed_password, email=admin_email, is_active=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    db.close()


if __name__ == "__main__":
    reset_database()
    ManagementBase.metadata.create_all(bind=engine)
    create_admin_user()
    print("MSSP operator user created successfully.")
