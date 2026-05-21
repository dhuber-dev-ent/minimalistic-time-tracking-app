import subprocess
import webbrowser
import time
import sys
import os

PORT = 5000
URL = f"http://127.0.0.1:{PORT}"
APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

if __name__ == "__main__":
    server = subprocess.Popen([sys.executable, APP_PATH])
    time.sleep(1.5)
    webbrowser.open(URL)
    try:
        server.wait()
    except KeyboardInterrupt:
        server.terminate()
