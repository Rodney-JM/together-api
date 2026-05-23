from uuid import UUID
from app.domain.models.user import User
from app.core.exceptions import ForbiddenError

def assert_couple_ownership(resource_couple_id: UUID, user: User) -> None:
    if resource_couple_id != user.couple_id:
        raise ForbiddenError()