from dataclasses import dataclass
from icecream import ic

from app.stream_state import StreamState
from events_and_config.events_and_config import ClickEvent, Config, FrameEvent
from services.adb_service import ADBService
from services.scrcpy_server_service import ScrcpyServerService
from services.video_receiver_service import VideoReceiverService
from ui.stream_ui import StreamView
# -----------------------------
# app/controller.py
# -----------------------------

class Controller():
    """Main controller that wires together view, state, and services."""
    
    def __init__(self, config: Config):
        self.config = config
        self.stream_state = StreamState()
        self.view = StreamView(config,self.stream_state)

        """ Setup Services """
        self.adb_service = ADBService(config.device_serial)
        self.scrcpy_service = ScrcpyServerService()
        self.t_receiverService = VideoReceiverService(config)
        
        """ Setup Callbacks """
        self.view.set_click_callback(self.on_click)
        
        self.t_receiverService.set_frame_callback(self.stream_state.set_frame)
        self.view.set_close_callback(self.stop)
    
    def start(self) -> None:
        self.scrcpy_service.start_server()
        self.t_receiverService.start_streaming()
        self.view.start()
    
    def stop(self) -> None:
        self.t_receiverService.stop_streaming()
        self.scrcpy_service.stop_server()
        self.view.close()
    
    """ CALLBACK FUNCTIONS """

    def on_new_frame(self, event: FrameEvent) -> None:
        self.view.update_frame(event.frame)
    
    def on_click(self, event: ClickEvent) -> None:
        self.adb_service.tap(event.x, event.y)

