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