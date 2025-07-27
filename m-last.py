import tkinter as tk
import threading
from icecream import ic
import subprocess

class H264Renderer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.mainloop()

def setup_scrcpy_server():
    # print("[*] Setting up srcpy server")
    # subprocess.run("adb forward tcp:1234 localabstract:scrcpy",check=True)
    print("[*] Waiting for server to start...")
    cmd=("adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / com.genymobile.scrcpy.Server 3.3.1"
    " tunnel_forward=true audio=false control=false cleanup=false raw_stream=true max_size=1920")
    subprocess.Popen(cmd,text=True)

def main():
    threading.Thread(target=setup_scrcpy_server).start()
    H264Renderer()

if __name__ == "__main__":
    main()