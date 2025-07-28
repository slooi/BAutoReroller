# run.py
import time
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# The file we want to run and watch
APP_FILE = "main2.py" 

class AppReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_process()

    def start_process(self):
        """Start or restart the Tkinter application."""
        if self.process:
            print("Restarting app...")
            self.process.kill()  # Forcefully kill the old process
            self.process.wait()  # Wait for it to be fully killed
        
        # Start a new process
        self.process = subprocess.Popen([sys.executable, APP_FILE])
        print(f"App started with PID: {self.process.pid}")

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.src_path.endswith(APP_FILE):
            print(f"Change detected in {APP_FILE}.")
            self.start_process()

if __name__ == "__main__":
    path = "."  # Watch the current directory
    event_handler = AppReloader()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Watching for changes in {APP_FILE}...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.kill()
            event_handler.process.wait()
    observer.join()
    print("Watcher stopped.")