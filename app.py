from flask import Flask, request, jsonify, render_template
import whisper
import zhconv
import wave
import pyaudio
import numpy as np
import re
from fuzzywuzzy import process
from device.gener_equipment import GeneralEquipment
from device.air_conditioner import AirConditioner
import threading
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

GeneralEquipments = [GeneralEquipment(i) for i in range(1, 4)]
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
    audio_frames = []
    while is_recording:
        data = stream.read(CHUNK)
        audio_frames.append(data)
    record_to_file("audio_data/output.wav", audio_frames, p.get_sample_size(FORMAT))
    process_command()
    stream.stop_stream()
    stream.close()
    p.terminate()


def process_command():
    result = model.transcribe("audio_data/output.wav", language='Chinese')
    s = result["text"]
    s1 = zhconv.convert(s, 'zh-cn')
    print(s1)
    control_device(s1, GeneralEquipments, ac)


def control_device(command, GeneralEquipments, ac):
    commands = {
        "电视开": lambda: GeneralEquipments[0].turn_on(),
        "电视关": lambda: GeneralEquipments[0].turn_off(),
        "台灯开": lambda: GeneralEquipments[1].turn_on(),
        "台灯关": lambda: GeneralEquipments[1].turn_off(),
        "电脑开": lambda: GeneralEquipments[2].turn_on(),
        "电脑关": lambda: GeneralEquipments[2].turn_off(),
        "空调开": lambda: ac.turn_on(),
        "空调关": lambda: ac.turn_off(),
        "空调制冷": lambda: ac.set_mode("cool"),
        "空调制热": lambda: ac.set_mode("heat"),
        "温度加": lambda: ac.set_temperature_add(),
        "温度减": lambda: ac.set_temperature_reduce()
    }

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
        "GeneralEquipments": [GeneralEquipment.get_status() for GeneralEquipment in GeneralEquipments],
        "air_conditioner_state": ac.get_status(),
        "air_conditioner_temp": ac.get_temperature(),
        "air_conditioner_mode": ac.get_mode()
    })

if __name__ == '__main__':
    app.run(debug=True)
