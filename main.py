import socket
import tkinter as tk
from PIL import Image, ImageTk
import av
import threading
import random

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 1234
WINDOW_TITLE = "scrcpy Real-Time Stream (Low Latency)"


class H264Renderer:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.label = tk.Label(root)
        self.label.pack()

        self.codec = av.CodecContext.create("h264", "r")
 
        self.latest_frame = None 
        self.lock = threading.Lock() # 2. A lock to prevent race conditions when accessing the variable 
        self.is_running = True

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start the network/decoder thread
        self.worker_thread = threading.Thread(target=self._network_and_decode_loop, daemon=True)
        self.worker_thread.start()
        
        # 
        self.render_latest_frame()

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


def main():
    # Run scrcpy: scrcpy --no-control --tcpip=1234
    root = tk.Tk()
    app = H264Renderer(root)
    root.mainloop()

if __name__ == "__main__":
    main()