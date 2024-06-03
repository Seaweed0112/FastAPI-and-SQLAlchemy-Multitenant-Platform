import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import app.crud.tenant as crud_tenant
from app.api.deps import get_current_mssp_operator, get_management_db
from app.crud.tenant import get_all_tenants
from app.models.management import MSSPOperator
from app.models.tenant import Task
from app.schemas.user import UserCreate
from app.schemas.auth import Identity

logger = logging.getLogger(__name__)

router = APIRouter()


# @router.get("/tasks/")
# async def read_all_tasks(current_user: MSSPOperator = Depends(get_current_mssp_operator)):
#     if not current_user:
#         raise HTTPException(status_code=403, detail="Not authorized")

#     tasks = []
#     tenants = await get_all_tenants()
#     for tenant in tenants:
#         engine = create_async_engine(tenant.db_url)
#         SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
#         async with SessionLocal() as session:
#             result = await session.execute(select(Task))
#             tasks.extend(result.scalars().all())

#     return tasks


class TenantAdminCreate(BaseModel):
    tenant_org: str
    admin_user: UserCreate


@router.post("/tenants/")
async def create_tenant(
    request: TenantAdminCreate,
    mssp: Identity = Depends(get_current_mssp_operator),
    management_db: AsyncSession = Depends(get_management_db),
):
    tenant_org = request.tenant_org.strip().upper()
    logger.info(f"Creating tenant {tenant_org}")

    if not tenant_org.isalnum():
        raise HTTPException(status_code=400, detail="Invalid tenant ID")

    try:
        # run the async function in the background
        await crud_tenant.create_tenant(mssp, tenant_org, request.admin_user, management_db)

        # Optionally, update tenant configuration storage
        return {"message": f"Tenant {tenant_org} created successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants/")
async def list_tenants():
    tenants = await get_all_tenants()
    return tenants


@router.get("/tenants/{tenant_org}")
async def get_tenant(
    tenant_org: str,
    mssp: str = Depends(get_current_mssp_operator),
    management_db: AsyncSession = Depends(get_management_db),
):
    tenant = await crud_tenant.get_tenant_by_org(tenant_org, management_db)
    return tenant
