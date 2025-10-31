"""Scanner package initialization."""

from .screenshot import capture_screenshot
from .validator import ErrorCategory, StreamValidationResult, StreamValidator

__all__ = [
    "StreamValidator",
    "StreamValidationResult",
    "ErrorCategory",
    "capture_screenshot",
]
