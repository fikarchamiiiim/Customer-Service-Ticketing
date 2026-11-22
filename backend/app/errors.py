"""Envelope error seragam: {"error": {"code", "message", "details"}}.

Catatan: versi LENGKAP (validasi 422, 500, logging) dibuat di Step 7.
Yang ada di sini hanya yang benar-benar dibutuhkan FE sekarang:
membedakan 401 (belum login) vs 403 (tidak berhak) vs error lain.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

DEFAULT_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL",
}


def _envelope(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            code = detail.get("code") or DEFAULT_CODES.get(exc.status_code, "ERROR")
            message = detail.get("message") or str(detail)
            details = detail.get("details")
        else:
            code = DEFAULT_CODES.get(exc.status_code, "ERROR")
            message = str(detail)
            details = None
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, message, details),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope(
                "VALIDATION_ERROR",
                "Data yang dikirim tidak valid",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("INTERNAL", "Terjadi kesalahan pada server"),
        )
