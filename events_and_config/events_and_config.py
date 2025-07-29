
from dataclasses import dataclass
from PIL import Image, ImageTk

# -----------------------------
# config.py
# -----------------------------

@dataclass
class Config:
    device_serial: str = "192.168.1.2:5555"
    host: str = "127.0.0.1"
    port: int = 1234
    window_title: str = "scrcpy Real-Time Stream (Low Latency)"
    window_size: tuple[int, int] = (360, 800)
    max_fps: int = 1000

# -----------------------------
# core/events.py
# -----------------------------

@dataclass
class ClickEvent:
    x: int
    y: int


