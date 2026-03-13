class AesironError(ValueError):
    """Base error for domain-level failures."""


class AppNotFoundError(AesironError):
    """Raised when the requested app cannot be found."""


class AppAlreadyExistsError(AesironError):
    """Raised when trying to create or rename to an existing app."""


class DockerResourceError(AesironError):
    """Raised for Docker resource lookup failures."""
