import os
import sys
import json
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_FILE = os.path.join(BASE_DIR, "curriculum/curated_broll_manifest.json")
PUBLIC_BROLL = os.path.join(BASE_DIR, "public/broll")

def fetch_broll_for_day(day_num):
    day_str = f"{day_num:03d}"
    print(f"=== FETCHING B-ROLL FOR DAY {day_str} ===")
    
    if not os.path.exists(MANIFEST_FILE):
        print(f"Manifest not found: {MANIFEST_FILE}")
        return False
        
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    day_data = manifest.get(str(day_num)) or manifest.get(day_num)
    if not day_data:
        print(f"No B-roll entry in manifest for Day {day_num}. (Day 1 uses existing local broll).")
        return True

    target_dir = os.path.join(PUBLIC_BROLL, f"day_{day_str}")
    os.makedirs(target_dir, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for sc_name, item in day_data.items():
        v_url = item.get("url")
        v_id = item.get("id")
        dest_file = os.path.join(target_dir, f"{sc_name}.mp4")
        
        if os.path.exists(dest_file) and os.path.getsize(dest_file) > 100000:
            print(f"Clip {sc_name} already exists ({os.path.getsize(dest_file)} bytes). Skipping download.")
            continue
            
        print(f"Downloading {sc_name} (ID: {v_id}) from Pexels CDN...")
        req = urllib.request.Request(v_url, headers=headers)
        with urllib.request.urlopen(req, timeout=45) as resp, open(dest_file, "wb") as out_f:
            out_f.write(resp.read())
            
        size_mb = os.path.getsize(dest_file) / (1024 * 1024)
        print(f"-> Saved {dest_file} ({size_mb:.2f} MB)")
        
    print(f"B-roll for Day {day_str} is ready in {target_dir}!")
    return True

if __name__ == "__main__":
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    fetch_broll_for_day(day)
