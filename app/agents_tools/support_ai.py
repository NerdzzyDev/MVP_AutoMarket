# app/agents_tools/support_ai.py
import os
from loguru import logger
from openai import AsyncOpenAI

from app.models.support import SupportMessage, SupportTicket


class SupportAIAgent:
    """
    AI-помощник для поддержки.
    Используем OpenAI по аналогии с TextPartIdentifierAgent.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("[SupportAI] OPENAI_API_KEY not set!")
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_reply(self, ticket: SupportTicket, new_user_message: SupportMessage) -> str:
        """
        Строим промпт на основе темы тикета и истории сообщений.
        Возвращаем только текст ответа (без разметки, без JSON).
        AI НЕ видит фото/файлы, только текст.
        Отвечает на языке пользователя, но все элементы интерфейса оставляет на немецком.
        """

        user_text = (new_user_message.message or "").strip()

        # Собираем историю (компактно, без дубля последнего сообщения)
        history_lines: list[str] = []
        msgs = sorted(ticket.messages, key=lambda m: m.created_at or 0)

        for m in msgs:
            if m.id == new_user_message.id:
                continue
            role = "Пользователь" if m.sender == "user" else "Оператор/AI"
            text = m.message or "(пустое сообщение)"
            history_lines.append(f"{role}: {text}")

        history_lines.append(f"Пользователь (новое сообщение): {user_text}")
        history = "\n".join(history_lines)

        prompt = (
            "Ты — вежливый помощник службы поддержки сервиса по поиску автозапчастей (веб-сайт на немецком).\n"
            "Отвечай КРАТКО и ПО ДЕЛУ, на ТОМ ЖЕ ЯЗЫКЕ, на котором пишет пользователь.\n"
            "Если пользователь пишет по-русски — отвечай по-русски. Если по-немецки — отвечай по-немецки. "
            "Если по-английски — по-английски и т.д.\n\n"

            "ОЧЕНЬ ВАЖНО:\n"
            "- Ты НЕ видишь вложения (фото, документы, файлы). Ты видишь только текст сообщений.\n"
            "- Никогда не говори, что ты 'посмотрел фото' или 'проанализировал картинку'.\n"
            "- Если пользователь ссылается на фото/документ, объясни, что он должен сделать на сайте, "
            "чтобы система сама обработала этот документ/фото.\n"
            "- Не придумывай данные заказа, VIN, KBA, TSN, цены и прочие точные значения, если их нет в тексте.\n"
            "- Если пользователь не даёт нужных данных, честно скажи, что их не видишь, и подскажи, где их взять.\n\n"

            "Как устроен поиск на сайте (используй это, когда нужно объяснить 'что где нажать'):\n"
            "1) На главной странице есть вкладка **\"Automatisches Suchen\"**:\n"
            "   • Поле **\"Dokument hochladen\"** для загрузки СТС (документа на транспортное средство).\n"
            "     Система автоматически извлекает VIN/KBA/TSN и подбирает детали под конкретный автомобиль.\n"
            "   • Также там можно загрузить фото детали и в строке поиска рядом указать её название.\n\n"
            "2) Есть вкладка **\"Manuelle Suchen\"**:\n"
            "   • В поле **\"KBA\"** вводятся 4 цифры из документа.\n"
            "   • В поле **\"TSN\"** — первые 3 символа (буквы/цифры), например: **0603 BRA**.\n"
            "   • После этого в строке поиска вводится название детали (например, \"Bremsbeläge\" или "
            "\"tормозные колодки\").\n\n"
            "3) Когда пользователь спрашивает, где найти KBA/TSN в документе:\n"
            "   • Объясни, что KBA — это 4-значный код, TSN — 3 символа (буквы/цифры).\n"
            "   • Скажи, что они обычно находятся в СТС/регистрационном документе рядом с данными автомобиля, "
            "но не выдумывай точную верстку полей.\n\n"

            "Всегда:\n"
            "- Отвечай дружелюбно и понятно.\n"
            "- Если объясняешь шаги на сайте — используй точные немецкие названия вкладок, кнопок и полей "
            "(\"Automatisches Suchen\", \"Manuelle Suchen\", \"Dokument hochladen\", \"KBA\", \"TSN\" и т.п.), "
            "НЕ переводи эти названия.\n"
            "- Не пиши префиксы 'AI:' или 'Assistant:'. Просто текст ответа.\n\n"

            f"Тема тикета: {ticket.subject}\n\n"
            "История диалога:\n"
            f"{history}\n\n"
            "Ответ:"
        )

        try:
            logger.debug(
                "[SupportAI] Generating reply for ticket_id={} message_id={}",
                ticket.id,
                new_user_message.id,
            )
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            answer = (resp.choices[0].message.content or "").strip()
            logger.info("[SupportAI] Generated reply for ticket_id={}", ticket.id)
            return answer
        except Exception as e:
            logger.error("[SupportAI] Error generating reply: {}", e)
            return (
                "Leider ist ein technischer Fehler bei der automatischen Antwort aufgetreten. "
                "Bitte versuchen Sie es später noch einmal oder wenden Sie sich direkt an unseren Support."
            )
