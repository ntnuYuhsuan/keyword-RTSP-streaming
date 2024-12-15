from openai import OpenAI
import os
import requests
import json
import subprocess
import time
import tempfile
from datetime import datetime
from rtsp_server import extract_audio_from_rtsp
from urllib.parse import quote
import yt_dlp
import vlc

class MinimaxTTS:
    def __init__(self):
        self.group_id = '1848913859063071253'
        self.api_key = os.getenv('MINIMAX_API_KEY')
        self.url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={self.group_id}"

    def build_request_body(self, text: str) -> dict:
        return {
            "model": "speech-01-turbo",
            "text": text,
            "stream": True,
            "voice_setting": {
                "voice_id": "male-qn-qingse",
                "speed": 1.25,
                "vol": 1.0,
                "pitch": 0
            },
            "audio_setting": {
                "audio_sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        }

    def speak(self, text: str):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # 建立臨時文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_path = temp_file.name
                
                # 獲取並寫入音訊數據
                response = requests.post(
                    self.url,
                    headers=headers,
                    json=self.build_request_body(text),
                    stream=True
                )

                for chunk in response.raw:
                    if chunk:
                        if chunk[:5] == b'data:':
                            data = json.loads(chunk[5:])
                            if "data" in data and "extra_info" not in data:
                                if "audio" in data["data"]:
                                    audio_hex = data["data"]['audio']
                                    audio_bytes = bytes.fromhex(audio_hex)
                                    temp_file.write(audio_bytes)
                
                temp_file.flush()
                
                # 使用 ffplay 播放音訊
                ffplay_command = [
                    'ffplay',
                    '-autoexit',  # 播放完自動退出
                    '-nodisp',    # 不顯示視窗
                    '-hide_banner',  # 隱藏橫幅
                    '-loglevel', 'quiet',  # 安靜模式
                    temp_path
                ]
                
                subprocess.run(ffplay_command)

        except Exception as e:
            print(f"語音合成或播放錯誤: {e}")
        finally:
            # 清理臨時文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
class YouTubePlayer:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
    def play_youtube_music(self, song_name: str):
        """直接播放YouTube音樂"""
        try:
            # 搜索並獲取第一個視頻的URL
            search_query = f"ytsearch1:{song_name} 官方MV"
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # 搜索視頻
                result = ydl.extract_info(search_query, download=False)
                
                if 'entries' in result and result['entries']:
                    video = result['entries'][0]
                    video_url = f"https://www.youtube.com/watch?v={video['id']}"
                    
                    # 獲取音頻流URL
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(video_url, download=False)
                        audio_url = info['url']
                    
                    # 使用VLC播放音頻
                    media = self.instance.media_new(audio_url)
                    self.player.set_media(media)
                    self.player.play()
                    return True
                    
            return False
            
        except Exception as e:
            print(f"播放YouTube音樂時發生錯誤: {e}")
            return False
            
    def stop(self):
        """停止播放"""
        if self.player:
            self.player.stop()

def process_audio_and_respond(audio_file, youtube_player):
    """整合語音識別、GPT回應和語音合成"""
    try:
        # 初始化 OpenAI 客戶端
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 語音轉文字
        with open(audio_file, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio,
                language="zh"
            )
        
        user_text = transcription.text
        print(f"使用者輸入: {user_text}")

        # 音樂指令
        if "播放" in user_text:
            song_name = extract_song_name(user_text)
            if song_name:
                if youtube_player.play_youtube_music(song_name):
                    return {
                        "user_text": user_text,
                        "response": f"正在為您播放: {song_name}",
                        "action": "play_music"
                    }
        elif "停止" in user_text or "暫停" in user_text:
            youtube_player.stop()
            return {
                "user_text": user_text,
                "response": "已停止播放",
                "action": "stop_music"
            }

        if "瑞昱" not in user_text:
            return {
                "user_text": user_text,
                "gpt_response": "non-keyword",
                "action": "none"
            }
        
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是專業且友善的瑞昱車載系統，模擬台北天氣晴朗的氣候回應使用者，使用zh-tw正體中文回答問題。"},
                {"role": "user", "content": user_text}
            ]
        )
        
        gpt_response = response.choices[0].message.content
        print(f"Realtek CarPlay: {gpt_response}")
        
        # 使用 Minimax TTS 進行語音合成
        tts = MinimaxTTS()
        tts.speak(gpt_response)

        return {
            "user_text": user_text,
            "response": gpt_response,
            "action": "speak"
        }
    
    except Exception as e:
        print(f"處理過程發生錯誤: {e}")
        return None
    
def extract_song_name(text: str) -> str:
    """從文字中提取歌曲名稱"""
    if "播放" in text:
        return text.split("播放", 1)[1].strip()
    return ""

def main():
    # rtsp_url = "rtsp://192.168.50.90:554"
    rtsp_url = "rtsp://192.168.0.109:554"
    temp_audio = "temp_audio.wav"
    youtube_player = YouTubePlayer()
    
    print("開始監聽 RTSP 串流...")
    
    try:
        while True:
            print("正在擷取音訊...")
            
            if extract_audio_from_rtsp(rtsp_url, temp_audio):
                result = process_audio_and_respond(temp_audio, youtube_player)
                
                if result:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n[{timestamp}]")
                    
                    if result['action'] == "none":
                        print("non-keyword")
                    elif result['action'] == "play_music":
                        print(f"Realtek CarPlay: {result['response']}")
                    else:
                        print(f"Realtek CarPlay: {result['response']}")
                    
                    print("-" * 50)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n程式結束")
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        youtube_player.stop()

if __name__ == "__main__":
    main()