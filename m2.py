import socket
import sys
import tkinter as tk
from PIL import Image, ImageTk
import av
import threading
import random
from icecream import ic
import subprocess

class H264Renderer:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # Start the network/decoder thread
        self.is_running=True
        self.worker_thread = threading.Thread(target=self._network_and_decode_loop, daemon=True)
        self.worker_thread.start()
    def on_close(self):
        print("[!] Window closed, shutting down.")
        self.is_running = False
        self.worker_thread.join(timeout=10.0)
        self.root.destroy()
    def _network_and_decode_loop(self):
        while self.is_running:
            pass


def setup_scrcpy_server():
    cmd = [sys.executable, "-u", "-c", "import time; i = 0; "
        "while True: print(f'server running {i}'); i += 1; time.sleep(1)"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def main():
    # Run scrcpy: scrcpy --no-control --tcpip=1234
    t=threading.Thread(target=setup_scrcpy_server)
    t.start()

    root = tk.Tk()
    app = H264Renderer(root)
    root.mainloop()

if __name__ == "__main__":
    main()