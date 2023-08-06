import sounddevice as sd
import soundfile as sf
import numpy as np
from pynput import keyboard
import subprocess
import asyncio
import websockets
import json
import threading
import pickle
import uuid

# Set the duration in seconds
duration = 30.0  # seconds
fs = 16000  # Setting sample rate to 16 kHz
channels = 1

recording = False
buffer = np.array([])
device = 13  # default device

def load_device():
    try:
        with open('device.pkl', 'rb') as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError):
        return device

def save_device(device):
    with open('device.pkl', 'wb') as f:
        pickle.dump(device, f)

def callback(indata, frames, time, status):
    global buffer
    buffer = np.append(buffer, indata)

def start_recording(device):
    global recording, buffer, stream
    recording = True
    buffer = np.array([])
    print('Recording started...')
    stream = sd.InputStream(device=device, channels=channels, samplerate=fs, callback=callback)
    stream.start()

def stop_recording():
    global recording
    if recording:
        recording = False
        print('Recording stopped...')
        stream.stop()
        sf.write('output.wav', buffer, fs)
        # Whisper command should be modified according to its actual usage
        subprocess.run(['whisper', 'output.wav', '--output_format', 'txt', '--model', 'medium.en', '--task', 'transcribe', '--language', 'en'], stdout=subprocess.PIPE)
        with open('output.txt', 'r') as f:
            data = f.read()
            # Removing line breaks and carriage returns from the text data
            data = data.replace('\n', '').replace('\r', '')
            asyncio.run(send_to_streamerbot(data))


def on_press(key):
    global device
    if key.char == 'x':
        print(sd.query_devices())
        new_device = int(input("Enter the ID of the device you want to use: "))
        device = new_device
        save_device(device)
    elif key.char == 'r' and not recording:
        threading.Thread(target=start_recording, args=(device,)).start()
    elif key.char == 't' and recording:
        threading.Thread(target=stop_recording).start()

async def send_to_streamerbot(data):
    try:
        uri = "ws://127.0.0.1:8080/"
        async with websockets.connect(uri) as websocket:
            message = {
                'request': 'DoAction',
                'action': {
                    'id': '9506452c-3986-4e20-821d-236513484bd0',
                    'name': 'HAL_FROM_WEBSOCKETS'
                },
                'args': {
                    'key': 'GPTPrompt',
                    'value': data
                },
                'id': str(uuid.uuid4())  # Generate a unique ID for the request
            }
            await websocket.send(json.dumps(message))
            print("Message sent to server successfully.")
    except Exception as e:
        print(f"An error occurred while sending data to server: {e}")



device = load_device()
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
