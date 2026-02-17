#!/usr/bin/env python3
"""
Simple Click Server
Listens for network commands and performs a single click at the current mouse position.
Requires: pip install pyautogui
"""

import socket
import pyautogui


def start_server(host='0.0.0.0', port=5555):
    """
    Start a simple server that clicks when it receives any message.
    
    Args:
        host (str): Host IP to bind to
        port (int): Port to listen on
    """
    # Enable failsafe
    pyautogui.FAILSAFE = True
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"[SERVER] Simple Click Server started on {host}:{port}")
    print(f"[SERVER] Waiting for click commands...")
    
    try:
        while True:
            # Accept connection
            client_socket, address = server_socket.accept()
            print(f"[SERVER] Connection from {address}")
            
            try:
                # Receive any data
                data = client_socket.recv(1024)
                
                if data:
                    # Perform click at current mouse position
                    pyautogui.click()
                    print(f"[SERVER] ✓ Clicked at current mouse position")
                    
                    # Send confirmation
                    client_socket.send(b"CLICKED")
                    
            except Exception as e:
                print(f"[SERVER] Error: {e}")
            finally:
                client_socket.close()
                
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
