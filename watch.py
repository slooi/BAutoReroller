import time
import subprocess
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

APP_FILE = "main.py"

class AppReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_process()

    def start_process(self):
        """Start or restart the Python application."""
        if self.process:
            print("Restarting app...")
            self.process.kill()
            self.process.wait()

        self.process = subprocess.Popen([sys.executable, APP_FILE])
        print(f"App started with PID: {self.process.pid}")

    def on_any_event(self, event):
        """Called when a file is modified, created, deleted, or moved."""
        if (
            event.is_directory
            or not event.src_path.endswith(".py")
        ):
            return

        print(f"Change detected in: {event.src_path}")
        self.start_process()

if __name__ == "__main__":
    watch_path = "."  # Watch everything in the current directory
    event_handler = AppReloader()
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()
    print(f"Watching for changes in all .py files under {os.path.abspath(watch_path)}...")

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
