import tkinter as tk
import threading
import subprocess

class Client:
    def __init__(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.mainloop()

def server():
    print("[*] Waiting for server to start...")
    cmd=("adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / com.genymobile.scrcpy.Server 3.3.1"
    " tunnel_forward=true audio=false control=false cleanup=false raw_stream=true max_size=1920")
    subprocess.Popen(cmd,text=True)

def main():
    threading.Thread(target=server).start()
    Client()

main()