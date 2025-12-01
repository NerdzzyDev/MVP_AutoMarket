# from app.core.orchestrator import AgentOrchestrator
# from app.models.schemas import FullResponse
# from fastapi import APIRouter, File, Form, HTTPException, UploadFile
# from fastapi.responses import JSONResponse
# from loguru import logger

# router = APIRouter(tags=["AI Agents"])
# # router = APIRouter(tags=["Without AI Agents"])


# @router.post(
#     "/search-parts",
#     response_model=FullResponse,
#     summary="Search for car parts by VIN/KBA and part details",
# )
# async def search_parts(
#     registration_document_image: UploadFile = File(...),
#     part_image: UploadFile | None = File(default=None),
#     part_text_query: str | None = Form(default=None),
# ):
#     if isinstance(part_image, UploadFile) and part_image.filename == "":
#         part_image = None

#     if not part_image and not part_text_query:
#         raise HTTPException(
#             status_code=400,
#             detail="Нужно указать либо part_image, либо part_text_query",
#         )

#     doc_bytes = await registration_document_image.read()
#     image_bytes = await part_image.read() if part_image else None

#     orchestrator = AgentOrchestrator()

#     result = await orchestrator.full_pipeline(
#         registration_doc=doc_bytes,
#         part_image=image_bytes,
#         part_text_query=part_text_query,
#     )

#     # Проверим, что статус успешный
#     if result.get("status") != "ok":
#         raise HTTPException(
#             status_code=500, detail=result.get("error", "Ошибка агента")
#         )

#     logger.debug(f"response {result}")

#     # Вернём ответ агента напрямую, без изменений
#     return JSONResponse(content=result)


# # @router.post("/search-parts", response_model=FullResponse, summary="Search for car parts by VIN/KBA and part details")
# # async def search_parts(
# #     registration_document_image: UploadFile = File(..., description="Image of registration document."),  # noqa: B008
# #     part_image: UploadFile | None = File(default=None, description="Optional. Image of the car part."),  # noqa: B008
# #     part_text_query: str | None = Form(default=None, description="Optional. Text description of the part."),
# # ):
# #     # 🛡️ Защита от пустого файла
# #     if isinstance(part_image, UploadFile) and part_image.filename == "":
# #         logger.warning("Empty part_image received - treating as None")
# #         part_image = None

# #     # 🚫 Проверка: нужно хотя бы одно из part_image или part_text_query
# #     if not part_image and not part_text_query:
# #         raise HTTPException(status_code=400, detail="Нужно указать либо part_image, либо part_text_query")

# #     doc_bytes = await registration_document_image.read()
# #     image_bytes = await part_image.read() if part_image else None

# #     orchestrator = AgentOrchestrator()

# #     try:
# #         result = await orchestrator.full_pipeline(
# #             registration_doc=doc_bytes,
# #             part_image=image_bytes,
# #             part_text_query=part_text_query,
# #         )

# #         data_raw = result.get("data")

# #         if isinstance(data_raw, str):
# #             try:
# #                 # Пробуем как один JSON
# #                 data = json.loads(data_raw)
# #             except json.JSONDecodeError:
# #                 # Пробуем распарсить несколько подряд и объединить
# #                 logger.warning("⚠️ result['data'] содержит несколько JSON-объектов подряд. Пробуем распарсить вручную.")
# #                 try:
# #                     json_chunks = re.findall(r'{.*?}(?=\s*{|\s*$)', data_raw, re.DOTALL)
# #                     data = {}
# #                     for chunk in json_chunks:
# #                         parsed = json.loads(chunk)
# #                         data.update(parsed)  # объединяем в один словарь
# #                 except Exception as e:
# #                     logger.error(f"Не удалось распарсить несколько JSON-объектов из result['data']: {e}")
# #                     raise HTTPException(status_code=500, detail="Ошибка при ручной обработке JSON-ответа")
# #         else:
# #             data = data_raw
# #         # Извлекаем products
# #         products = data.get("products", [])
# #         if isinstance(products, str):
# #             try:
# #                 products = json.loads(products)
# #             except json.JSONDecodeError as e:
# #                 logger.error(f"Failed to parse products as JSON: {e!s}")
# #                 products = []  # Fallback to empty list

# #         # Валидация продуктов с фильтрацией
# #         valid_products = []
# #         for item in products:
# #             try:
# #                 valid_products.append(PartItem(**item))
# #             except ValidationError as e:
# #                 logger.warning(f"Skipping invalid product item: {item}, error: {e!s}")
# #                 continue

# #         # Создаем результат
# #         part_search_result = PartSearchResult(
# #             vin=search_data.get("vin_recognized", ""),
# #             kba_hsn=search_data.get("kba_recognized", "0/0").split("/")[0],
# #             kba_tsn=search_data.get("kba_recognized", "0/0").split("/")[1],
# #             part_type=search_data.get("identified_part_type", ""),
# #             oem=search_data.get("oem_found", ""),
# #             products=valid_products,
# #         )

# #         return FullResponse(
# #             status="ok",
# #             result=part_search_result,
# #         )

# #     except Exception as e:
# #         logger.exception("Ошибка в обработке запроса /search-parts")
# #         return FullResponse(status="error", error=str(e))


# # @router.post("/test-text-identification")
# # async def test_text_identification(text_query: str):
# #     agent = TextPartIdentifierAgent()
# #     part_type = await agent.identify_part_type(text_query)
# #     if not part_type:
# #         raise HTTPException(status_code=500, detail="Failed to identify part type")
# #     return {"part_type": part_type}


# # @router.post("/test-parse-parts-by-oem")
# # async def search_parts_by_oem(request: OEMRequest):
# #     """Search for parts by OEM number."""
# #     agent = AutoteileMarktParserAgent()
# #     parts = await agent.search_parts_by_oem(request.oem_number, request.max_products)
# #     if not parts:
# #         raise HTTPException(status_code=500, detail="Failed to fetch parts data")
# #     return parts
