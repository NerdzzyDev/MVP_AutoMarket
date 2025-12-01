import io

import torch
from PIL import Image
from qdrant_client import QdrantClient
from transformers import CLIPModel, CLIPProcessor


class ImagePartIdentifierAgent:
    """Определяет тип детали по изображению через CLIP + Qdrant."""

    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.client = QdrantClient(
            host="qdrant", port=6333
        )  # важно: хост — как в docker-compose
        self.collection_name = "oem_nums"

    # def _extract_car_part_type(self, image_path: str) -> str:
    #     match = re.search(r"/([A-Z ]+)/\d+\.jpg$", image_path)
    #     if match:
    #         return match.group(1)
    #     return "UNKNOWN"

    async def identify(self, image_bytes: bytes) -> str:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            embedding = self.model.get_image_features(**inputs)
            embedding = embedding / embedding.norm(p=2, dim=-1, keepdim=True)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding[0].tolist(),
            limit=1,
        )

        # if results:
        #     print(f"res = {results}")
        #     return self._extract_car_part_type(results[0].payload.get("image_path", ""))
        # return "UNKNOWN"

        if results:
            # Вернем весь первый результат как словарь
            scored_point = results[0]
            # Для удобства преобразуем ScoredPoint в dict с нужными полями
            result_dict = {
                "id": scored_point.id,
                "version": scored_point.version,
                "score": scored_point.score,
                "payload": scored_point.payload,
                # Можно добавить другие поля, если нужны
            }
            return result_dict

        return "UNKNOWN"
