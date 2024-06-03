import logging
import os

import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient

from app.main import myapp

MSSP_OPERATOR_EMAIL = "mssp@ridgesecurity.com"
MSSP_OPERATOR_PASSWORD = "XYZ"

logger = logging.getLogger(__name__)
logging.getLogger("faker").setLevel(logging.ERROR)


@pytest.fixture(scope="session", autouse=True)
def set_test_env_vars():
    os.environ["DISABLE_CAPTCHA"] = "true"
    yield
    os.environ["DISABLE_CAPTCHA"] = "false"


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(transport=ASGITransport(app=myapp), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="module")
async def mssp_operator_token(client: AsyncClient):
    # Log in as mssp_operator
    response = await client.post(
        "/auth/login",
        json={
            "email": MSSP_OPERATOR_EMAIL,
            "password": MSSP_OPERATOR_PASSWORD,
            "captcha_key": "123",
            "captcha_text": "ABC",
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    logger.info(tokens)
    return tokens["access_token"]


@pytest.mark.anyio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    # assert response.json() == {"message": "Welcome to the FastAPI multi-tenant application!"}


@pytest.mark.anyio
async def test_mssp_login(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={
            "email": MSSP_OPERATOR_EMAIL,
            "password": MSSP_OPERATOR_PASSWORD,
            "captcha_key": "123",
            "captcha_text": "ABC",
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]
    logger.info(f"Access token: {access_token}")


@pytest.mark.anyio
async def test_mssp_logout(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={
            "email": MSSP_OPERATOR_EMAIL,
            "password": MSSP_OPERATOR_PASSWORD,
            "captcha_key": "123",
            "captcha_text": "ABC",
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]
    assert access_token is not None

    # test logout
    response = await client.post("/auth/logout", headers={"Authorization": f"Bearer {access_token}"})

    logger.info(response.json())
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}


@pytest.mark.anyio
async def test_mssp_me(client: AsyncClient, mssp_operator_token):
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {mssp_operator_token}"})
    assert response.status_code == 200
    logger.info(response.json())


class TestTenant:
    # Create a new tenant
    tenant_org = Faker().word()
    tenant_admin_password = Faker().password()
    tenant_admin_name = Faker().name()
    clean_admin_name = "".join(letter for letter in tenant_admin_name if letter.isalnum())
    tenant_admin_email = clean_admin_name + "@" + tenant_org.lower() + ".ai"


    @pytest.mark.anyio
    async def test_create_tenant(self, mssp_operator_token, client: AsyncClient):
        logger.info(f"tenant_org: {self.tenant_org}")
        logger.info(f"tenant_admin_email: {self.tenant_admin_email}")
        logger.info(f"tenant_admin_password: {self.tenant_admin_password}")

        response = await client.post(
            "/mssp_operator/tenants/",
            json={
                "tenant_org": self.tenant_org,
                "admin_user": {
                    "name": self.tenant_admin_name,
                    "email": self.tenant_admin_email,
                    "password": self.tenant_admin_password,
                },
            },
            headers={"Authorization": f"Bearer {mssp_operator_token}"},
        )
        logger.debug(response.json())

        assert response.status_code == 200
        assert response.json()["message"] == f"Tenant {self.tenant_org.strip().upper()} created successfully."

    @pytest.mark.anyio
    async def test_get_tenant(self, mssp_operator_token, client: AsyncClient):
        response = await client.get(
            f"/mssp_operator/tenants/{self.tenant_org}", headers={"Authorization": f"Bearer {mssp_operator_token}"}
        )

        assert response.status_code == 200
        assert response.json()["tenant_org"] == self.tenant_org.strip().upper()


class TestCreateTenantUser:
    # Create a new tenant
    tenant_org = Faker().word()
    tenant_admin_password = Faker().password()
    tenant_admin_name = Faker().name()
    clean_admin_name = "".join(letter for letter in tenant_admin_name if letter.isalnum())
    tenant_admin_email = clean_admin_name + "@" + tenant_org.lower() + ".ai"

    tenant_user_password = Faker().password()
    tenant_user_name = Faker().name()
    clean_user_name = "".join(letter for letter in tenant_user_name if letter.isalnum())
    tenant_user_email = clean_user_name + "@" + tenant_org.lower() + ".ai"

    @pytest.fixture(scope="module")
    async def tenant_admin_token(self, mssp_operator_token, client: AsyncClient):
        response = await client.post(
            "/mssp_operator/tenants/",
            json={
                "tenant_org": self.tenant_org,
                "admin_user": {
                    "name": self.tenant_admin_name,
                    "email": self.tenant_admin_email,
                    "password": self.tenant_admin_password,
                },
            },
            headers={"Authorization": f"Bearer {mssp_operator_token}"},
        )
        logger.info(response.json())
        assert response.status_code == 200
        assert response.json()["message"] == f"Tenant {self.tenant_org.strip().upper()} created successfully."

        # Log in as the new tenant admin
        response = await client.post(
            "/auth/login",
            json={
                "email": self.tenant_admin_email,
                "password": self.tenant_admin_password,
                "captcha_key": "123",
                "captcha_text": "ABC",
            },
        )
        assert response.status_code == 200
        tokens = response.json()
        return tokens["access_token"]

    @pytest.mark.anyio
    async def test_create_user_for_tenant(self, tenant_admin_token, client: AsyncClient):
        logger.info(f"Tenant admin token: {tenant_admin_token}")
        # Create a new user for the tenant
        response = await client.post(
            f"/tenants/{self.tenant_org}/users/",
            json={
                "tenant_org": self.tenant_org,
                "name": self.tenant_user_name,
                "email": self.tenant_user_email,
                "password": self.tenant_user_password,
            },
            headers={"Authorization": f"Bearer {tenant_admin_token}"},
        )
        logger.info(response.json())
        assert response.status_code == 200
        assert response.json()["email"] == self.tenant_user_email

    @pytest.mark.anyio
    async def test_get_user_for_tenant(self, tenant_admin_token, client: AsyncClient):
        response = await client.get(
            f"/tenants/{self.tenant_org}/users/3",
            headers={"Authorization": f"Bearer {tenant_admin_token}"},
        )
        logger.info(response.json())
        assert response.status_code == 200
        assert response.json()["email"] == self.tenant_user_email

    @pytest.fixture(scope="module")
    async def tenant_user_token(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={
                "email": self.tenant_user_email,
                "password": self.tenant_user_password,
                "captcha_key": "123",
                "captcha_text": "ABC",
            },
        )
        assert response.status_code == 200
        tokens = response.json()
        access_token = tokens["access_token"]
        logger.info(f"Access token: {access_token}")
        return access_token

    @pytest.mark.anyio
    async def tenant_user_token(self, tenant_user_token, client: AsyncClient):
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {tenant_user_token}"})
        logger.info(response.json())
        assert response.status_code == 200
        assert response.json()["email"] == self.tenant_user_email
