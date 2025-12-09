# app/services/support_service.py
from typing import Sequence

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from loguru import logger

from app.models.support import SupportMessage, SupportTicket
from app.agents_tools.support_ai import SupportAIAgent
from app.utils.minio_client import upload_support_file


class SupportService:
    ai_agent = SupportAIAgent()

    @staticmethod
    async def create_ticket(db: AsyncSession, user_id: int, subject: str):
        logger.info("[Support] Creating ticket for user_id={} subject={!r}", user_id, subject)
        # статус по умолчанию "ai"
        ticket = SupportTicket(user_id=user_id, subject=subject, status="ai")
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        logger.info("[Support] Ticket created: id={} status={}", ticket.id, ticket.status)
        return ticket

    @staticmethod
    async def get_user_tickets(db: AsyncSession, user_id: int):
        logger.info("[Support] Fetching tickets for user_id={}", user_id)
        result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.created_at.desc())
        )
        tickets = result.scalars().unique().all()
        logger.info("[Support] Found {} tickets for user_id={}", len(tickets), user_id)
        return tickets

    @staticmethod
    async def get_ticket(db: AsyncSession, user_id: int, ticket_id: int):
        logger.info("[Support] Fetching ticket ticket_id={} for user_id={}", ticket_id, user_id)
        ticket = await db.get(SupportTicket, ticket_id)
        if not ticket or ticket.user_id != user_id:
            logger.warning("[Support] Ticket not found or access denied: ticket_id={} user_id={}", ticket_id, user_id)
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket

    @staticmethod
    async def add_message(
        db: AsyncSession,
        ticket_id: int,
        user_id: int,
        sender: str,
        message: str | None = None,
        attachment_url: str | None = None,
    ):
        """
        Старый метод: одно сообщение, опционально с готовым attachment_url.
        Вызывается из add_message_with_files для текстового сообщения.
        """
        logger.info(
            "[Support] Adding message: ticket_id={} user_id={} sender={} has_text={} has_attachment={}",
            ticket_id,
            user_id,
            sender,
            bool(message),
            bool(attachment_url),
        )
        ticket = await db.get(SupportTicket, ticket_id)
        if not ticket or ticket.user_id != user_id:
            logger.warning("[Support] Ticket not found or access denied when add_message: ticket_id={} user_id={}", ticket_id, user_id)
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

        # Автоответ AI: только если пишет пользователь и статус тикета == "ai"
        if sender == "user" and ticket.status == "ai" and message:
            logger.info("[Support] Ticket {} in 'ai' mode → generating AI reply", ticket_id)
            try:
                ai_reply_text = await SupportService.ai_agent.generate_reply(ticket, msg)
                ai_msg = SupportMessage(
                    ticket_id=ticket_id,
                    sender="ai",
                    message=ai_reply_text,
                )
                db.add(ai_msg)
                await db.commit()
                await db.refresh(ai_msg)
                logger.info("[Support] AI reply created for ticket_id={} msg_id={}", ticket_id, ai_msg.id)
            except Exception as e:
                logger.error("[Support] Failed to generate AI reply for ticket_id={}: {}", ticket_id, e)

        return msg

    @staticmethod
    async def add_message_with_files(
        db: AsyncSession,
        ticket_id: int,
        user_id: int,
        message: str | None,
        files: Sequence[UploadFile] | None = None,
    ) -> list[SupportMessage]:
        """
        Универсальный сценарий:
        - можно отправить только текст;
        - только файлы;
        - или текст + файлы одновременно.
        attachment_url в body не принимаем, всё генерится на стороне бэка.
        """
        created: list[SupportMessage] = []

        # 1) Текстовое сообщение (с AI-ответом, если статус тикета 'ai')
        if message:
            user_msg = await SupportService.add_message(
                db=db,
                ticket_id=ticket_id,
                user_id=user_id,
                sender="user",
                message=message,
                attachment_url=None,
            )
            created.append(user_msg)

        # 2) Файлы (каждый файл — отдельное сообщение с attachment_url)
        if files:
            ticket = await db.get(SupportTicket, ticket_id)
            if not ticket or ticket.user_id != user_id:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Ticket not found")

            for file in files:
                url = await upload_support_file(file, ticket_id=ticket_id, user_id=user_id)
                msg = SupportMessage(
                    ticket_id=ticket_id,
                    sender="user",
                    attachment_url=url,
                )
                db.add(msg)
                created.append(msg)

            if created and (len(created) > 1 or not message):
                # нужно отдельно закоммитить attachment-сообщения
                await db.commit()
                for m in created:
                    if m.id is None:
                        await db.refresh(m)

        logger.info(
            "[Support] add_message_with_files done for ticket_id={} user_id={} created_msgs={}",
            ticket_id,
            user_id,
            len(created),
        )
        return created

    @staticmethod
    async def escalate_to_operator(db: AsyncSession, ticket_id: int, user_id: int):
        logger.info("[Support] Escalate ticket_id={} to operator by user_id={}", ticket_id, user_id)
        ticket = await db.get(SupportTicket, ticket_id)
        if not ticket or ticket.user_id != user_id:
            logger.warning("[Support] Ticket not found or access denied on escalate: ticket_id={} user_id={}", ticket_id, user_id)
            raise HTTPException(status_code=404, detail="Ticket not found")

        ticket.status = "open"
        await db.commit()
        await db.refresh(ticket)
        logger.info("[Support] Ticket {} status changed to 'open'", ticket.id)
        return ticket

    @staticmethod
    async def get_open_tickets(db: AsyncSession):
        """
        Все тикеты, которые нужно обработать оператору.
        AI-тикеты не трогаем, только open / in_progress.
        """
        from sqlalchemy import select

        logger.info("[Support] Fetching all open/in_progress tickets")
        result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.status.in_(["open", "in_progress"]))
            .order_by(SupportTicket.created_at.asc())
        )
        tickets = result.scalars().unique().all()
        logger.info("[Support] Found {} operator tickets", len(tickets))
        return tickets
