
import socket
import threading
import av
from PIL import Image, ImageTk
from typing import Callable, Optional, TypeAlias

from events_and_config.events_and_config import Config

# -----------------------------
# services/stream_client_service.py
# -----------------------------

DecodedFrameCallback: TypeAlias = Callable[[Image.Image], None]

class VideoReceiverService:
    """Receives and decodes H.264 frames over TCP from scrcpy."""
    
    def __init__(self, config: Config):
        self.config = config
        self.codec = av.CodecContext.create("h264", "r")
        self.worker_thread: Optional[threading.Thread] = None
        self._running = False
        self.latest_frame: Optional[Image.Image] = None
        self._frame_updated = False
        self._lock = threading.Lock()
    
    def start_streaming(self) -> None:
        self._running = True
        self.worker_thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.worker_thread.start()
    
    def stop_streaming(self) -> None:
        self._running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
    
    """ PRIVATE METHODS """

    def _stream_worker(self) -> None:
        sock = None
        try:
            print(f"[*] Connecting to scrcpy server at {self.config.host}:{self.config.port}...")
            sock = socket.create_connection((self.config.host, self.config.port))
            print("[*] Connected! Waiting for video stream...")
            
            while self._running:
                data = sock.recv(4096)
                if not data:
                    print("NO DATA BREAKING")
                    break
                
                try:
                    packets = self.codec.parse(data)
                    self._frame_updated=True
                    for packet in packets:
                        frames = self.codec.decode(packet)
                        last_frame=frames[-1]
                        if last_frame:
                            with self._lock:
                                self.latest_frame=last_frame.to_image()
                except Exception as e:
                    print(f"[!] Decode error: {e}")
                    
        except Exception as e:
            print(f"[!] Stream worker error: {e}")
        finally:
            if sock:
                sock.close()
            print("[*] Stream worker finished.")

    """ SETTER """

    def get_frame(self):
        if not self._frame_updated:
            return None
        self._frame_updated=False
        with self._lock:
            return self.latest_frame