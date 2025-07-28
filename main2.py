import socket
import time
import tkinter as tk
from PIL import Image, ImageTk
import av
import threading
import subprocess
from abc import ABC, abstractmethod
from typing import Optional, Callable, Protocol
from dataclasses import dataclass
from icecream import ic


# --- Configuration ---
@dataclass
class Config:
    device_serial: str = ""
    host: str = "127.0.0.1"
    port: int = 1234
    window_title: str = "scrcpy Real-Time Stream (Low Latency)"
    window_size: tuple[int, int] = (360, 800)
    max_fps: int = 30


# --- Events ---
@dataclass
class ClickEvent:
    x: int
    y: int


@dataclass
class FrameEvent:
    frame: Image.Image


# --- Protocols ---
class ClickObserver(Protocol):
    def on_click(self, event: ClickEvent) -> None: ...


# --- MODEL ---
class StreamModel:
    """Model: Manages the video stream data and state"""
    
    def __init__(self):
        self.latest_frame: Optional[Image.Image] = None
        self.is_running = False
        self._lock = threading.Lock()

        self._frame_callback: Optional[Callable[[FrameEvent],None]] = None
    
    def get_latest_frame(self) -> Optional[Image.Image]:
        with self._lock:
            return self.latest_frame
    
    def update_frame(self, frame: Image.Image) -> None:
        with self._lock:
            self.latest_frame = frame

        if self._frame_callback:
            frame_event = FrameEvent(frame=frame)
            self._frame_callback(frame_event)
    
    def start(self) -> None:
        self.is_running = True
    
    def stop(self) -> None:
        self.is_running = False
    
    # Observer setup
    def set_new_frame_callback(self,callback:Callable[[FrameEvent],None]) -> None:
        self._frame_callback=callback


# --- SERVICE LAYER ---
class ADBService:
    """Service: Handles ADB operations"""
    
    def __init__(self, device_serial: str = ""):
        self.device_serial = device_serial
    
    def tap(self, x: int, y: int) -> None:
        device_cmd = f"-s {self.device_serial} " if self.device_serial else ""
        cmd = f"adb {device_cmd}shell input tap {x} {y}"
        ic(f"ADB tap: {x}, {y}")
        ic(f"Command: {cmd}")
        subprocess.run(cmd, check=True)


class ScrcpyServerService:
    """Service: Manages the scrcpy server process"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
    
    def start_server(self) -> None:
        print("[*] Setting up scrcpy server")
        subprocess.run("adb forward tcp:1234 localabstract:scrcpy", check=True)
        
        print("[*] Starting scrcpy server...")
        cmd = (
            "adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / "
            "com.genymobile.scrcpy.Server 3.3.1 tunnel_forward=true audio=false "
            "control=false cleanup=false raw_stream=true max_size=1920"
        )
        
        self.process = subprocess.Popen(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        
        if self.process.stdout:
            for line in self.process.stdout:
                print(f"[SERVER]: {line.strip()}")
                if "[server] INFO: Device:" in line:
                    print("[*] Scrcpy server setup complete")
                    return
    
    def stop_server(self) -> None:
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None


class StreamService:
    """Service: Handles H.264 stream decoding"""
    
    def __init__(self, config: Config, model: StreamModel):
        self.config = config
        self.model = model
        self.codec = av.CodecContext.create("h264", "r")
        self.worker_thread: Optional[threading.Thread] = None
    
    def start_streaming(self) -> None:
        self.worker_thread = threading.Thread(
            target=self._stream_worker, daemon=True
        )
        self.worker_thread.start()
    
    def stop_streaming(self) -> None:
        self.model.stop()
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
    
    def _stream_worker(self) -> None:
        """Background thread that receives and decodes video data"""
        sock = None
        try:
            print(f"[*] Connecting to scrcpy server at {self.config.host}:{self.config.port}...")
            sock = socket.create_connection((self.config.host, self.config.port))
            print("[*] Connected! Waiting for video stream...")
            
            while self.model.is_running:
                data = sock.recv(4096)
                if not data:
                    print("NO DATA BREAKING")
                    break
                
                try:
                    packets = self.codec.parse(data)
                    for packet in packets:
                        frames = self.codec.decode(packet)
                        for frame in frames:
                            self.model.update_frame(frame.to_image())
                except Exception as e:
                    print(f"[!] Decode error: {e}")
                    
        except Exception as e:
            print(f"[!] Stream worker error: {e}")
        finally:
            if sock:
                sock.close()
            self.model.stop()
            print("[*] Stream worker finished.")


# --- VIEW ---
class StreamView:
    """View: Handles the GUI display"""
    
    def __init__(self, config: Config):
        self.config = config
        self.root = tk.Tk()
        self.root.geometry(f"{config.window_size[0]}x{config.window_size[1]}")
        self.root.title(config.window_title)
        
        self.label = tk.Label(self.root)
        self.label.pack()
        
        self._click_observers: list[ClickObserver] = []
        self._close_callback: Optional[Callable] = None
        
        # Bind events
        self.label.bind("<Button-1>", self._on_click)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Start render loop
        self._render_loop()
    
    def add_click_observer(self, observer: ClickObserver) -> None:
        self._click_observers.append(observer)
    
    def remove_click_observer(self, observer: ClickObserver) -> None:
        if observer in self._click_observers:
            self._click_observers.remove(observer)
    
    def set_close_callback(self, callback: Callable) -> None:
        self._close_callback = callback
    
    def update_frame(self, frame: Image.Image) -> None:
        """Update the displayed frame"""
        photo_img = ImageTk.PhotoImage(image=frame)
        self.label.config(image=photo_img)
        self.label.image = photo_img  # Keep a reference
    
    def start(self) -> None:
        self.root.mainloop()
    
    def close(self) -> None:
        self.root.destroy()
    
    def _on_click(self, event) -> None:
        click_event = ClickEvent(x=event.x, y=event.y)
        for observer in self._click_observers:
            observer.on_click(click_event)
    
    def _on_close(self) -> None:
        print("[!] Window closed, shutting down.")
        if self._close_callback:
            self._close_callback()
    
    def _render_loop(self) -> None:
        """Placeholder render loop - controller will override this"""
        self.root.after(1000 // self.config.max_fps, self._render_loop)


# --- CONTROLLER ---
class StreamController:
    """Controller: Orchestrates all components and handles business logic"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize components
        self.model = StreamModel()
        self.view = StreamView(config)
        self.adb_service = ADBService(config.device_serial)
        self.server_service = ScrcpyServerService()
        self.stream_service = StreamService(config, self.model)
        
        # Wire up observers & callbacks
        self.view.add_click_observer(self)
        self.model.set_new_frame_callback(self.on_new_frame)
        self.view.set_close_callback(self.stop)
        
        # Override view's render loop
        self.view._render_loop = self._render_loop
    
    def start(self) -> None:
        """Start the entire application"""
        # Start server in background thread
        server_thread = threading.Thread(target=self.server_service.start_server)
        server_thread.start()
        server_thread.join()
        time.sleep(0.1)
        
        # Start streaming
        self.model.start()
        self.stream_service.start_streaming()
        
        # Start GUI (blocking)
        self.view.start()
    
    def stop(self) -> None:
        """Clean shutdown of all components"""
        self.stream_service.stop_streaming()
        self.server_service.stop_server()
        self.view.close()
    
    # Observer & Callback implementations
    def on_new_frame(self, event: FrameEvent) -> None:
        """Handle new frame from model"""
        # This runs in the background thread, so we schedule GUI update
        self.view.root.after_idle(lambda: self.view.update_frame(event.frame))
    
    def on_click(self, event: ClickEvent) -> None:
        """Handle click from view"""
        print("click!!!")
        # Run ADB command in background thread to avoid blocking GUI
        threading.Thread(
            target=self.adb_service.tap, 
            args=(event.x, event.y), 
            daemon=True
        ).start()
    
    def _on_close(self) -> None:
        """Handle window close"""
        self.stop()
    
    def _render_loop(self) -> None:
        """Optimized render loop"""
        frame = self.model.get_latest_frame()
        if frame:
            self.view.update_frame(frame)
        
        if self.model.is_running:
            self.view.root.after(1000 // self.config.max_fps, self._render_loop)
        else:
            self.view.close()


# --- MAIN ---
def main():
    config = Config()
    controller = StreamController(config)
    controller.start()


if __name__ == "__main__":
    main()