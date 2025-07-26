import socket
import tkinter as tk
from PIL import Image, ImageTk
import av  # The decoder library (FFmpeg wrapper)

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 1234
WINDOW_TITLE = "scrcpy H.264 Stream"


class H264Renderer:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)

        # This label will hold the video frames
        self.label = tk.Label(root)
        self.label.pack()

        # The magic component: the H.264 decoder context from PyAV
        self.codec = av.CodecContext.create("h264", "r")

        self.sock = None
        self.is_running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.connect_and_run()

    def on_close(self):
        """Handle window closing."""
        print("[!] Window closed, shutting down.")
        self.is_running = False
        self.root.destroy()

    def connect_and_run(self):
        """Connects to the scrcpy server and starts the rendering loop."""
        try:
            print(f"[*] Connecting to scrcpy server at {HOST}:{PORT}...")
            self.sock = socket.create_connection((HOST, PORT), timeout=1)
            print("[*] Connected!")

            self.receive_and_render()
            self.root.mainloop()
        except ConnectionRefusedError:
            print(f"[!] Connection refused. Is scrcpy running with '--forward-port={PORT}'?")
        except socket.timeout:
            print("[!] Connection timed out. No data received from scrcpy.")
        except Exception as e:
            print(f"[!] An error occurred: {e}")
        finally:
            if self.sock:
                self.sock.close()
            print("[*] Connection closed.")

    def receive_and_render(self):
        """The core loop: receive data, decode it, and update the GUI."""
        if not self.is_running:
            return

        try:
            data = self.sock.recv(4096)
            if not data:
                print("[!] Stream ended.")
                self.on_close()
                return

            packets = self.codec.parse(data)
            for packet in packets:
                frames = self.codec.decode(packet)
                for frame in frames:
                    img = frame.to_image()
                    photo_img = ImageTk.PhotoImage(image=img)

                    self.label.config(image=photo_img)
                    self.label.image = photo_img    # Keep a reference to avoid garbage collection

        except socket.timeout:
            # No data received, just continue.  EG: device is asleep
            print("     !!!  timeout")
            pass
        except BlockingIOError:
            # No data available on non-blocking socket
            print("     !!!  BlockingIOError")
            pass
        except Exception as e:
            # Ignore minor decoding errors that can happen at the start
            # print(f"[-] Decoding error: {e}")
            print("     !!!  Exception")
            pass
        self.root.after(1, self.receive_and_render) # run after 1ms to run without freezing the GUI.


def main():
    root = tk.Tk()
    app = H264Renderer(root)

if __name__ == "__main__":
    main()
