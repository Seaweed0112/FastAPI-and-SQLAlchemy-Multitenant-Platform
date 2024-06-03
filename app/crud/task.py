import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Task
from app.schemas.task import TaskCreate

logger = logging.getLogger(__name__)


async def get_task(db: AsyncSession, task_id: int):
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalars().first()


async def get_tasks_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Task).where(Task.user_id == user_id))
    return result.scalars().all()


async def create_task(db: AsyncSession, task: TaskCreate, user_id: int):
    db_task = Task(title=task.title, description=task.description, user_id=user_id)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def update_task(db: AsyncSession, task_id: int, title: str, description: str, user_id: int):
    task = await get_task(db, task_id)
    if not task:
        return None
    task.title = title
    task.description = description
    await db.commit()
    return task


async def delete_task(db: AsyncSession, task_id: int, user_id: int):
    task = await get_task(db, task_id)
    if not task:
        return None
    await db.delete(task)
    await db.commit()
    return task
