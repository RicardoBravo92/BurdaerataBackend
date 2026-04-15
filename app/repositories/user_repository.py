from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.repositories.base_repository import BaseRepository
from app.core.clerk import clerk_client


class UserRepository(BaseRepository[User]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


user_repository = UserRepository(User)


async def ensure_clerk_user(db: AsyncSession, user_id: str) -> User:
    user = await user_repository.get(db, user_id)
    
    # If the user doesn't exist OR they have the default "Player" name, fetch from Clerk
    if not user or user.full_name == "Player":
        try:
            clerk_user = await clerk_client.users.get_async(user_id=user_id)
            
            first_name = clerk_user.first_name or ""
            last_name = clerk_user.last_name or ""
            full_name = f"{first_name} {last_name}".strip() or "Player"
            email = None
            if clerk_user.email_addresses:
                email = clerk_user.email_addresses[0].email_address
            
            if not user:
                user = User(
                    id=user_id,
                    full_name=full_name,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    avatar_url=clerk_user.image_url,
                )
                db.add(user)
            else:
                user.full_name = full_name
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.avatar_url = clerk_user.image_url
                db.add(user)
                
        except Exception:
            if not user:
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
        if user:
            await db.refresh(user)
            
    return user
