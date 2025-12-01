import uuid

from agents import Runner
from app.agents_tools.image_identifier import ImagePartIdentifierAgent
from app.agents_tools.ocr import GoogleVisionOCRAgent, SparrowOCRAgent
from app.agents_tools.parser import AutoteileMarktParserAgent
from app.agents_tools.part_text import TextPartIdentifierAgent
from app.schemas.ai_schemas import OEMRequest, QueryRequest
from app.utils.llm_buffer import temp_storage
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger

router = APIRouter(prefix="/tools", tags=["Agent Tools"])

# ─────────────────────────────────────────────────────────────────────────────


# @router.post("/llm/query", summary="Run LLM text-only prompt")
# async def query_llm(request: QueryRequest):
#     """
#     Send a plain text prompt to the LLM agent and return the generated response.

#     Source: GPT agent (LLM)
#     Input: { input: str }
#     Output: { response: str }
#     """
#     result = await Runner.run(agent, input=request.input)
#     return {"response": result.final_output}


@router.post("/llm/query-with-image", summary="Run LLM prompt with image")
async def query_llm_with_image(input: str = Form(...), image: UploadFile = File(...)):
    """
    Send a text prompt and image to the LLM agent. The image is passed as buffer_id.

    Source: GPT agent (LLM)
    Form fields:
    - input: prompt text
    - image: UploadFile

    Returns: { buffer_id: str, response: str }
    """
    image_bytes = await image.read()
    buffer_id = str(uuid.uuid4())
    temp_storage.put(buffer_id, image_bytes, ttl=300)
    full_prompt = f"{input.strip()}\nbuffer_id: {buffer_id}"
    result = await Runner.run(agent, input=full_prompt)
    return {"buffer_id": buffer_id, "response": result.final_output}


@router.post("/identify/text", summary="Identify part type from text")
async def identify_part_from_text(text_query: str):
    """
    Identify a car part type based on text description.

    Source: Rule-based agent
    Input: text_query: str
    Output: { part_type: str }
    """
    agent = TextPartIdentifierAgent()
    part_type = await agent.identify_part_type(text_query)
    if not part_type:
        raise HTTPException(status_code=500, detail="Failed to identify part type")
    return {"part_type": part_type}


@router.post("/identify/image", summary="Identify part type from image")
async def identify_part_from_image(file: UploadFile = File(...)):
    """
    Identify a car part type using image embedding + Qdrant similarity search.

    Source: CLIP + Qdrant
    Input: file: UploadFile
    Output: { identified_part_type: str }
    """
    agent = ImagePartIdentifierAgent()
    image_bytes = await file.read()
    part_type = await agent.identify(image_bytes)
    return {"status": "success", "identified_part_type": part_type}


@router.post("/identify/ocr", summary="Extract VIN/KBA from image using OCR")
async def identify_from_ocr(file: UploadFile = File(...)):
    """
    Extract vehicle data (VIN, KBA, etc.) from an uploaded image using Google Vision OCR.
    Falls back to Sparrow OCR if Google Vision fails.

    Input: file: UploadFile (e.g. photo of registration or part)
    Output: { status: "success", vin: str | None, kba: dict | None }
    """
    agent = GoogleVisionOCRAgent()
    ocr_reserve_agent = SparrowOCRAgent()
    image_bytes = await file.read()

    try:
        result = await agent.extract_vehicle_data(image_bytes)
        if result == {}:
            raise Exception
        logger.info(f"[OCR][Google] Result: {result}")
    except Exception as err:
        logger.warning(f"[OCR][Google] Failed: {err}")
        result = await ocr_reserve_agent.extract_vehicle_data(image_bytes)
        logger.info(f"[OCR][Sparrow] Result: {result}")

    logger.debug(f"result is {result}")

    return {"status": "success", "vin": result.get("vin"), "kba": result.get("kba")}


@router.post("/search/parse_market", summary="Search parts from marketplace by OEM")
async def search_parts_from_marketplace(request: OEMRequest):
    """
    Use AutoteileMarkt parser to fetch product listings for given OEM.

    Source: HTML parser (AutoteileMarkt.de) + Redis cache
    Input: { oem_number: str, max_products: int }
    Output: List of parsed product info
    """
    agent = AutoteileMarktParserAgent()
    parts = await agent.search_parts_by_oem(request.oem_number, request.max_products)
    if not parts:
        raise HTTPException(status_code=500, detail="Failed to fetch parts data")
    return parts

