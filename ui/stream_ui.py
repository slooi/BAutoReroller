
# -----------------------------
# ui/stream_view.py
# -----------------------------
from enum import Enum
import tkinter as tk
from PIL import Image, ImageTk
from typing import Callable, Optional, Tuple, TypeAlias

from events_and_config.events_and_config import ClickEvent, Config
from utils.utils import ic


ClickCallback: TypeAlias = Callable[[ClickEvent], None]
GetFrameCallback: TypeAlias = Callable[[], Optional[Image.Image]]

class Orientation(Enum):
    PORTRAIT = 0
    LANDSCAPE = 1

class StreamView:
    """Tkinter GUI that displays frames and captures clicks."""
    
    def __init__(self, config: Config):
        self.config = config

        """ Local variables """
        self.layout = Orientation.PORTRAIT

        """ Tkinter setup """
        self.root = tk.Tk()
        self.root.title(config.window_title)
        self._set_geometry(self.config.window_size)

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



    """ CORE FUNCTIONALITY """

    def _render_loop(self) -> None:
        """Core render loop"""
        self._render_frame()
        self.root.after(1000 // self.config.max_fps, self._render_loop)

    """ CORE SUB FUNCTIONALITY """
    
    def _render_frame(self):
        """Renders a single frame"""
        if not self._get_frame_callback:
            return
        
        frame=self._get_frame_callback()
        if not frame:
            return
        
        # frame.size
        photo_img = ImageTk.PhotoImage(image=frame.resize((self.config.window_size[0],self.config.window_size[1]),Image.Resampling.LANCZOS))
        self.image = photo_img # prevent GC
        self.canvas.create_image(0, 0, image=photo_img, anchor="nw")

    # def _update_geometry(self,frame:Image.Image):


        # Update geometry if changed
        # ic(frame.size==self._frame_size)
        # if (frame.size != self._frame_size):
        #     self._set_geometry(self._frame_size)
        #     # self._frame_size = frame.size




    """ HELPER METHODS """

    def _set_geometry(self,size:Tuple[int,int]):
        self.root.geometry(f"{size[0]}x{size[1]}")
    
    # def _


    """ PUBLIC METHODS """

    def start(self) -> None:
        self.root.mainloop()
    
    def close(self) -> None:
        self.root.destroy()




    """ INTERNAL CALLBACK FUNCTIONS """

    def _on_resize(self,event):
        print(event)

    """ CALLBACK FUNCTIONS """

    def _on_click(self, event) -> None:
        # ic(self._frame_size)
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