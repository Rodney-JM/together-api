from typing import Annotated
from fastapi import Depends
from uuid import UUID

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.infra.db.session import get_db_session
from app.infra.repositories.user_repo import UserRepository
from app.domain.models.user import User
from app.core.exceptions import UnauthorizedError
from app.core.security import verify_token

bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    db=Depends(get_db_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
) -> User:
    if not credentials:
        raise UnauthorizedError()
    payload = verify_token(credentials.credentials, token_type="access")
    user = await UserRepository(db).get_by_id(UUID(payload["sub"]))
    if not user or not user.is_active:
        raise UnauthorizedError()
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]