"""exceptions — domain level errors for file upload."""
from __future__ import annotations


class DomainError(Exception):
    """Base domain exception."""
    pass


class InvalidFileNameError(DomainError):
    """Raised when original filename is empty or invalid."""
    pass


class InvalidStatusTransitionError(DomainError):
    """Raised when an illegal lifecycle state transition is attempted."""
    pass
