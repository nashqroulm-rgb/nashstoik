import os
import sys
import glob
import json
import base64
import urllib.request

AUDIO_DIR = "C:/Users/K4G3/social-fleet-assets/nash/NASH-03_nash_stoik_mindset/assets/audio"
PUBLIC_DIR = "C:/Users/K4G3/social-fleet-assets/nash/NASH-03_nash_stoik_mindset/public"
CURRICULUM_DIR = "C:/Users/K4G3/social-fleet-assets/nash/NASH-03_nash_stoik_mindset/curriculum"

def get_google_api_key():
    for env_path in [
        "FastAINews/.env",
        "Documents/Github/FastAINews/.env",
        "social-fleet-pipeline/.env"
    ]:
        full_p = os.path.expanduser(f"C:/Users/K4G3/{env_path}")
        if os.path.exists(full_p):
            with open(full_p, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GOOGLE_API_KEY="):
                        return line.split("=", 1)[1].strip()
    return os.environ.get("GOOGLE_API_KEY", "")

def transcribe_audio(audio_path, api_key):
    print(f"[Gemini 3.8 Flash] Mentranskripsikan timestamps untuk: {os.path.basename(audio_path)}...")
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = """
Berikan transkripsi presisi dari audio ini dalam bentuk array JSON berisi objek rentang waktu dan teks:
[
  {"start": 0.0, "end": 4.14, "text": "Kalimat pertama..."},
  {"start": 4.14, "end": 7.36, "text": "Kalimat kedua..."}
]
Pastikan semua teks tercover lengkap dari awal sampai akhir audio.
Hanya return JSON murni tanpa markdown formatting backtick.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "audio/mp3", "data": audio_b64}}
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        out_text = res["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(out_text)

def sync_day(day_num, api_key):
    day_str = f"{day_num:03d}"
    candidate_names = [
        f"narasi{day_str}.mp3",
        f"narasi{day_num}.mp3",
        f"narasi_{day_str}.mp3",
        f"narasi_{day_num}.mp3"
    ]

    source_path = None
    for c in candidate_names:
        p = os.path.join(AUDIO_DIR, c)
        if os.path.exists(p):
            source_path = p
            break

    if not source_path:
        print(f"[Sync] File audio untuk Day {day_str} belum ditemukan di {AUDIO_DIR}")
        print(f"       Harap letakkan file rekaman Anda dengan nama: narasi{day_str}.mp3")
        return False

    dest_public = os.path.join(PUBLIC_DIR, f"voiceover_user_{day_str}.mp3")
    if day_num == 1:
        # Backward compatibility for Day 001
        dest_public_compat = os.path.join(PUBLIC_DIR, "voiceover_user.mp3")
        with open(source_path, "rb") as sf, open(dest_public_compat, "wb") as df:
            df.write(sf.read())

    with open(source_path, "rb") as sf, open(dest_public, "wb") as df:
        df.write(sf.read())
    print(f"[Sync] Berhasil menyalin {source_path} -> {dest_public}")

    sub_file = os.path.join(CURRICULUM_DIR, f"subtitles_user_{day_str}.json")
    if not os.path.exists(sub_file):
        try:
            subtitles = transcribe_audio(source_path, api_key)
            with open(sub_file, "w", encoding="utf-8") as out_f:
                json.dump(subtitles, out_f, indent=2, ensure_ascii=False)
            print(f"[Sync] Subtitles tersimpan rapi di: {sub_file}")
        except Exception as e:
            print(f"[Sync Error] Gagal mentranskripsikan audio: {e}")
            return False
    else:
        print(f"[Sync] File subtitle {sub_file} sudah tersedia.")

    return True

def main():
    api_key = get_google_api_key()
    if not api_key:
        print("Error: GOOGLE_API_KEY tidak ditemukan!")
        sys.exit(1)

    if len(sys.argv) > 1:
        day_num = int(sys.argv[1])
        sync_day(day_num, api_key)
    else:
        print("=== SCAN SEMUA AUDIO DI ASSETS/AUDIO ===")
        files = glob.glob(os.path.join(AUDIO_DIR, "narasi*.mp3"))
        for f in sorted(files):
            base = os.path.basename(f)
            num_part = "".join(filter(str.isdigit, base))
            if num_part:
                day_num = int(num_part)
                sync_day(day_num, api_key)

if __name__ == "__main__":
    main()
