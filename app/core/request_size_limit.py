from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limit request body size to prevent DoS via large payloads.

    Default limits:
    - JSON: 1 MB
    - Form/multipart: 10 MB
    - Other: 1 MB
    """

    def __init__(
        self,
        app,
        max_json_size: int = 1_048_576,  # 1 MB
        max_form_size: int = 10_485_760,  # 10 MB
        max_other_size: int = 1_048_576,  # 1 MB
    ):
        super().__init__(app)
        self.max_json_size = max_json_size
        self.max_form_size = max_form_size
        self.max_other_size = max_other_size

    async def dispatch(self, request: Request, call_next):
        content_type = request.headers.get("content-type", "").lower()
        content_length = request.headers.get("content-length")

        # If no content-length, we can't check upfront - Starlette will handle streaming
        if content_length is None:
            return await call_next(request)

        try:
            length = int(content_length)
        except ValueError:
            return await call_next(request)

        # Determine limit based on content type
        if "application/json" in content_type:
            limit = self.max_json_size
        elif (
            "multipart/form-data" in content_type
            or "application/x-www-form-urlencoded" in content_type
        ):
            limit = self.max_form_size
        else:
            limit = self.max_other_size

        if length > limit:
            return JSONResponse(
                status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "detail": f"Request body too large. Maximum size: {limit} bytes"
                },
            )

        return await call_next(request)
