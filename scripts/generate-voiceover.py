import os
import sys
import json
import asyncio
import subprocess
import edge_tts
import edge_tts.constants
import edge_tts.communicate

# Fix Microsoft Edge TTS 403 (synthesize via api.msedgeservices.com failover)
ENDPOINTS = [
    (
        "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"
        f"?Ocp-Apim-Subscription-Key={edge_tts.constants.TRUSTED_CLIENT_TOKEN}"
    ),
    (
        "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1"
        f"?TrustedClientToken={edge_tts.constants.TRUSTED_CLIENT_TOKEN}"
    ),
]

DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKET_PATH = os.path.join(DIR_PATH, "curriculum", "content_packet_day_001.json")
OUTPUT_AUDIO = os.path.join(DIR_PATH, "public", "voiceover_day_001.mp3")

async def generate():
    with open(PACKET_PATH, "r", encoding="utf-8") as f:
        packet = json.load(f)
        
    script = packet["script"]
    voice = "id-ID-ArdiNeural" # Suara pria berwibawa & tenang
    rate = "-4%" # Pacing tenang & berbobot
    
    print(f"[TTS] Menyintesis naskah Day {packet.get('day', 1)}...")
    print(f"[TTS] Voice: {voice} | Rate: {rate} | Karakter: {len(script)}")
    
    os.makedirs(os.path.dirname(OUTPUT_AUDIO), exist_ok=True)
    
    last_err = None
    for endpoint in ENDPOINTS:
        edge_tts.constants.WSS_URL = endpoint
        setattr(edge_tts.communicate, "WSS_URL", endpoint)
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(script, voice=voice, rate=rate)
                with open(OUTPUT_AUDIO, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk.get("type") == "audio" and "data" in chunk:
                            f.write(chunk["data"])
                
                # Verifikasi durasi audio dengan ffprobe
                res = subprocess.run([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "csv=p=0", OUTPUT_AUDIO
                ], capture_output=True, text=True)
                
                duration = float(res.stdout.strip())
                print(f"[TTS] SUKSES! File: {OUTPUT_AUDIO} ({os.path.getsize(OUTPUT_AUDIO)} bytes)")
                print(f"[TTS] Durasi riil: {duration:.2f} detik")
                return duration
            except Exception as e:
                last_err = e
                print(f"[TTS] Attempt {attempt+1} gagal: {e}")
                await asyncio.sleep(1.0)
                
    raise RuntimeError(f"Semua endpoint TTS gagal. Error terakhir: {last_err}")

if __name__ == "__main__":
    dur = asyncio.run(generate())
    sys.exit(0 if dur > 0 else 1)
