import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_user, get_tenant_db
from app.crud.task import create_task, delete_task, get_task, get_tasks_by_user, update_task
from app.models.tenant import User
from app.schemas.task import TaskCreate
from app.schemas.auth import Identity

router = APIRouter()


@router.post("/{tenant_org}/tasks/")
async def create_task_for_user(
    task: TaskCreate,
    current_user: Identity = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    return await create_task(db, task, current_user.user_id)


@router.get("/{tenant_org}/tasks/")
async def read_tasks_by_user(
    current_user: Identity = Depends(get_current_tenant_user), db: AsyncSession = Depends(get_tenant_db)
):
    return await get_tasks_by_user(db, current_user.user_id)


@router.get("/{tenant_org}/tasks/{task_id}")
async def read_task(
    task_id: int, current_user: User = Depends(get_current_tenant_user), db: AsyncSession = Depends(get_tenant_db)
):
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return task


@router.put("/{tenant_org}/tasks/{task_id}")
async def update_task(
    task_id: int,
    title: str,
    description: str,
    current_user: User = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    task = await update_task(db, task_id, title, description, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{tenant_org}/tasks/{task_id}")
async def delete_task(
    task_id: int, current_user: User = Depends(get_current_tenant_user), db: AsyncSession = Depends(get_tenant_db)
):
    task = await delete_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}
