from __future__ import annotations

import uuid
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError
from app.core.logging_config import get_logger

logger = get_logger(__name__)
PRESIGNED_URL_TTL = 3600
_client = None

def _get_client():
    global _client
    if _client is None:
        kw: dict = {
            "service_name" : "s3",
            "region_name" : settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY
        }
        
        if settings.AWS_S3_ENDPOINT_URL:
            kw["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
        _client = boto3.client(**kw)
    return _client

def _detect_mime(content: bytes) -> str:
    try: 
        import magic
        return magic.from_buffer(
            content[:2048], mime=True
        )
    except ImportError:
        import mimetypes
        return "application/octet-stream"
    
async def upload_file(file: UploadFile, couple_id: uuid.UUID, namespace: str) -> tuple[str, int]:
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise FileTooLargeError(settings.MAX_UPLOAD_SIZE_MB)
    
    detected = _detect_mime(content)
    allowed = settings.allowed_image_type_list
    if detected not in allowed:
        raise InvalidFileTypeError(allowed)
    
    ext = Path(file.filename or "upload").suffix.lower()
    key = f"couples/{couple_id}/{namespace}/{uuid.uuid4().hex}{ext}"
    
    try:
        _get_client().put_object(
            Bucket=settings.AWS_S3_BUCKET, Key=key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
            ServerSideEncryption="AES256",
            Metadata={"couple-id": couple_id}
        )
    except (ClientError, BotoCoreError) as exc:
        logger.error("s3_upload_failed", key=key, error=str(exc))
        raise
    
    return key, len(content)

def get_presigned_url(key: str, expires: int = PRESIGNED_URL_TTL) -> str:
    try:
        return _get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
            ExpiresIn=expires,
        )
    except Exception as exc:
        logger.error("presigned_url_failed", key=key, error=str(exc))
        return ""

def delete_file(key: str) -> None:
    try:
        _get_client().delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
    except Exception as exc:
        logger.error("s3_delete_failed", key=key, error=str(exc))