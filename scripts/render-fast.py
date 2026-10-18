import os
import sys
import json
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
CURRICULUM_DIR = os.path.join(BASE_DIR, "curriculum")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
HF_SCENES_DIR = os.path.join(BASE_DIR, "hyperframes_scenes/scenes")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def render_day_fast(day_num):
    t0 = time.time()
    day_str = f"{day_num:03d}"
    print(f"==================================================")
    print(f"   NASH STOIK ZERO DEJA-VU PIPELINE: DAY {day_str}")
    print(f"==================================================")

    # 1. Resolve Audio & Duration
    audio_file = os.path.join(PUBLIC_DIR, f"voiceover_user_{day_str}.mp3")
    if not os.path.exists(audio_file):
        # Fallback to assets/audio
        alt = os.path.join(BASE_DIR, f"assets/audio/narasi{day_str}.mp3")
        if os.path.exists(alt):
            import shutil
            shutil.copy2(alt, audio_file)
        else:
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

    bgm_file = os.path.join(PUBLIC_DIR, "bgm_stoic_ambient.mp3")

    cmd_probe = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio_file]
    audio_dur = float(subprocess.check_output(cmd_probe).decode().strip())
    total_dur = audio_dur + 1.2
    print(f"Audio duration: {audio_dur:.2f}s | Target video duration: {total_dur:.2f}s")

    d1 = audio_dur * 0.20
    d2 = audio_dur * 0.18
    d3 = audio_dur * 0.30
    d4 = audio_dur * 0.16
    d5 = total_dur - (d1 + d2 + d3 + d4)

    # 2. Resolve Unique HyperFrames Scene
    if day_num == 1:
        hf_mp4 = os.path.join(PUBLIC_DIR, "hyperframes_stoic_ethereal.mp4")
    else:
        hf_mp4 = os.path.join(PUBLIC_DIR, f"hyperframes_day{day_str}.mp4")
        hf_html = os.path.join(HF_SCENES_DIR, f"scene_day{day_str}.html")
        
        if not os.path.exists(hf_mp4):
            print(f"Rendering dedicated HyperFrames for Day {day_str} ({hf_html})...")
            cmd_hf = ["npx", "hyperframes", "render", "-c", hf_html, "-o", hf_mp4, "--fps", "24", "--low-memory-mode"]
            # on Windows shell might be needed
            subprocess.run(cmd_hf, check=True, shell=(os.name == "nt"))

    # 3. Resolve Unique B-roll
    if day_num == 1:
        v1 = os.path.join(PUBLIC_DIR, "broll/scene_01_night_insomnia.mp4")
        v2 = os.path.join(PUBLIC_DIR, "broll/scene_02_rain_window.mp4")
        v4 = os.path.join(PUBLIC_DIR, "broll/scene_04_coffee_steam.mp4")
        v5 = os.path.join(PUBLIC_DIR, "broll/scene_05_walking_sunrise.mp4")
    else:
        day_broll_dir = os.path.join(PUBLIC_DIR, f"broll/day_{day_str}")
        v1 = os.path.join(day_broll_dir, "scene_01.mp4")
        v2 = os.path.join(day_broll_dir, "scene_02.mp4")
        v4 = os.path.join(day_broll_dir, "scene_04.mp4")
        v5 = os.path.join(day_broll_dir, "scene_05.mp4")

        # If any missing, fetch via fetch-broll.py
        if not (os.path.exists(v1) and os.path.exists(v2) and os.path.exists(v4) and os.path.exists(v5)):
            print(f"B-roll missing for Day {day_str}, calling fetch-broll.py...")
            subprocess.run([sys.executable, os.path.join(BASE_DIR, "scripts/fetch-broll.py"), str(day_num)], check=True)

    v3 = hf_mp4

    # 4. Generate Calibrated Subtitle SRT
    sub_json = os.path.join(CURRICULUM_DIR, f"subtitles_user_{day_str}.json")
    srt_file = os.path.join(OUTPUT_DIR, f"subtitles_day_{day_str}.srt")
    with open(sub_json, "r", encoding="utf-8") as f:
        cues = json.load(f)

    def to_srt_time(sec):
        hrs = int(sec // 3600)
        mins = int((sec % 3600) // 60)
        secs = int(sec % 60)
        ms = int(round((sec - int(sec)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

    with open(srt_file, "w", encoding="utf-8") as f:
        for idx, cue in enumerate(cues, 1):
            s_t = to_srt_time(cue["start"])
            e_t = to_srt_time(cue["end"] + 0.12)
            text = cue["text"].upper()
            f.write(f"{idx}\n{s_t} --> {e_t}\n{text}\n\n")

    out_mp4 = os.path.join(OUTPUT_DIR, f"nash_stoik_day_{day_str}_compressed.mp4")
    srt_escaped = srt_file.replace("\\", "/").replace(":", "\\:")

    # 5. FFmpeg Ultra-Fast Assembly Filter Complex
    filter_complex = f'''
[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,trim=duration={d1:.2f},setpts=PTS-STARTPTS[v0];
[1:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,trim=duration={d2:.2f},setpts=PTS-STARTPTS[v1];
[2:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,trim=duration={d3:.2f},setpts=PTS-STARTPTS[v2];
[3:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,trim=duration={d4:.2f},setpts=PTS-STARTPTS[v3];
[4:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,trim=duration={d5:.2f},setpts=PTS-STARTPTS[v4];
[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0[vbase];
[vbase]subtitles='{srt_escaped}':force_style='PlayResX=720,PlayResY=1280,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,MarginV=90,Alignment=2,Fontname=Arial'[vsub];
[vsub]drawbox=x=220:y=40:w=280:h=44:color=black@0.75:t=fill,drawbox=x=220:y=40:w=280:h=44:color=0xd4af37@0.6:t=1,drawtext=text='NASH STOIK  •  KETENANGAN JIWA':fontcolor=white:fontsize=10:x=(w-text_w)/2:y=56[vout];
[5:a]volume=1.0[avoice];
[6:a]volume=0.10[abgm];
[avoice][abgm]amix=inputs=2:duration=first:dropout_transition=2[aout]
'''.strip()

    cmd_ffmpeg = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", v1,
        "-stream_loop", "-1", "-i", v2,
        "-stream_loop", "-1", "-i", v3,
        "-stream_loop", "-1", "-i", v4,
        "-stream_loop", "-1", "-i", v5,
        "-i", audio_file,
        "-i", bgm_file,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "32",
        "-maxrate", "1200k",
        "-bufsize", "2400k",
        "-c:a", "aac",
        "-b:a", "64k",
        "-t", f"{total_dur:.2f}",
        out_mp4
    ]

    print("Running FFmpeg render...")
    subprocess.run(cmd_ffmpeg, check=True)
    size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    elapsed = time.time() - t0
    print(f"SUCCESS Day {day_str}! Output: {out_mp4} ({size_mb:.2f} MB) in {elapsed:.1f}s")
    return out_mp4

if __name__ == "__main__":
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    render_day_fast(day)
