import threading
from PIL import Image, ImageTk
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, TypeAlias

from events_and_config.events_and_config import FrameEvent

# -----------------------------
# app/stream_state.py
# -----------------------------

class StreamState:
    """Holds current decoded video frame and running state (thread-safe)."""
    
    def __init__(self):
        self.latest_frame: Optional[Image.Image] = None
        self._lock = threading.Lock()

    """ SETTER """

    def get_frame(self):
        with self._lock:
            return self.latest_frame
    
    def set_frame(self, frame: Image.Image) -> None:
        with self._lock:
            self.latest_frame = frame