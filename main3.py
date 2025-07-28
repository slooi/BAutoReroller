# -----------------------------
# config.py
# -----------------------------
from dataclasses import dataclass
import socket
import threading
import av
from typing import Callable, Optional, Protocol, TypeAlias
from icecream import ic
import subprocess
import tkinter as tk
from PIL import Image, ImageTk
import time

@dataclass
class Config:
    device_serial: str = ""
    host: str = "127.0.0.1"
    port: int = 1234
    window_title: str = "scrcpy Real-Time Stream (Low Latency)"
    window_size: tuple[int, int] = (360, 800)
    max_fps: int = 30


# -----------------------------
# core/events.py
# -----------------------------

@dataclass
class ClickEvent:
    x: int
    y: int

@dataclass
class FrameEvent:
    frame: Image.Image


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
    
    def get_latest_frame(self) -> Optional[Image.Image]:
        with self._lock:
            return self.latest_frame
    
    def update_frame(self, frame: Image.Image) -> None:
        with self._lock:
            self.latest_frame = frame

        if self._frame_callback:
            self._frame_callback(FrameEvent(frame=frame))
    
    def start(self) -> None:
        self.is_running = True
    
    def stop(self) -> None:
        self.is_running = False
    
    def set_new_frame_callback(self, callback: Callable[[FrameEvent], None]) -> None:
        self._frame_callback = callback


# -----------------------------
# services/adb_service.py
# -----------------------------

class ADBService:
    """Handles ADB tap commands via subprocess."""
    
    def __init__(self, device_serial: str = ""):
        self.device_serial = device_serial
    
    def tap(self, x: int, y: int) -> None:
        threading.Thread(
            target=self._tap_worker,
            args=(x, y),
            daemon=True
        ).start()
        
    """ PRIVATE METHODS """
    
    def _tap_worker(self, x: int, y: int):
        device_cmd = f"-s {self.device_serial} " if self.device_serial else ""
        cmd = f"adb {device_cmd}shell input tap {x} {y}"
        ic(f"ADB tap: {x}, {y}")
        ic(f"Command: {cmd}")
        subprocess.run(cmd, check=True)


# -----------------------------
# services/scrcpy_server_service.py
# -----------------------------

class ScrcpyServerService:
    """Starts/stops the scrcpy server via adb."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
    
    def start_server(self) -> None:
        server_thread = threading.Thread(target=self._start_server_worker)
        server_thread.start()
        server_thread.join()
        time.sleep(0.1)

    def stop_server(self) -> None:
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    """ PRIVATE METHODS """

    def _start_server_worker(self):
        print("[*] Setting up scrcpy server")
        subprocess.run("adb forward tcp:1234 localabstract:scrcpy", check=True)

        print("[*] Starting scrcpy server...")
        cmd = (
            "adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar "
            "app_process / com.genymobile.scrcpy.Server 3.3.1 "
            "tunnel_forward=true audio=false control=false "
            "cleanup=false raw_stream=true max_size=1920"
        )

        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if self.process.stdout:
            for line in self.process.stdout:
                print(f"[SERVER]: {line.strip()}")
                if "[server] INFO: Device:" in line:
                    print("[*] Scrcpy server setup complete")
                    return
    

# -----------------------------
# services/stream_client_service.py
# -----------------------------
DecodedFrameCallback = Callable[[Image.Image], None]
class StreamClientService:
    """Receives and decodes H.264 frames over TCP from scrcpy."""
    
    def __init__(self, config: Config, state: StreamState):
        self.config = config
        self.stream_state = state
        self.codec = av.CodecContext.create("h264", "r")
        self.worker_thread: Optional[threading.Thread] = None
    
    def start_streaming(self) -> None:
        self.worker_thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.worker_thread.start()
    
    def stop_streaming(self) -> None:
        self.stream_state.stop()
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
    
    """ PRIVATE METHODS """

    def _stream_worker(self) -> None:
        sock = None
        try:
            print(f"[*] Connecting to scrcpy server at {self.config.host}:{self.config.port}...")
            sock = socket.create_connection((self.config.host, self.config.port))
            print("[*] Connected! Waiting for video stream...")
            
            while self.stream_state.is_running:
                data = sock.recv(4096)
                if not data:
                    print("NO DATA BREAKING")
                    break
                
                try:
                    packets = self.codec.parse(data)
                    for packet in packets:
                        frames = self.codec.decode(packet)
                        for frame in frames:
                            self.stream_state.update_frame(frame.to_image())
                except Exception as e:
                    print(f"[!] Decode error: {e}")
                    
        except Exception as e:
            print(f"[!] Stream worker error: {e}")
        finally:
            if sock:
                sock.close()
            self.stream_state.stop()
            print("[*] Stream worker finished.")


# -----------------------------
# ui/stream_view.py
# -----------------------------
ClickCallback: TypeAlias = Callable[[ClickEvent], None]
class StreamView:
    """Tkinter GUI that displays frames and captures clicks."""
    
    def __init__(self, config: Config):
        self.config = config
        self.root = tk.Tk()
        self.root.geometry(f"{config.window_size[0]}x{config.window_size[1]}")
        self.root.title(config.window_title)
        
        self.label = tk.Label(self.root)
        self.label.pack()
        
        self._click_callback: Optional[ClickCallback] = None
        self._close_callback: Optional[Callable] = None
        
        self.label.bind("<Button-1>", self._on_click)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def update_frame(self, frame: Image.Image) -> None:
        photo_img = ImageTk.PhotoImage(image=frame)
        self.label.config(image=photo_img)
        self.label.image = photo_img # type: ignore # Prevent GC
    
    def start(self) -> None:
        self.root.mainloop()
    
    def close(self) -> None:
        self.root.destroy()
    
    """ CALLBACK FUNCTIONS """

    def _on_click(self, event) -> None:
        if self._click_callback:
            click_event = ClickEvent(x=event.x, y=event.y)
            self._click_callback(click_event)
    
    def _on_close(self) -> None:
        print("[!] Window closed, shutting down.")
        if self._close_callback:
            self._close_callback()
            
    """ Callback Function Setters """

    def set_click_callback(self,callback:ClickCallback):
        self._click_callback=callback

    def set_close_callback(self, callback: Callable) -> None:
        self._close_callback = callback
    


# -----------------------------
# app/controller.py
# -----------------------------

class Controller():
    """Main controller that wires together view, state, and services."""
    
    def __init__(self, config: Config):
        self.config = config
        self.stream_state = StreamState()
        self.view = StreamView(config)

        """ Setup Services """
        self.adb_service = ADBService(config.device_serial)
        self.scrcpy_service = ScrcpyServerService()
        self.stream_service = StreamClientService(config, self.stream_state)
        
        """ Setup Callbacks """
        self.view.set_click_callback(self.on_click)
        self.stream_state.set_new_frame_callback(self.on_new_frame)
        self.view.set_close_callback(self.stop)
    
    def start(self) -> None:
        self.scrcpy_service.start_server()

        self.stream_state.start()
        self.stream_service.start_streaming()
        self.view.start()
    
    def stop(self) -> None:
        self.stream_service.stop_streaming()
        self.scrcpy_service.stop_server()
        self.view.close()
    
    """ CALLBACK FUNCTIONS """

    def on_new_frame(self, event: FrameEvent) -> None:
        self.view.update_frame(event.frame)
    
    def on_click(self, event: ClickEvent) -> None:
        self.adb_service.tap(event.x,event.y)


# -----------------------------
# main.py
# -----------------------------

def main():
    config = Config()
    controller = Controller(config)
    controller.start()

if __name__ == "__main__":
    main()
