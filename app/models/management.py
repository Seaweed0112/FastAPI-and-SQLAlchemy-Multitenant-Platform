import datetime

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base

ManagementBase = declarative_base()


class MSSPOperator(ManagementBase):
    __tablename__ = "mssp_operators"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC)
    )


class Tenant(ManagementBase):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    tenant_org = Column(String(255), unique=True, nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    db_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC)
    )
