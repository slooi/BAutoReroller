
# -----------------------------
# ui/stream_view.py
# -----------------------------
import tkinter as tk
from PIL import Image, ImageTk
from typing import Callable, Optional, TypeAlias

from events_and_config.events_and_config import ClickEvent, Config


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
        self.label.image = photo_img # type:ignore # Prevent GC
    
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

    def set_click_callback(self, callback: ClickCallback):
        self._click_callback = callback

    def set_close_callback(self, callback: Callable) -> None:
        self._close_callback = callback
    
