from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    captcha_key: str
    captcha_text: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Identity(BaseModel):
    role: str
    tenant_org: str
    user_id: int
    is_admin: bool