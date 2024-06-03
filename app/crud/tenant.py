from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import MANAGEMENT_DATABASE_URL, TENANT_DATABASE_TEMPLATE_URL
from app.crud.user import create_tenant_admin_user
from app.models.management import Tenant
from app.models.tenant import TenantBase
from app.schemas.user import UserCreate
from app.schemas.auth import Identity
from app.security import get_random_password




async def create_tenant(mssp: Identity, tenant_org: str, tenant_admin: UserCreate, management_db: AsyncSession):
    tenant_db_name = await create_tenant_database(tenant_org)
    await add_tenant_to_db(tenant_org, tenant_admin, tenant_db_name, management_db)

    tenant_db_url = TENANT_DATABASE_TEMPLATE_URL.format(tenant_db_name=tenant_db_name)
    tenant_engine = create_async_engine(tenant_db_url)
    async with tenant_engine.begin() as tenant_conn:
        await tenant_conn.run_sync(TenantBase.metadata.create_all)

    TenantSessionLocal = sessionmaker(bind=tenant_engine, class_=AsyncSession, expire_on_commit=False)
    async with TenantSessionLocal() as tenant_db:
        # create mssp admin user in tenant db
        mssp_admin = UserCreate(
            name="MSSP Operator",
            email="mssp@mssp.mssp",
            password=get_random_password(),
            is_admin=True,
        )
        await create_tenant_admin_user(tenant_org, mssp_admin, tenant_db)
        # create tenant admin user
        await create_tenant_admin_user(tenant_org, tenant_admin, tenant_db)


async def create_tenant_database(tenant_org: str):
    try:
        tenant_db_name = f"tenant_{tenant_org}"
        admin_engine = create_async_engine(MANAGEMENT_DATABASE_URL)
        async with admin_engine.connect() as admin_conn:
            await admin_conn.execute(text(f"CREATE DATABASE {tenant_db_name}"))
        return tenant_db_name
    except Exception as e:
        raise Exception(f"Error creating tenant database {tenant_db_name}: {str(e)}")


async def get_tenant_by_org(tenant_org: str, management_db: AsyncSession):
    #  management_db.query(Tenant).filter(Tenant.tenant_org == tenant_org).first()
    result = await management_db.execute(select(Tenant).where(Tenant.tenant_org == tenant_org))
    return result.scalars().first()


async def add_tenant_to_db(tenant_org: str, tenant_admin: UserCreate, tenant_db_name: str, management_db: AsyncSession):
    _, domain = tenant_admin.email.split("@")
    tenant = Tenant(tenant_org=tenant_org, domain=domain, db_name=tenant_db_name)
    management_db.add(tenant)
    await management_db.commit()


async def get_all_tenants(management_db: AsyncSession):
    result = await management_db.execute(select(Tenant))
    tenants = result.scalars().all()
    return tenants


async def get_tenant_by_domain(domain: str, management_db: AsyncSession) -> Tenant:
    # return management_db.query(Tenant).filter(Tenant.domain == domain).first()
    result = await management_db.execute(select(Tenant).where(Tenant.domain == domain))
    return result.scalars().first()


async def get_tenant_db_name(tenant_org: str, management_db: AsyncSession) -> str:
    tenant = await get_tenant_by_org(tenant_org, management_db)
    if tenant is None:
        raise Exception(f"Tenant with id {tenant_org} not found")
    return tenant.db_name
