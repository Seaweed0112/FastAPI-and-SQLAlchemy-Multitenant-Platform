from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import User
from app.schemas.user import UserCreate
from app.security import hash_password


async def create_tenant_admin_user(tenant_org: str, user: UserCreate, db: AsyncSession) -> User:
    hashed_password = hash_password(user.password)
    db_user = User(
        tenant_org=tenant_org,
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_user(tenant_org: str, user: UserCreate, db: AsyncSession):
    hashed_password = hash_password(user.password)  # Assuming hash_password is defined elsewhere
    db_user = User(tenant_org=tenant_org, name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_id(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()
