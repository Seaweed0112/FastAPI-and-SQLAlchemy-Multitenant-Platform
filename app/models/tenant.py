import datetime

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

TenantBase = declarative_base()


class User(TenantBase):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_org = Column(String(50), nullable=False)
    name = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC)
    )
    # tasks = relationship("Task", back_populates="user")


class Task(TenantBase):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(TIMESTAMP, default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        TIMESTAMP, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC)
    )
    # user = relationship("User", back_populates="tasks")
