from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


user_repository = UserRepository(User)


async def ensure_clerk_user(db: AsyncSession, user_id: str) -> User:
    existing = await user_repository.get(db, user_id)
    if existing:
        return existing
    user = User(
        id=user_id,
        full_name="Player",
        first_name="",
        last_name="",
        email=None,
        avatar_url=None,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
