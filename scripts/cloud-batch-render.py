import os
import sys
import subprocess
import time
import json
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
HF_SCENES_DIR = os.path.join(BASE_DIR, "hyperframes_scenes/scenes")

def check_release_exists_and_has_asset(tag):
    cmd = ["gh", "release", "view", tag, "--json", "assets"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        try:
            data = json.loads(res.stdout)
            assets = data.get("assets", [])
            for a in assets:
                if a.get("name", "").endswith(".mp4") and a.get("size", 0) > 500000:
                    return True
        except Exception:
            pass
    return False

def render_and_stage_day(day_num):
    day_str = f"{day_num:03d}"
    tag = f"v-day-{day_str}"
    t_start = time.time()
    print(f"\n========================================================")
    print(f"🚀 [CLOUD BATCH] STARTING PRODUCTION: DAY {day_str} ({tag})")
    print(f"========================================================")

    # 1. Skip if already released
    if check_release_exists_and_has_asset(tag):
        print(f"✅ Release {tag} already exists with master MP4. Skipping Day {day_str}.")
        return True

    # 2. Check prerequisites
    audio_file = os.path.join(PUBLIC_DIR, f"voiceover_user_{day_str}.mp3")
    alt_audio = os.path.join(BASE_DIR, f"assets/audio/narasi{day_str}.mp3")
    if not os.path.exists(audio_file) and not os.path.exists(alt_audio):
        print(f"❌ Audio missing for Day {day_str}. Cannot proceed.")
        return False
    if not os.path.exists(audio_file) and os.path.exists(alt_audio):
        shutil.copy2(alt_audio, audio_file)

    # 3. Fetch B-roll
    print(f"📥 Step 1/4: Fetching B-roll for Day {day_str}...")
    cmd_broll = [sys.executable, os.path.join(BASE_DIR, "scripts/fetch-broll.py"), str(day_num)]
    subprocess.run(cmd_broll, check=True)

    # 4. Render HyperFrames
    hf_scene = os.path.join(HF_SCENES_DIR, f"scene_day{day_str}.html")
    hf_out = os.path.join(PUBLIC_DIR, f"hyperframes_day{day_str}.mp4")
    if not os.path.exists(hf_out):
        print(f"🎨 Step 2/4: Rendering HyperFrames vector scene ({hf_scene})...")
        cmd_hf = ["npx", "hyperframes", "render", "-c", hf_scene, "-o", hf_out, "--fps", "24", "--low-memory-mode"]
        subprocess.run(cmd_hf, check=True, shell=(os.name == "nt"))
    else:
        print(f"🎨 Step 2/4: HyperFrames {hf_out} already rendered.")

    # 5. Assemble Video
    print(f"🎬 Step 3/4: Assembling video with FFmpeg for Day {day_str}...")
    cmd_render = [sys.executable, os.path.join(BASE_DIR, "scripts/render-fast.py"), str(day_num)]
    subprocess.run(cmd_render, check=True)

    video_file = os.path.join(OUTPUT_DIR, f"nash_stoik_day_{day_str}_compressed.mp4")
    if not os.path.exists(video_file) or os.path.getsize(video_file) < 500000:
        raise RuntimeError(f"Output video missing or invalid: {video_file}")

    size_mb = os.path.getsize(video_file) / (1024 * 1024)
    print(f"📦 Rendered video: {video_file} ({size_mb:.2f} MB)")

    # 6. Stage to GitHub Release
    print(f"☁️ Step 4/4: Staging {video_file} to GitHub Release {tag}...")
    check_cmd = ["gh", "release", "view", tag]
    if subprocess.run(check_cmd, capture_output=True).returncode == 0:
        print(f"Release {tag} exists. Uploading clobber asset...")
        cmd_upload = ["gh", "release", "upload", tag, video_file, "--clobber"]
        subprocess.run(cmd_upload, check=True)
    else:
        print(f"Creating new GitHub Release {tag}...")
        cmd_create = [
            "gh", "release", "create", tag, video_file,
            "--title", f"Nash Stoik Day {day_str}: Master Short Video",
            "--notes", f"Automated cloud production asset for Nash Stoik Day {day_str}.\nRendered on GitHub Actions cloud runner."
        ]
        subprocess.run(cmd_create, check=True)

    # 7. Cleanup local scratch assets to preserve disk space
    day_broll_dir = os.path.join(PUBLIC_DIR, f"broll/day_{day_str}")
    if os.path.exists(day_broll_dir):
        shutil.rmtree(day_broll_dir, ignore_errors=True)
    if os.path.exists(hf_out):
        try:
            os.remove(hf_out)
        except Exception:
            pass
    if os.path.exists(video_file):
        try:
            os.remove(video_file)
        except Exception:
            pass

    elapsed = time.time() - t_start
    print(f"🎉 [SUCCESS] Day {day_str} staged to GitHub Release {tag} in {elapsed:.1f}s!\n")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/cloud-batch-render.py <start_day> <end_day>")
        sys.exit(1)

    start_day = int(sys.argv[1])
    end_day = int(sys.argv[2])
    print(f"Starting Batch Cloud Production for Days {start_day} to {end_day}...")

    succeeded = 0
    failed = 0
    for d in range(start_day, end_day + 1):
        try:
            ok = render_and_stage_day(d)
            if ok:
                succeeded += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error rendering Day {d:03d}: {e}")
            failed += 1

    print(f"========================================================")
    print(f"BATCH FINISHED: {succeeded} succeeded, {failed} failed (Range: {start_day}..{end_day})")
    print(f"========================================================")

if __name__ == "__main__":
    main()
