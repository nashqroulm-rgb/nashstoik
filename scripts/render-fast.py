import os
import sys
import json
import subprocess
import time

BASE_DIR = "C:/Users/K4G3/social-fleet-assets/nash/NASH-03_nash_stoik_mindset"
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
CURRICULUM_DIR = os.path.join(BASE_DIR, "curriculum")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def render_day_fast(day_num):
    t0 = time.time()
    day_str = f"{day_num:03d}"
    print(f"=== RENDERING DAY {day_str} FAST PIPELINE ===")

    audio_file = os.path.join(PUBLIC_DIR, f"voiceover_user_{day_str}.mp3")
    bgm_file = os.path.join(PUBLIC_DIR, "bgm_stoic_ambient.mp3")

    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio_file]
    audio_dur = float(subprocess.check_output(cmd).decode().strip())
    total_dur = audio_dur + 1.2
    print(f"Audio duration: {audio_dur:.2f}s | Target video duration: {total_dur:.2f}s")

    d1 = audio_dur * 0.20
    d2 = audio_dur * 0.18
    d3 = audio_dur * 0.30
    d4 = audio_dur * 0.16
    d5 = total_dur - (d1 + d2 + d3 + d4)

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
            e_t = to_srt_time(cue["end"] + 0.15)
            text = cue["text"].upper()
            f.write(f"{idx}\n{s_t} --> {e_t}\n{text}\n\n")

    v1 = os.path.join(PUBLIC_DIR, "broll/scene_01_night_insomnia.mp4")
    v2 = os.path.join(PUBLIC_DIR, "broll/scene_02_rain_window.mp4")
    v3 = os.path.join(PUBLIC_DIR, "hyperframes_stoic_ethereal.mp4")
    v4 = os.path.join(PUBLIC_DIR, "broll/scene_04_coffee_steam.mp4")
    v5 = os.path.join(PUBLIC_DIR, "broll/scene_05_walking_sunrise.mp4")

    out_mp4 = os.path.join(OUTPUT_DIR, f"nash_stoik_day_{day_str}_compressed.mp4")
    srt_escaped = srt_file.replace("\\", "/").replace(":", "\\:")

    # Clean, fast filter complex with -stream_loop on inputs
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
        "-preset", "ultrafast",
        "-crf", "30",
        "-c:a", "aac",
        "-b:a", "64k",
        "-t", f"{total_dur:.2f}",
        out_mp4
    ]

    print("Running fast render with -preset ultrafast...")
    subprocess.run(cmd_ffmpeg, check=True)
    size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    elapsed = time.time() - t0
    print(f"SUCCESS Day {day_str}! Output: {out_mp4} ({size_mb:.2f} MB) in {elapsed:.1f}s")
    return out_mp4

if __name__ == "__main__":
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    render_day_fast(day)
