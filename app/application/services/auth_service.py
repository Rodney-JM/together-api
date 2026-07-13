from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.subscription_service

