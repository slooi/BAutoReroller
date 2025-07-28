
import threading
import subprocess
from icecream import ic
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


