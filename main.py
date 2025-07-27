import socket
import tkinter as tk
from PIL import Image, ImageTk
import av
import threading
import random
from icecream import ic
import subprocess

# --- Configuration ---
# Set to your device serial if you have more than 1 device connected to adb. 
# You can find by typing `adb devices`. Example serials: adb-RJV8-su22._adb-tls-connect._tcp, 192.168.1.2:25345
DEVICE_SERIAL = "" 

HOST = "127.0.0.1"
PORT = 1234

# CONSTANTS
WINDOW_TITLE = "scrcpy Real-Time Stream (Low Latency)"

def adb_tap(x, y,device_serial=DEVICE_SERIAL):
    device_serial_cmd=""
    if device_serial:
        device_serial_cmd=f"-s {device_serial} " if device_serial else ""

    cmd = f"adb {device_serial_cmd}shell input tap {x} {y}"
    ic(x,y)
    ic(cmd)
    subprocess.run(cmd, check=True)

class H264Renderer:
    def __init__(self, root:tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.label = tk.Label(root)
        self.label.pack()

        self.codec = av.CodecContext.create("h264", "r")
 
        self.latest_frame = None 
        self.lock = threading.Lock() # 2. A lock to prevent race conditions when accessing the variable 
        self.is_running = True

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Event handlers
        self.label.bind("<Button-1>",self.click)

        # Start the network/decoder thread
        self.worker_thread = threading.Thread(target=self._network_and_decode_loop, daemon=True)
        self.worker_thread.start()
        
        # Render loop
        self.render_latest_frame()

    def click(self,event):
        threading.Thread(target=adb_tap,args=(event.x,event.y,),daemon=True).start()
        ic(event)



    def on_close(self):
        """Handle window closing."""
        print("[!] Window closed, shutting down.")
        self.is_running = False
        self.worker_thread.join(timeout=1.0)
        self.root.destroy()

    def _network_and_decode_loop(self):
        """
        Runs in a background thread. It continuously receives data from the
        socket, decodes it, and updates the single `self.latest_frame`
        variable with the newest frame.
        """
        sock = None
        try:
            print(f"[*] Connecting to scrcpy server at {HOST}:{PORT}...")
            sock = socket.create_connection((HOST, PORT))
            print("[*] Connected! Waiting for video stream...")

            while self.is_running:
                data = sock.recv(4096)
                if not data:
                    break

                try:
                    packets = self.codec.parse(data)
                    for packet in packets:
                        frames = self.codec.decode(packet)
                        # print(random.randint(0,10000),"frames ",frames)
                        for frame in frames: 
                            with self.lock: # Acquires lock for ctx
                                self.latest_frame = frame.to_image() 
                except Exception as e:
                    print(f"[!] error: {e}")
                    pass 
        except Exception as e:
            print(f"[!] Worker thread error: {e}")
        finally:
            if sock:
                sock.close()
            self.is_running = False
            print("[*] Worker thread finished.")

    def render_latest_frame(self):
        """
        Runs in the main GUI thread. It checks the `self.latest_frame`
        variable and updates the Tkinter label with the image.
        """
        frame_to_render = None
        
        # Acquire the lock to safely read the latest_frame
        with self.lock:
            if self.latest_frame is not None:
                frame_to_render = self.latest_frame
        
        # If we have a new frame, render it. 
        if frame_to_render:
            photo_img = ImageTk.PhotoImage(image=frame_to_render)
            self.label.config(image=photo_img)
            self.label.image = photo_img

        # If the worker thread has stopped, close the window
        if not self.is_running:
            self.root.destroy()
            return
            
        # Schedule the next render. ~30 FPS is plenty for rendering.
        self.root.after(33, self.render_latest_frame)


# def setup_scrcpy_server():
#     print("[*] Setting up srcpy server")
#     subprocess.run("adb forward tcp:1234 localabstract:scrcpy",check=True)
#     subprocess.run("adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / com.genymobile.scrcpy.Server 3.3.1 tunnel_forward=true audio=false control=false cleanup=false raw_stream=true max_size=1920",check=True)
#     print("[*] Scrcpy server setup complete")

def main():
    # Run scrcpy: scrcpy --no-control --tcpip=1234
    # t=threading.Thread(target=setup_scrcpy_server)
    # t.start()
    # t.join()

    root = tk.Tk()
    app = H264Renderer(root)
    root.mainloop()

if __name__ == "__main__":
    main()