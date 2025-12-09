# app/routers/support_service.py
from fastapi import APIRouter, Depends, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db as get_db
from app.routers.user_router import get_current_user
from app.schemas.support_schema import (
    SupportMessageRead,
    SupportTicketCreate,
    SupportTicketRead,
)
from app.services.support_service import SupportService

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/", response_model=SupportTicketRead)
async def create_ticket(
    data: SupportTicketCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await SupportService.create_ticket(db=db, user_id=user.id, subject=data.subject)


@router.get("/", response_model=list[SupportTicketRead])
async def get_my_tickets(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await SupportService.get_user_tickets(db=db, user_id=user.id)


@router.get("/{ticket_id}", response_model=SupportTicketRead)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await SupportService.get_ticket(db=db, user_id=user.id, ticket_id=ticket_id)


@router.post("/{ticket_id}/message", response_model=list[SupportMessageRead])
async def add_message(
    ticket_id: int,
    message: str | None = Form(None, description="Текст сообщения"),
    files: list[UploadFile] | None = File(
        default=None,
        description="Необязательный список файлов для вложений",
    ),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Универсальная ручка:
    - можно отправить только текст;
    - только файлы;
    - или текст + файлы.
    attachment_url в теле НЕ принимаем – всё генерится на бэке через MinIO.
    """
    created = await SupportService.add_message_with_files(
        db=db,
        ticket_id=ticket_id,
        user_id=user.id,
        message=message,
        files=files or [],
    )
    return created


@router.post("/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Пользователь вызывает оператора.
    Статус меняется на 'open', AI отключается.
    Возвращаем человеко-понятный ответ.
    """
    await SupportService.escalate_to_operator(
        db=db,
        ticket_id=ticket_id,
        user_id=user.id,
    )

    return {
        "status": "ok",
        "message": (
            "✅ Отлично! Ваше обращение передано оператору.\n\n"
            "⏳ Обычно ответ поступает в течение 24 часов.\n"
            "📬 Ответ придёт на вашу почту.\n\n"
            "Спасибо за обращение!"
        ),
    }


@router.get("/open/all", response_model=list[SupportTicketRead])
async def get_all_open_tickets(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Возвращает все тикеты со статусами 'open' и 'in_progress'.
    Проверку прав убираем — доступ есть у любого залогиненного пользователя.
    """
    return await SupportService.get_open_tickets(db=db)
