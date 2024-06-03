from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.management import MSSPOperator


async def get_mssp_operator_by_id(db: Session, user_id: int):
    result = await db.execute(select(MSSPOperator).where(MSSPOperator.id == user_id)).first()
    return result.scalars().first()


async def get_mssp_operator_by_email(db: Session, email: str) -> MSSPOperator:
    result = await db.execute(select(MSSPOperator).where(MSSPOperator.email == email))
    return result.scalars().first()
