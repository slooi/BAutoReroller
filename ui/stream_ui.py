
# -----------------------------
# ui/stream_view.py
# -----------------------------
import tkinter as tk
from PIL import Image, ImageTk
from typing import Callable, Optional, TypeAlias

from events_and_config.events_and_config import ClickEvent, Config


ClickCallback: TypeAlias = Callable[[ClickEvent], None]
GetFrameCallback: TypeAlias = Callable[[], Optional[Image.Image]]

class StreamView:
    """Tkinter GUI that displays frames and captures clicks."""
    
    def __init__(self, config: Config):
        self.config = config

        """ Tkinter setup """
        self.root = tk.Tk()
        self.root.title(config.window_title)
        self.root.geometry(f"{config.window_size[0]}x{config.window_size[1]}")

        self.canvas=tk.Canvas(self.root)
        self.canvas.pack(expand=True,fill="both")
        
        """ Setup callbacks """
        self._click_callback: Optional[ClickCallback] = None
        self._close_callback: Optional[Callable] = None
        self._get_frame_callback: Optional[GetFrameCallback] = None
        
        """ Setup eventlisteners """
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._render_loop()

    def _render_loop(self) -> None:
        """Placeholder render loop - controller will override this"""
        if self._get_frame_callback:
            frame=self._get_frame_callback()
            # print(frame)
            if frame:
                # frame.size
                photo_img = ImageTk.PhotoImage(image=frame.resize((self.config.window_size[0],self.config.window_size[1]),Image.Resampling.LANCZOS))
                self.image = photo_img # prevent GC
                self.canvas.create_image(0, 0, image=photo_img, anchor="nw")
        self.root.after(1000 // self.config.max_fps, self._render_loop)
    
    def start(self) -> None:
        self.root.mainloop()
    
    def close(self) -> None:
        self.root.destroy()

    """ INTERNAL CALLBACK FUNCTIONS """

    def _on_resize(self,event):
        print(event)

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

    def set_get_frame_callback(self,callback:GetFrameCallback):
        self._get_frame_callback=callback

    def set_click_callback(self, callback: ClickCallback):
        self._click_callback = callback

    def set_close_callback(self, callback: Callable) -> None:
        self._close_callback = callback