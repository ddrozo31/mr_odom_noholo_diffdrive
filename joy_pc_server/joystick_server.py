#!/usr/bin/env python3
import pygame
import socket
import json
import time
import sys

# === Settings ===
WSL2_HOST = "127.0.0.1"
PORT = 5005
RETRY_DELAY = 2  # seconds

# === Initialize joystick ===
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No joystick/gamepad detected.")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f" Joystick found: {joystick.get_name()}")
print(f" Attempting to connect to {WSL2_HOST}:{PORT}...")

sock = None

# === Retry connection loop ===
while sock is None:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((WSL2_HOST, PORT))
        print(f" Connected to WSL2 receiver at {WSL2_HOST}:{PORT}")
    except ConnectionRefusedError:
        print(" WSL2 receiver not ready... retrying in 2s")
        sock.close()
        sock = None
        time.sleep(RETRY_DELAY)

# === Stream joystick data ===
try:
    while True:
        pygame.event.pump()
        axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
        buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
        hats = list(joystick.get_hat(0)) if joystick.get_numhats() > 0 else []

        payload = {
            "axes": axes,
            "buttons": buttons,
            "hats": hats,
            "timestamp": time.time()
        }

        sock.sendall((json.dumps(payload) + "\n").encode())
        time.sleep(0.02)  # ~50 Hz update rate

except KeyboardInterrupt:
    print("\nShutting down...")
except Exception as e:
    print(f" Error: {e}")
finally:
    joystick.quit()
    pygame.quit()
    if sock:
        sock.close()
    print(" Clean exit.")
