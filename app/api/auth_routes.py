import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_current_user, get_management_db
from app.config import ADMIN_DOMAIN, TENANT_DATABASE_TEMPLATE_URL
from app.crud.mssp_operator import get_mssp_operator_by_email
from app.crud.tenant import get_tenant_by_domain
from app.crud.user import get_user_by_email
from app.models.management import MSSPOperator
from app.schemas.auth import LoginRequest, Token, Identity
from app.schemas.user import UserResponse
from app.security import create_access_token, decode_access_token, verify_password
from app.utils.captcha import validate_captcha
from app.utils.redis_client import redis_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_management_db)):
    # token payload: role, tenant_org, user_id, is_admin

    if not validate_captcha(request.captcha_key, request.captcha_text):
        logger.error("Invalid CAPTCHA")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CAPTCHA")

    user = None
    tenant_org = None
    is_admin = False

    _, email_domain = request.email.split("@")


    if email_domain == ADMIN_DOMAIN:
        user = await get_mssp_operator_by_email(db, request.email)
        role = "mssp_operator"
        tenant_org = "mssp"
    else:
        tenant = await get_tenant_by_domain(email_domain, db)
        if tenant:
            tenant_org = tenant.tenant_org
            tenant_db_url = TENANT_DATABASE_TEMPLATE_URL.format(tenant_db_name=tenant.db_name)
            tenant_engine = create_async_engine(tenant_db_url)
            TenantSessionLocal = sessionmaker(bind=tenant_engine, class_=AsyncSession, expire_on_commit=False)
            async with TenantSessionLocal() as tenant_db:
                user = await get_user_by_email(request.email, tenant_db)
                role = "tenant_admin" if user.is_admin else "tenant_user"

    if user is None or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    is_admin = (role == "mssp_operator" or user.is_admin)
    access_token = create_access_token(data={"sub": str(request.email), "role": role, "tenant_org": tenant_org, "user_id": user.id, "is_admin": is_admin})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me(current_user: Identity = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    # Decode the token to get the expiry time
    logger.info(f"Token: {token}")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    logger.info(f"Payload: {payload}")
    expiry = payload.get("exp")
    jti = payload.get("jti")
    if not expiry or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Store the token in Redis with an expiry time
    redis_client.setex(f"blacklist_{jti}", expiry - int(time.time()), "true")
    logger.info(f"Token with jti {jti} has been blacklisted.")
    return {"message": "Successfully logged out"}
