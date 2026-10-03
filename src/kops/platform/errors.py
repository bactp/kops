"""API errors in the contract's shape: {"error": code, "detail": text}."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

STATUS = {"unauthenticated": 401, "forbidden": 403, "not_found": 404, "quota_exceeded": 409,
          "capacity_exceeded": 503, "bad_state": 409, "invalid_request": 422, "provider_error": 502}


class ApiError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, STATUS[code]


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(_: Request, e: ApiError):
        return JSONResponse({"error": e.code, "detail": e.detail}, status_code=e.status)

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, e: RequestValidationError):
        msg = "; ".join(f"{'.'.join(str(p) for p in x['loc'][1:])}: {x['msg']}" for x in e.errors())
        return JSONResponse({"error": "invalid_request", "detail": msg}, status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException):
        code = {401: "unauthenticated", 403: "forbidden", 404: "not_found"}.get(e.status_code, "invalid_request")
        return JSONResponse({"error": code, "detail": str(e.detail)}, status_code=e.status_code)
