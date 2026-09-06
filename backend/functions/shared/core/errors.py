"""Domain exceptions.

Services raise these. Routers translate them to HTTP — services never import HTTP concepts,
which is what keeps them testable without a request object.
"""


class DomainError(Exception):
    """Base for everything raised by a service."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.__doc__ or "")
        self.message = message or "Something went wrong."


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    """A slug collision, or a publish transition that isn't allowed."""

    status_code = 409
    code = "conflict"


class ValidationError(DomainError):
    status_code = 422
    code = "validation_error"


class PermissionDeniedError(DomainError):
    status_code = 403
    code = "permission_denied"


class RateLimitedError(DomainError):
    status_code = 429
    code = "rate_limited"
