import whisper
import zhconv
import wave
import pyaudio
import numpy as np
import re
import keyboard
from fuzzywuzzy import process
from device.bulb import Bulb
from device.air_conditioner import AirConditioner


# 定义常量
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

def record_to_file(path, frames, sample_width, rate, channels):
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))


def listen_and_record():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("按 'r' 开始录音，按 's' 停止录音，按 'q' 退出。")
    
    audio_frames = []

    try:
        while True:
            if keyboard.is_pressed('r'):  # 监听 'r' 键开始录音
                print("正在录音... 按 's' 停止。")
                audio_frames = []
                while not keyboard.is_pressed('s'):  # 直到按 's' 键停止
                    data = stream.read(CHUNK)
                    audio_frames.append(data)
                print("录音停止，正在处理...")
                record_to_file("audio_data/output.wav", audio_frames, p.get_sample_size(FORMAT), RATE, CHANNELS)
                process_command()
                print("等待按键 'r' 开始新的录音...")
            elif keyboard.is_pressed('q'):  # 监听 'q' 键退出
                print("退出程序。")
                break
            keyboard.read_event()
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


def process_command():
    model = whisper.load_model("medium")
    result = model.transcribe("audio_data/output.wav", language='Chinese')
    s = result["text"]
    s1 = zhconv.convert(s, 'zh-cn')
    print("转换后的文本:", s1)
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

    # 模糊匹配命令
    matched_command, score = process.extractOne(command, commands.keys())
    if score >= 80:  # 如果匹配度大于等于80
        print(f"Matched command: {matched_command} (Score: {score})")
        commands[matched_command]()


if __name__ == '__main__':
    bulbs = [Bulb(i) for i in range(1, 4)]
    ac = AirConditioner()
    listen_and_record()

