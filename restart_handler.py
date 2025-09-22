# Console restart handler for debugging
import threading
import sys
import os

def console_input_handler():
    """Handle console input commands in a separate thread."""
    try:
        while True:
            try:
                user_input = input().strip().upper()
                if user_input == 'R':
                    print("\n[RESTART] Restarting proxy with updated code...")
                    print("[INFO] Current instance will shutdown, new instance will start")
                    print("=" * 60)
                    # Kill current process and restart with same arguments
                    os.execv(sys.executable, ['python'] + sys.argv)
                elif user_input == 'Q' or user_input == 'QUIT':
                    print("\n[SHUTDOWN] Shutting down proxy...")
                    os._exit(0)
                elif user_input == 'H' or user_input == 'HELP':
                    print("\n[COMMANDS] Available commands:")
                    print("  R - Restart proxy (reload code changes)")
                    print("  Q - Quit proxy")
                    print("  H - Show this help")
                    print("  Ctrl+C - Force quit\n")
            except (EOFError, KeyboardInterrupt):
                break
    except Exception as e:
        # Silently handle any input errors
        pass

def start_console_handler():
    """Start the console input handler in a separate thread."""
    thread = threading.Thread(target=console_input_handler, daemon=True)
    thread.start()
    return thread
