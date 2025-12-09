# app/services/support_service.py
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.support import SupportMessage, SupportTicket


class SupportService:
    @staticmethod
    async def create_ticket(db: AsyncSession, user_id: int, subject: str):
        ticket = SupportTicket(user_id=user_id, subject=subject)
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        return ticket

    @staticmethod
    async def get_user_tickets(db: AsyncSession, user_id: int):
        result = await db.execute(select(SupportTicket).where(SupportTicket.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def add_message(
        db: AsyncSession, ticket_id: int, user_id: int, sender: str, message: str = None, attachment_url: str = None
    ):
        ticket = await db.get(SupportTicket, ticket_id)
        if not ticket or ticket.user_id != user_id:
            raise HTTPException(status_code=404, detail="Ticket not found")

        msg = SupportMessage(
            ticket_id=ticket_id,
            sender=sender,
            message=message,
            attachment_url=attachment_url,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def upload_attachment(db: AsyncSession, ticket_id: int, user_id: int, file: UploadFile):
        ticket = await db.get(SupportTicket, ticket_id)
        if not ticket or ticket.user_id != user_id:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # TODO: заменить на реальную загрузку (например, S3)
        fake_url = f"https://cdn.example.com/uploads/{file.filename}"

        msg = SupportMessage(ticket_id=ticket_id, sender="user", attachment_url=fake_url)
        db.add(msg)
        await db.commit()
        return {"attachment_url": fake_url}
