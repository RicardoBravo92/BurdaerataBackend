from clerk_backend_api import Clerk
from app.core.config import get_settings

def get_clerk_client() -> Clerk:
    settings = get_settings()
    return Clerk(bearer_auth=settings.CLERK_SECRET_KEY)

clerk_client = get_clerk_client()
