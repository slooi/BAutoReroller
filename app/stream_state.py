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
        self.is_running = False
        self._lock = threading.Lock()
        self._frame_callback: Optional[Callable[[FrameEvent], None]] = None
    
    def start(self) -> None:
        self.is_running = True
    
    def stop(self) -> None:
        self.is_running = False

    """ SETTER """
    
    def set_frame(self, frame: Image.Image) -> None:
        with self._lock:
            self.latest_frame = frame

        if self._frame_callback:
            self._frame_callback(FrameEvent(frame=frame))

    """ CALLBACK FUNCTION SETTER """
    
    def set_new_frame_callback(self, callback: Callable[[FrameEvent], None]) -> None:
        self._frame_callback = callback
