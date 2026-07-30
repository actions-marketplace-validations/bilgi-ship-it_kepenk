class KepenkError(Exception):
    """Base exception for expected Kepenk failures."""


class PolicyError(KepenkError):
    """Raised when a policy is missing, malformed, or unsupported."""


class AuditError(KepenkError):
    """Raised when an audit chain cannot be written or verified."""
