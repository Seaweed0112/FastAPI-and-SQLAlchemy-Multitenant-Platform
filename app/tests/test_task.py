import logging

import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient

from app.main import myapp

MSSP_OPERATOR_EMAIL = "mssp@ridgesecurity.com"
MSSP_OPERATOR_PASSWORD = "XYZ"

logger = logging.getLogger(__name__)
logging.getLogger("faker").setLevel(logging.ERROR)


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
            "captcha_text": "123",
        },
    )
    assert response.status_code == 200
    tokens = response.json()
    logger.info(tokens)
    return tokens["access_token"]


class TestTask:
    tenant_org = Faker().word()
    tenant_admin_password = Faker().password()
    tenant_admin_name = Faker().name()
    clean_admin_name = "".join(letter for letter in tenant_admin_name if letter.isalnum())
    tenant_admin_email = clean_admin_name + "@" + tenant_org.lower() + ".ai"

    @pytest.fixture(scope="module")
    async def tenant_admin_token(self, mssp_operator_token, client: AsyncClient):
        # Create a new tenant
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

        # Log in as the new tenant admin
        response = await client.post(
            "/auth/login",
            json={
                "email": self.tenant_admin_email,
                "password": self.tenant_admin_password,
                "captcha_key": "123",
                "captcha_text": "123",
            },
        )
        assert response.status_code == 200
        tokens = response.json()
        return tokens["access_token"]

    @pytest.fixture(scope="module")
    async def tenant_user_token(self, tenant_admin_token, client: AsyncClient):
        # Create a new user for the tenant
        tenant_user_password = Faker().password()
        tenant_user_name = Faker().name()
        clean_user_name = "".join(letter for letter in tenant_user_name if letter.isalnum())
        tenant_user_email = clean_user_name + "@" + self.tenant_org.lower() + ".ai"

        response = await client.post(
            f"/tenants/{self.tenant_org}/users/",
            json={
                "tenant_org": self.tenant_org,
                "name": tenant_user_name,
                "email": tenant_user_email,
                "password": tenant_user_password,
            },
            headers={"Authorization": f"Bearer {tenant_admin_token}"},
        )
        logger.info(response.json())
        assert response.status_code == 200
        assert response.json()["email"] == tenant_user_email

        # Log in as the new tenant user
        response = await client.post(
            "/auth/login",
            json={
                "email": tenant_user_email,
                "password": tenant_user_password,
                "captcha_key": "123",
                "captcha_text": "123",
            },
        )
        assert response.status_code == 200
        tokens = response.json()
        return tokens["access_token"]

    @pytest.mark.anyio
    async def test_create_task(self, tenant_user_token, client: AsyncClient):
        response = await client.post(
            f"/tenants/{self.tenant_org}/tasks/",
            json={"title": "Test Task", "description": "This is a test task"},
            headers={"Authorization": f"Bearer {tenant_user_token}"},
        )
        logger.info(response.json())
        assert response.status_code == 200
        assert response.json()["title"] == "Test Task"

    @pytest.mark.anyio
    async def test_create_another_task(self, tenant_user_token, client: AsyncClient):
        response = await client.post(
            f"/tenants/{self.tenant_org}/tasks/",
            json={"title": "Another Test Task", "description": "This is another test task"},
            headers={"Authorization": f"Bearer {tenant_user_token}"},
        )
        logger.info(response.json())
        assert response.status_code == 200
        assert response.json()["title"] == "Another Test Task"

    @pytest.mark.anyio
    async def test_get_tasks(self, tenant_user_token, client: AsyncClient):
        response = await client.get(
            f"/tenants/{self.tenant_org}/tasks/",
            headers={"Authorization": f"Bearer {tenant_user_token}"},
        )
        logger.info(response.json())
        assert response.status_code == 200
        assert len(response.json()) == 2
