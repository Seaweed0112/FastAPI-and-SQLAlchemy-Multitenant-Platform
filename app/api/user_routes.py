import logging
from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_user, get_current_user, get_tenant_db, get_current_tenant_admin
from app.crud.user import create_user, get_user_by_email, get_user_by_id
from app.models.management import MSSPOperator
from app.models.tenant import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Identity

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/{tenant_org}/users/", response_model=UserResponse)
async def register_user(
    tenant_org: str,
    new_user: UserCreate,
    current_user: Identity = Depends(get_current_tenant_admin),
    db: AsyncSession = Depends(get_tenant_db),
):
    tenant_org = tenant_org.upper()
    db_user = await get_user_by_email(new_user.email, db)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await create_user(tenant_org, new_user, db)


@router.get("/{tenant_org}/users/{user_id}", response_model=UserResponse)
async def read_user(
    tenant_org: str,
    user_id: int,
    current_user: Identity = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    if current_user.user_id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
