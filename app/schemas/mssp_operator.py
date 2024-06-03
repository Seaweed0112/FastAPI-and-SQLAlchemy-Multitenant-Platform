from pydantic import BaseModel


class MSSPOperatorBase(BaseModel):
    username: str
    email: str


class MSSPOperatorCreate(MSSPOperatorBase):
    password: str


class MSSPOperatorResponse(MSSPOperatorBase):
    id: int
