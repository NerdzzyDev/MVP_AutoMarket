from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db as get_db
from app.routers.user_router import get_current_user
from app.schemas.support_schema import SupportMessageCreate, SupportMessageRead, SupportTicketCreate, SupportTicketRead
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


@router.post("/{ticket_id}/message", response_model=SupportMessageRead)
async def add_message(
    ticket_id: int,
    data: SupportMessageCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await SupportService.add_message(
        db=db,
        ticket_id=ticket_id,
        user_id=user.id,
        sender="user",
        message=data.message,
        attachment_url=data.attachment_url,
    )


@router.post("/{ticket_id}/upload")
async def upload_file(
    ticket_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await SupportService.upload_attachment(db=db, ticket_id=ticket_id, user_id=user.id, file=file)
