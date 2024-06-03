from pydantic import BaseModel


class TenantBase(BaseModel):
    tenant_org: str


class TenantCreate(TenantBase):
    pass


class Tenant(TenantBase):
    id: int
    db_name: str
