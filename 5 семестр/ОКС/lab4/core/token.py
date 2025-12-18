from typing import Optional, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from .station import Message

class Token:
    def __init__(self):
        self.is_free = True
        self.message: Optional["Message"] = None
        self.current_holder: Optional[int] = None
        self.last_updated = time.time()
        self.is_corrupted = False
        self.monitor_bit = False

    def __repr__(self):
        status = "FREE" if self.is_free else "BUSY"
        monitor = "M" if self.monitor_bit else "-"
        return f"Token({status} [{monitor}])"