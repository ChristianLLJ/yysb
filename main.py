from flask import Flask, request, jsonify, render_template
import whisper
import zhconv
import wave
import pyaudio
import numpy as np
import re
from fuzzywuzzy import process
from device.bulb import Bulb
from device.air_conditioner import AirConditioner
import threading

app = Flask(__name__)

bulbs = [Bulb(i) for i in range(1, 4)]
ac = AirConditioner()
model = whisper.load_model("medium")

# 全局变量
is_recording = False
audio_frames = []
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD = 500
SILENCE_LIMIT = 1

def is_silent(data):
    audio_data = np.frombuffer(data, dtype=np.int16)
    return np.max(audio_data) < THRESHOLD

def record_to_file(path, frames, sample_width):
    wf = wave.open(path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def listen_and_record():
    global is_recording, audio_frames
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    silent_chunks = 0
    audio_frames = []

    while is_recording:
        data = stream.read(CHUNK)
        if is_silent(data):
            silent_chunks += 1
            if silent_chunks > int(SILENCE_LIMIT * RATE / CHUNK):
                if audio_frames:
                    record_to_file("output.wav", audio_frames, p.get_sample_size(FORMAT))
                    audio_frames = []
                    process_command()
                silent_chunks = 0
        else:
            silent_chunks = 0
            audio_frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

def process_command():
    result = model.transcribe("output.wav", language='Chinese')
    s = result["text"]
    s1 = zhconv.convert(s, 'zh-cn')
    control_device(s1, bulbs, ac)

def control_device(command, bulbs, ac):
    commands = {
        "灯泡一开": lambda: bulbs[0].turn_on(),
        "灯泡一关": lambda: bulbs[0].turn_off(),
        "灯泡二开": lambda: bulbs[1].turn_on(),
        "灯泡二关": lambda: bulbs[1].turn_off(),
        "灯泡三开": lambda: bulbs[2].turn_on(),
        "灯泡三关": lambda: bulbs[2].turn_off(),
        "空调开": lambda: ac.turn_on(),
        "空调关": lambda: ac.turn_off(),
        "空调模式制冷": lambda: ac.set_mode("cool"),
        "空调模式制热": lambda: ac.set_mode("heat")
    }

    if '温度' in command:
        temp_match = re.search(r'温度(\d+)', command)
        if temp_match:
            temperature = int(temp_match.group(1))
            ac.set_temperature(temperature)

    matched_command, score = process.extractOne(command, commands.keys())
    if score >= 80:
        commands[matched_command]()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_recording():
    global is_recording
    if not is_recording:
        is_recording = True
        threading.Thread(target=listen_and_record).start()
    return jsonify({"status": "recording started"})

@app.route('/stop', methods=['POST'])
def stop_recording():
    global is_recording
    is_recording = False
    return jsonify({"status": "recording stopped"})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "bulbs": [bulb.get_status() for bulb in bulbs],
        "air_conditioner": ac.get_status()
    })

if __name__ == '__main__':
    app.run(debug=True)
