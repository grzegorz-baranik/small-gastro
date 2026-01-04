"""
Middleware for the FastAPI application.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.i18n import parse_accept_language, set_language


class LanguageMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and set the language for each request.

    Reads the Accept-Language header and sets the language context variable.
    """

    async def dispatch(self, request: Request, call_next):
        # Get Accept-Language header
        accept_language = request.headers.get("Accept-Language", None)

        # Parse and set the language
        lang = parse_accept_language(accept_language)
        set_language(lang)

        # Process the request
        response = await call_next(request)

        # Add Content-Language header to response
        response.headers["Content-Language"] = lang

        return response
