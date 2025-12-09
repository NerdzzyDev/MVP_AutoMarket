# app/utils/minio_client.py
import io
import os
from uuid import uuid4

from loguru import logger
from minio import Minio
from minio.error import S3Error
import json



MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "support-attachments")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", MINIO_ENDPOINT)


_client: Minio | None = None

def get_minio_client() -> Minio:
    global _client
    if _client is None:
        logger.info(
            "[MinIO] Initializing client: endpoint=%r secure=%s bucket=%r",
            MINIO_ENDPOINT,
            MINIO_SECURE,
            MINIO_BUCKET,
        )
        _client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        # создаём bucket при первом обращении
        try:
            if not _client.bucket_exists(MINIO_BUCKET):
                logger.info("[MinIO] Creating bucket %s", MINIO_BUCKET)
                _client.make_bucket(MINIO_BUCKET)

            # 💡 Делаем бакет публичным на чтение
            public_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"],
                    }
                ],
            }
            try:
                _client.set_bucket_policy(
                    MINIO_BUCKET,
                    json.dumps(public_policy),
                )
                logger.info("[MinIO] Public read policy set for bucket %s", MINIO_BUCKET)
            except S3Error as e:
                logger.error("[MinIO] Failed to set bucket policy: %s", e)

        except S3Error as e:
            logger.error("[MinIO] Bucket init error: %s", e)
    return _client



def build_public_url(object_name: str) -> str:
    # если MinIO за nginx, можешь тут использовать MINIO_PUBLIC_ENDPOINT="cdn.example.com"
    scheme = "https" if MINIO_SECURE else "http"
    return f"{scheme}://{MINIO_PUBLIC_ENDPOINT}/{MINIO_BUCKET}/{object_name}"


async def upload_support_file(file, ticket_id: int, user_id: int) -> str:
    """
    Принимает UploadFile.file (file-like) и загружает в MinIO.
    Возвращает публичный URL.
    """
    client = get_minio_client()
    filename = file.filename
    ext = os.path.splitext(filename)[1]
    object_name = f"tickets/{ticket_id}/{user_id}/{uuid4().hex}{ext}"

    # MinIO клиент синхронный – читаем в память, можно заменить на tmp-файл при больших объёмах
    data = await file.read()
    file_size = len(data)
    logger.info("[MinIO] Uploading object %s (size=%d bytes) to bucket=%s", object_name, file_size, MINIO_BUCKET)

    try:
        client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            data=io.BytesIO(data),
            length=file_size,
            part_size=10 * 1024 * 1024,
        )
    except Exception as e:
        logger.error("[MinIO] Error uploading object {}: {}", object_name, e)
        raise

    url = build_public_url(object_name)
    logger.info("[MinIO] Uploaded object %s → %s", object_name, url)
    return url
