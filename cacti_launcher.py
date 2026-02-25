import sys
import threading
import time
import webbrowser
from web_app import run_server
from settings_manager import load_settings

def open_browser(port):
    """Wait a second for the server to start, then open the browser"""
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{port}")

if __name__ == "__main__":
    settings = load_settings()
    port = settings.get("web_port", 8181)
    
    # Start the browser opener in a background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Start the Flask server
    run_server(port)
