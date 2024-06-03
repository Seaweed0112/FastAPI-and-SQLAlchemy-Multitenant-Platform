import logging
from typing import AsyncGenerator, Union

from datetime import datetime, UTC
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import MANAGEMENT_DATABASE_URL, TENANT_DATABASE_TEMPLATE_URL
from app.crud.mssp_operator import get_mssp_operator_by_email
from app.crud.tenant import get_tenant_by_domain, get_tenant_db_name
from app.crud.user import get_user_by_email
from app.models.management import MSSPOperator
from app.models.tenant import User
from app.security import decode_access_token
from app.utils.redis_client import redis_client
from app.schemas.auth import Identity

logger = logging.getLogger(__name__)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Create the engine for the management database
management_engine = create_async_engine(MANAGEMENT_DATABASE_URL)

# Create a session factory for the management database
ManagementSessionLocal = sessionmaker(bind=management_engine, class_=AsyncSession, expire_on_commit=False)


async def get_management_db() -> AsyncGenerator[AsyncSession, None]:
    async with ManagementSessionLocal() as session:
        yield session


async def get_tenant_db(
    tenant_org: str = Path(...), management_db: AsyncSession = Depends(get_management_db)
) -> AsyncGenerator[AsyncSession, None]:
    tenant_db_name = await get_tenant_db_name(tenant_org.upper(), management_db)

    if not tenant_db_name:
        yield None
    else:
        tenant_db_url = TENANT_DATABASE_TEMPLATE_URL.format(tenant_db_name=tenant_db_name)
        tenant_engine = create_async_engine(tenant_db_url)
        TenantSessionLocal = sessionmaker(bind=tenant_engine, class_=AsyncSession, expire_on_commit=False)
        async with TenantSessionLocal() as session:
            yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> Identity:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    logger.info(f"Token payload: {payload}")
    jti = payload.get("jti")
    if redis_client.get(f"blacklist_{jti}"):
        logger.error("Token has been revoked")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    expire = datetime.fromtimestamp(payload.get("exp"), UTC)

    if datetime.now(UTC) > expire:
        logger.error("Token has expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    tenant_org: str = payload.get("tenant_org")
    role: str = payload.get("role")
    user_id = payload.get("user_id")
    is_admin = payload.get("is_admin") in [True, "True", "true"]

    return Identity(role=role, tenant_org=tenant_org, user_id=user_id, is_admin=is_admin)


async def get_current_mssp_operator(
    current_user: Identity = Depends(get_current_user),
) -> Identity:
    if current_user.role != "mssp_operator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return current_user


async def get_current_tenant_user(
    tenant_org: str = Path(...),
    current_user: Identity = Depends(get_current_user),
) -> Identity:
    if current_user.role != "mssp_operator" and current_user.tenant_org != tenant_org.upper():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user


async def get_current_tenant_admin(
    tenant_org: str = Path(...),
    current_user: Identity = Depends(get_current_user),
) -> Identity:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    if current_user.role != "mssp_operator" and current_user.tenant_org != tenant_org.upper():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
