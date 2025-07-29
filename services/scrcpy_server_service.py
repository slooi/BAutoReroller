

import threading
import subprocess
import time
from typing import Callable, Optional, Protocol, TypeAlias
from icecream import ic
# -----------------------------
# services/scrcpy_server_service.py
# -----------------------------

class ScrcpyServerService:
    """Starts/stops the scrcpy server via adb."""
    
    def __init__(self,device_serial:str):
        self.device_serial = device_serial
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
        device_cmd = f"-s {self.device_serial} " if self.device_serial else ""
        
        print("[*] Setting up scrcpy server")
        subprocess.run(f"adb {device_cmd}forward tcp:1234 localabstract:scrcpy", check=True)

        print("[*] Starting scrcpy server...")
        cmd = (
            f"adb {device_cmd}shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar "
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
    