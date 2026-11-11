"""Domain errors raised by the service layer.

Services describe *what* went wrong; ``register_exception_handlers`` translates
each error into an HTTP response, so business logic never depends on FastAPI.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND


class AuthenticationError(DomainError):
    status_code = status.HTTP_401_UNAUTHORIZED


class PermissionDeniedError(DomainError):
    status_code = status.HTTP_403_FORBIDDEN


class ConflictError(DomainError):
    """The request is valid but conflicts with the current state of a resource."""

    status_code = status.HTTP_409_CONFLICT


class ValidationError(DomainError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


async def _handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _handle_domain_error)
