from clerk_backend_api import Clerk
from app.core.config import settings

clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)