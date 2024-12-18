# keyword-RTSP-streaming
113-1 AIoT final project

[demo](https://drive.google.com/file/d/1YbIwnhX4K7pckyCVT73sVu9hes36kOPk/view?usp=sharing)

# Realtek CarPlay 語音助理

這個專案實現了一個基於語音控制的車載系統(智能語音助理)，可以通過 RTSP 串流處理語音指令，進行語音識別，並提供語音合成和音樂播放功能的回應。

Device : Realtek AMB82 MINI

- 透過 RTSP 串流即時擷取音訊
- 使用 OpenAI Whisper 進行語音轉文字
- 使用 GPT-4 進行自然語言處理
- 使用 Minimax API 進行文字轉語音合成
- YouTube 音樂播放功能
- 支援多平台（macOS 和 Windows）

### 在Arduino IDE 加載 AMB82 SDK

執行Ameba NN Audio Detection

### macOS 環境設置

1. 安裝 Homebrew（如果尚未安裝）：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. 安裝 FFmpeg：

```bash
brew install ffmpeg
```

3. 安裝 VLC：
```bash
brew install vlc
```

### Windows 環境設置

1. 安裝 FFmpeg：
[參考教學](https://youtu.be/ERee4DY2LQ8?si=y8A6qgbqKpboA0vz)
   - 從 [FFmpeg 官方網站](https://ffmpeg.org/download.html) 下載 FFmpeg
   - 解壓縮下載的檔案
   - 將 FFmpeg 加入系統 PATH：
     - 右鍵點擊「本機」>「內容」>「進階系統設定」>「環境變數」
     - 在系統變數中找到「Path」並點擊編輯
     - 新增 FFmpeg 的 bin 資料夾路徑（例如：C:\ffmpeg\bin）

2. 安裝 VLC：
   - 從 [VideoLAN 官方網站](https://www.videolan.org/vlc/) 下載 VLC
   - 執行安裝程式
   - 將 VLC 加入系統 PATH（步驟同 FFmpeg）

## Deployment

### 安裝所需的 Python 套件：

```bash
pip install opencv-python numpy openai python-vlc yt-dlp requests
```

### 環境變數設置

在專案根目錄建立 `.env` 檔案，包含以下變數：

```env
OPENAI_API_KEY=""
MINIMAX_API_KEY=""
```

```bash
python tts_response_rtsp.py
```

### 語音指令

系統支援以下類型的指令：

- 觸發助理互動（含關鍵字「嘿瑞昱」）
- 音樂播放指令：
  - 「播放 [歌名]」- 播放指定歌曲
  - 「停止」或「暫停」- 停止播放

