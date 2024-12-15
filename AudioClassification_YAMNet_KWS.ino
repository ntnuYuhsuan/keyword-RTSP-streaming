#include "WiFi.h"
#include "StreamIO.h"
#include "NNAudioClassification.h"
#include "AudioClassList.h"
#include "AudioStream.h"
#include "AudioEncoder.h"
#include "RTSP.h"

// WiFi credentials
char ssid[] = "";    
char pass[] = "";    
int status = WL_IDLE_STATUS;
const unsigned long STREAM_TIMEOUT = 5000;
unsigned long lastSpeechTime = 0;
// Audio Detection Settings
AudioSetting configDetection(16000, 1, USE_AUDIO_AMIC);  // 16KHz for YAMNet
Audio audioDetection;
NNAudioClassification audioNN;
StreamIO audioStreamerNN(1, 1);

// RTSP Streaming Settings
AudioSetting configStreaming(1);  // Default preset 1: 16kHz Mono Analog Mic
Audio audioStreaming;
AAC encoder;
RTSP rtsp;
StreamIO audioStreamer1(1, 1);
StreamIO audioStreamer2(1, 1);

// Control flag for RTSP streaming
bool streamingActive = false;

void setup() {
    Serial.begin(115200);

    // Connect to WiFi
    while (status != WL_CONNECTED) {
        status = WiFi.begin(ssid, pass);
        delay(2000);
    }
    Serial.println("Connected to WiFi");

    // Initialize Audio Detection
    audioDetection.configAudio(configDetection);
    audioDetection.begin();

    audioNN.configAudio(configDetection);
    audioNN.setResultCallback(ACPostProcess);
    audioNN.modelSelect(AUDIO_CLASSIFICATION, NA_MODEL, NA_MODEL, NA_MODEL, DEFAULT_YAMNET);
    audioNN.begin();

    audioStreamerNN.registerInput(audioDetection);
    audioStreamerNN.registerOutput(audioNN);
    if (audioStreamerNN.begin() != 0) {
        Serial.println("Audio Detection StreamIO link start failed");
    }

    // Initialize RTSP Streaming (but don't start it yet)
    audioStreaming.configAudio(configStreaming);
    audioStreaming.begin();

    encoder.configAudio(configStreaming);
    encoder.begin();

    rtsp.configAudio(configStreaming, CODEC_AAC);
    rtsp.begin();

    audioStreamer1.registerInput(audioStreaming);
    audioStreamer1.registerOutput1(encoder);

    audioStreamer2.registerInput(encoder);
    audioStreamer2.registerOutput(rtsp);
}

void loop() {
    // Main loop can be used for other tasks if needed
    delay(100);
}

// Callback function for audio detection
void ACPostProcess(std::vector<AudioClassificationResult> results) {

    // printf("No of Audio Detected = %d\r\n", audioNN.getResultCount());

    if (audioNN.getResultCount() > 0) {
        bool speechDetected = false;

        for (int i = 0; i < audioNN.getResultCount(); i++) {
            AudioClassificationResult audio_item = results[i];
            int class_id = (int)audio_item.classID();
            int prob = audio_item.score();

            // Check for Speech (ID 0) with sufficient probability
            if (class_id == 0 && prob > 80) {  // Adjust threshold as needed
                speechDetected = true;
                printf("Speech detected with probability: %d%%\n", prob);
                break;
            }
        }

        // Control RTSP streaming based on speech detection
        if (speechDetected) {
            lastSpeechTime = millis();
            if (!streamingActive){
                printf("Starting RTSP stream...");
                audioStreamer1.begin();
                audioStreamer2.begin();
                streamingActive = true;
            }
        } else if (!speechDetected && (millis() - lastSpeechTime > STREAM_TIMEOUT)) {
            printf("Stopping RTSP stream...");
            audioStreamer1.end();
            audioStreamer2.end();
            streamingActive = false;
        }
    }
}
