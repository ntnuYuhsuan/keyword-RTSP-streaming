import cv2
import numpy as np
from openai import OpenAI
import subprocess
import os
import time
from datetime import datetime

def extract_audio_from_rtsp(rtsp_url, output_file="temp_audio.wav", duration=5):
    """使用 FFmpeg 從 RTSP 串流擷取固定時長的音訊"""
    # command = [
    #     'ffmpeg',
    #     '-i', rtsp_url,
    #     '-t', str(duration),
    #     '-vn',
    #     '-acodec', 'pcm_s16le',
    #     '-ar', '16000',
    #     '-ac', '1',
    #     '-f', 'wav',
    #     output_file,
    #     '-y'
    # ]

    # macOS command
    command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-t', str(duration),
        '-vn',              # 只要音訊
        output_file,
        '-y'
    ]


    try:
        process = subprocess.run(
            command,
            check=True,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=duration + 5
        )
        
        return True
        # return False
    
    except subprocess.TimeoutExpired:
        print("FFmpeg 處理超時")
        return False
    except subprocess.CalledProcessError as e:
        print(f"音訊擷取錯誤: {e}")
        print(f"錯誤輸出: {e.stderr}")
        return False

def transcribe_audio(audio_file):
    """使用 OpenAI Whisper API 進行語音識別"""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        with open(audio_file, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio,
                language="zh"
            )
        
        return transcription.text
        
    except Exception as e:
        print(f"轉譯過程發生錯誤: {e}")
        return ""

def main():
    rtsp_url = "rtsp://192.168.1.90:554"
    temp_audio = "temp_audio.wav"
    
    print("開始監聽 RTSP 串流...")
    
    try:
        while True:
            print("正在擷取音訊...")
            
            if extract_audio_from_rtsp(rtsp_url, temp_audio):
                result = transcribe_audio(temp_audio)
                
                if result:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n[{timestamp}] 轉譯結果:")
                    print(result)
                    print("-" * 50)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n程式結束")
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

if __name__ == "__main__":
    main()