# app/agents_tools/ocr.py
import os
import re
import time

import google.auth.exceptions
import httpx

# Если позже решим использовать Google Vision:
from google.cloud import vision
from loguru import logger

# OCR.Space API ключ (бесплатный, можно задать через .env)
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY")


def extract_relevant_block(text: str, max_lines: int = 12) -> str:
    """
    Находит блок начиная с VIN или строки 'Fahrzeug-Identifizierungsnummer'
    и ограничивает количество строк (по умолчанию 12).
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "Fahrzeug-Identifizierungsnummer" in line or re.search(
            r"[A-HJ-NPR-Z0-9]{17}", line
        ):
            block = "\n".join(lines[i : i + max_lines])
            logger.debug(f"Вырезанный блок для поиска VIN/HSN/TSN:\n{block}")
            return block
    logger.debug("VIN-блок не найден, возвращаю весь текст")
    return text


def extract_vin_kba_from_text(text: str) -> dict:
    """
    Извлекаем VIN, HSN и TSN из OCR-текста.
    VIN через регулярку, HSN из второй строки, TSN — из первой строки (4 цифры).
    """
    print("Начало парсинга текста OCR")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    print(f"Всего строк после очистки: {len(lines)}")

    vin = None
    hsn = None
    tsn = None

    # TSN ищем в первой строке (4 цифры)
    if lines:
        numbers = re.findall(r"\b\d{4}\b", lines[0])
        if len(numbers) >= 2:
            tsn = numbers[1]  # берём второе число, а не первое (2020)
            print(f"TSN найден: {tsn}")

    # HSN из второй строки (только буквы)
    if len(lines) >= 2:
        hsn_match = re.match(r"([A-Z]+)", lines[1])
        if hsn_match:
            hsn = hsn_match.group(1)
            print(f"HSN найден: {hsn}")

    # VIN по стандартному паттерну
    vin_pattern = r"\b([A-HJ-NPR-Z0-9]{17})\b"
    vin_match = re.search(vin_pattern, text)
    if vin_match:
        vin = vin_match.group(1)
        print(f"VIN найден: {vin}")

    result = {
        "vin": vin,
        "kba": {
            "hsn": hsn,
            "tsn": tsn,
        },
    }

    print(f"Результат парсинга: {result}")
    return result


class SparrowOCRAgent:
    """OCR using Sparrow OCR API for document processing on CPU."""

    async def extract_vehicle_data(self, image_bytes: bytes) -> dict:
        """
        Extract vehicle text data (e.g. VIN, KBA) using Sparrow OCR API.

        Args:
            image_bytes (bytes): Image file content.

        Returns:
            dict: Parsed data containing extracted_text and optional meta.

        Raises:
            RuntimeError: If the OCR API fails after retry attempts.
        """
        url = "http://sparrow:8001/api/v1/sparrow-ocr/inference"
        max_attempts = 2
        attempt = 1

        while attempt <= max_attempts:
            try:
                logger.info(
                    f"📄 Sending image to Sparrow OCR (Attempt {attempt}/{max_attempts})"
                )

                # Prepare multipart form data
                files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
                data = {"include_bbox": "false", "debug": "false"}

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, files=files, data=data)
                    response.raise_for_status()

                result = response.json()
                logger.debug(f"✅ OCR result: {result}")

                if not result:
                    raise ValueError("Empty response from OCR API")

                text = result[0].get("extracted_text", "")
                return extract_vin_kba_from_text(text)

            except Exception as e:
                logger.error(f"❌ Sparrow OCR API error on attempt {attempt}: {e}")
                attempt += 1

        raise RuntimeError("Sparrow OCR API failed after multiple attempts")


class OCRSpaceAgent:
    """OCR через OCR.Space (используется по умолчанию)."""

    async def extract_vehicle_data(self, image_bytes: bytes) -> dict:
        url = "https://api.ocr.space/parse/image"
        files = {"file": ("doc.jpg", image_bytes, "image/jpeg")}
        data = {"language": "en", "isOverlayRequired": False, "OCREngine": 1}
        headers = {"apikey": OCR_SPACE_API_KEY}

        try:
            logger.info("🟡 OCR.Space → Отправка изображения (1 попытка)...")

            async with httpx.AsyncClient(timeout=httpx.Timeout(1.5)) as client:
                response = await client.post(
                    url, data=data, files=files, headers=headers
                )

            if response.status_code != 200:
                raise Exception(f"OCR.Space ошибка {response.status_code}")

            parsed = response.json()

            if parsed.get("IsErroredOnProcessing") or not parsed.get("ParsedResults"):
                raise ValueError("OCR.Space вернул ошибку или пустой ParsedResults")

            text = parsed["ParsedResults"][0].get("ParsedText", "")
            logger.debug(f"📄 OCR результат: {text.strip()}")
            return extract_vin_kba_from_text(text)

        except Exception as e:
            logger.warning(f"❌ Ошибка OCR.Space, подставляем мок-ответ: {e}")
            return self._mock_vehicle_data()

    def _mock_vehicle_data(self) -> dict:
        """Мок-ответ, имитирующий результат распознавания VIN-документа."""
        mock_text = """
            Fahrzeugschein
            Zulassungsbescheinigung Teil 1

            2.1: 0600
            2.2: AHK000

            VIN: WDB9036621R123456

            Mercedes-Benz Sprinter
            Erstzulassung: 12.06.2018
        """
        logger.info("📄 Используется мок-данные OCR")
        return extract_vin_kba_from_text(mock_text)


class GoogleVisionOCRAgent:
    """OCR через Google Cloud Vision (временно не используется)."""

    def __init__(self):
        try:
            self.client = vision.ImageAnnotatorClient()
        except google.auth.exceptions.DefaultCredentialsError as e:
            logger.error(
                f"Ошибка инициализации Google Vision API: проблема с учетными данными - {str(e)}"
            )
            self.client = None  # Set client to None to indicate failure

    async def extract_vehicle_data(self, image_bytes: bytes) -> dict:
        if self.client is None:
            logger.warning("Google Vision OCR недоступен из-за ошибки учетных данных")
            return {}  # Return empty dict as fallback

        logger.info("Google Vision → Запрос OCR...")
        start = time.perf_counter()

        try:
            image = vision.Image(content=image_bytes)
            response = self.client.text_detection(image=image)

            text = (
                response.full_text_annotation.text if response.text_annotations else ""
            )
            logger.info(f"⏱Google OCR ответ за {time.perf_counter() - start:.2f} сек")
            logger.debug(f"OCR текст (Google): {text.strip()}")

            return extract_vin_kba_from_text(text)
        except Exception as e:
            logger.error(f"Ошибка при выполнении OCR через Google Vision: {str(e)}")
            return {}  # Return empty dict as fallback
