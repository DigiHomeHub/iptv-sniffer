"""Scanner package exports."""

from .screenshot import capture_screenshot
from .strategy import ScanMode, ScanStrategy
from .validator import ErrorCategory, StreamValidationResult, StreamValidator

__all__ = [
    "capture_screenshot",
    "ScanMode",
    "ScanStrategy",
    "ErrorCategory",
    "StreamValidationResult",
    "StreamValidator",
]
