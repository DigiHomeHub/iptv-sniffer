"""Scanner package exports."""

from .screenshot import capture_screenshot
from .strategy import ScanMode, ScanStrategy
from .template_strategy import TemplateScanStrategy
from .validator import ErrorCategory, StreamValidationResult, StreamValidator

__all__ = [
    "capture_screenshot",
    "ScanMode",
    "ScanStrategy",
    "TemplateScanStrategy",
    "ErrorCategory",
    "StreamValidationResult",
    "StreamValidator",
]
