import os

from loguru import logger
from openai import AsyncOpenAI


class TextPartIdentifierAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set!")
        self.client = AsyncOpenAI(api_key=api_key)

    async def normalize_query(self, text_query: str) -> str:
        """Normalize and translate part type query for fuzzy matching."""
        prompt = (
            "You are a helpful assistant. Your task is to normalize an automotive part name "
            "so it can be matched with German product titles.\n\n"
            "Remove brand names, fix spelling errors, and if in English, translate to German.\n"
            "Return only 2-4 normalized words in German. No explanations.\n\n"
            f"Query: {text_query}\n\n"
            "Output:"
        )

        try:
            logger.debug(f"Normalizing query: {text_query}")
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=20,
            )
            normalized = response.choices[0].message.content.strip()
            logger.info(f"Normalized query: {normalized}")
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing query: {e}")
            return text_query  # fallback


### --- OLLAMA 3.1 --- ###
# # app/agents/part_text.py
# import asyncio
# import os
# import re

# import httpx
# from loguru import logger
# from ollama import AsyncClient


# class TextPartIdentifierAgent:
#     def __init__(
#         self,
#         ollama_host: str = os.getenv("OLLAMA_HOST", "http://ollama:11434"),
#         model: str = os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
#     ):
#         self.client = AsyncClient(host=ollama_host)
#         self.model = model
#         logger.info(f"Initialized TextPartIdentifierAgent with host={ollama_host}, model={model}")


#     async def identify_part_type(self, text_query: str) -> str | None:
#         """Normalize and classify the text query to identify the standardized part type."""
#         if not text_query:
#             logger.warning("Empty text query provided")
#             return None

#         # Simplified and strict prompt for Ollama
#         prompt = (f"You are an AI assistant that classifies automotive parts based on user queries.\n"
#                     f"Classify the following query into one of these categories:\n"
#                     f"[\"headlight\", \"brake pad\", \"oil filter\", \"spark plug\", \"brake disc\", \"air filter\", \"windshield wiper\", \"battery\", \"tire\", \"shock absorber\", \"other\"]\n\n"
#                     f"Query: {text_query}\n\n"
#                     f"Return ONLY the category name. No explanations, no formatting, no examples — just the category name.")

#         try:
#             logger.debug(f"Processing text query: {text_query}")
#             response = await self.client.generate(model=self.model, prompt=prompt)
#             raw_response = response["response"].strip()
#             logger.debug(f"Raw model response: {raw_response}")

#             # Post-process the response to extract only the category
#             # Look for a category in the response (case-insensitive)
#             valid_categories = [
#                 "headlight",
#                 "brake pad",
#                 "oil filter",
#                 "spark plug",
#                 "brake disc",
#                 "air filter",
#                 "windshield wiper",
#                 "battery",
#                 "tire",
#                 "shock absorber",
#                 "other",
#             ]
#             for category in valid_categories:
#                 if re.search(rf"\b{category}\b", raw_response, re.IGNORECASE):
#                     logger.info(f"Identified part type: {category}")
#                     return category

#             # If no category is found, try to extract the last line or a single word
#             last_line = raw_response.split("\n")[-1].strip()
#             if last_line in valid_categories:
#                 logger.info(f"Identified part type from last line: {last_line}")
#                 return last_line

#             # Fallback to "other" if no valid category is found
#             logger.warning(f"No valid category found in response: {raw_response}, returning 'other'")
#             return "other"

#         except Exception as e:
#             logger.error(f"Error in TextPartIdentifierAgent: {e!s}")
#             return None
