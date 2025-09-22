if __name__ == "__main__":
    proxy = GroqClaudeProxy()
    
    # Start console input handler for debugging commands
    print("[DEBUG] Console commands: R=Restart, Q=Quit, H=Help")
    console_thread = threading.Thread(target=proxy.console_input_handler, daemon=True)
    console_thread.start()
    
    proxy.start_server()
