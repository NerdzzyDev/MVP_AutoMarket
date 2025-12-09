# app/core/error_handlers.py
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger


def _build_user_message_de(status_code: int) -> str:
    """
    Простая мапа: по статус-коду → дефолтное сообщение на немецком.
    Можно расширять/кастомизировать.
    """
    if status_code == 400:
        return (
            "Die Anfrage enthält ungültige oder unvollständige Daten. "
            "Bitte überprüfen Sie Ihre Eingaben."
        )
    if status_code == 401:
        return (
            "Sie sind nicht angemeldet. Bitte melden Sie sich an und versuchen Sie es erneut."
        )
    if status_code == 403:
        return (
            "Sie haben keine Berechtigung, diese Aktion auszuführen."
        )
    if status_code == 404:
        return (
            "Die angeforderte Ressource wurde nicht gefunden. "
            "Bitte prüfen Sie die Angaben oder laden Sie die Seite neu."
        )
    # всё 5xx
    if 500 <= status_code < 600:
        return (
            "Es ist ein technischer Fehler aufgetreten. "
            "Bitte versuchen Sie es später erneut. "
            "Wenn das Problem weiterhin besteht, wenden Sie sich bitte an den Support."
        )

    # дефолт для остальных
    return (
        "Es ist ein Fehler aufgetreten. "
        "Bitte versuchen Sie es später erneut."
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Глобальный обработчик HTTPException.
    Нормализует detail в объект с полями:
    - error: для логов/дебага
    - user_message_de: для отображения на фронте
    """
    logger.warning(
        "[HTTPException] path={} status={} detail={}",
        request.url.path,
        exc.status_code,
        exc.detail,
    )

    # detail может быть строкой, dict, чем угодно
    if isinstance(exc.detail, dict):
        error_payload: dict[str, Any] = dict(exc.detail)
        # если разработчик уже сам задал user_message_de — не трогаем
        if "user_message_de" not in error_payload:
            error_payload["user_message_de"] = _build_user_message_de(exc.status_code)
    else:
        # detail строка/что-то ещё → оборачиваем
        error_payload = {
            "error": str(exc.detail),
            "user_message_de": _build_user_message_de(exc.status_code),
        }

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": error_payload},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный обработчик любых неожиданных Exception.
    Всегда отдаёт 500 с дружелюбным немецким текстом.
    """
    logger.exception(
        "[UnhandledException] path={} error={}",
        request.url.path,
        exc,
    )

    status_code = 500
    error_payload = {
        "error": "Unhandled server error",
        "user_message_de": _build_user_message_de(status_code),
    }

    return JSONResponse(
        status_code=status_code,
        content={"detail": error_payload},
    )
