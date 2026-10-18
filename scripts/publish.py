"""
NASH-03 Unified Multi-Platform Autonomous Publisher
Fully automated publishing for:
- TikTok (@nashstoik via Zernio)
- Instagram Reels (@nashstoik via Zernio)
- YouTube Shorts (@nashstoik via YouTube Data API v3)
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import time

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(DIR_PATH)
ENV_PATH = os.path.join(BASE_DIR, ".env")
STATE_DIR = os.path.join(BASE_DIR, "state")
PUBLISHED_FILE = os.path.join(STATE_DIR, "published.json")
CURRICULUM_DIR = os.path.join(BASE_DIR, "curriculum")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    # Also read from environment variables
    for k, v in os.environ.items():
        if v:
            env[k] = v
    return env

ENV = load_env()

# -------------------------------------------------------------
# 1. ZERNIO PUBLISHING (TikTok & Instagram Reels)
# -------------------------------------------------------------
def upload_to_zernio(video_path, caption):
    z_key = ENV.get("ZERNIO_API_KEY")
    tiktok_id = ENV.get("TIKTOK_ACCOUNT_ID", "6ad2d1d0e8d7d6b0bb182ee0")
    ig_id = ENV.get("INSTAGRAM_ACCOUNT_ID", "6ad2d1a2bae230c64c985aa1")
    
    if not z_key:
        raise ValueError("ZERNIO_API_KEY belum diset")
        
    file_size = os.path.getsize(video_path)
    file_name = os.path.basename(video_path)
    
    # 1. Presign R2 upload URL
    presign_req = urllib.request.Request(
        "https://api.zernio.com/v1/media/presign",
        data=json.dumps({
            "filename": file_name,
            "contentType": "video/mp4",
            "size": file_size
        }).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {z_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(presign_req) as p_resp:
        presign_data = json.loads(p_resp.read().decode())
        upload_url = presign_data.get("uploadUrl")
        public_url = presign_data.get("publicUrl")
        
    if not upload_url or not public_url:
        raise ValueError(f"Gagal mendapatkan presigned URL Zernio: {presign_data}")
        
    print(f"[Zernio] Mengunggah media binary ({file_size / (1024*1024):.2f} MB)...")
    with open(video_path, "rb") as f:
        media_bytes = f.read()
        
    put_req = urllib.request.Request(
        upload_url,
        data=media_bytes,
        headers={
            "Content-Type": "video/mp4"
        },
        method="PUT"
    )
    with urllib.request.urlopen(put_req) as put_resp:
        if put_resp.status not in [200, 204]:
            raise RuntimeError(f"Gagal upload binary ke R2: status {put_resp.status}")
            
    print("[Zernio] Binary berhasil terunggah ke Cloudflare R2.")
    
    # 2. Buat Post ke TikTok & Instagram
    platforms = []
    if tiktok_id:
        platforms.append({"platform": "tiktok", "accountId": tiktok_id})
    if ig_id:
        platforms.append({"platform": "instagram", "accountId": ig_id})
        
    post_payload = {
        "title": caption.split("\n")[0][:80],
        "content": caption,
        "mediaItems": [{"type": "video", "url": public_url}],
        "platforms": platforms,
        "publishNow": True
    }
    
    post_req = urllib.request.Request(
        "https://api.zernio.com/v1/posts",
        data=json.dumps(post_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {z_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(post_req) as post_resp:
        post_res = json.loads(post_resp.read().decode())
        post_obj = post_res.get("post") or post_res.get("data") or post_res
        post_id = post_obj.get("_id") or post_obj.get("id")
        
    print(f"[Zernio] ✅ POST BERHASIL DIBUAT (ID: {post_id})")
    return {"platform": "zernio", "ok": True, "postId": post_id, "publicUrl": public_url}

# -------------------------------------------------------------
# 2. YOUTUBE SHORTS PUBLISHING (YouTube Data API v3)
# -------------------------------------------------------------
def get_yt_access_token():
    refresh_token = ENV.get("YT_REFRESH_TOKEN")
    client_id = ENV.get("GOOGLE_CLIENT_ID")
    client_secret = ENV.get("GOOGLE_CLIENT_SECRET")
    
    if not refresh_token:
        raise ValueError("YT_REFRESH_TOKEN belum ada di .env")
        
    data = urllib.parse.urlencode({
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token"
    }).encode("utf-8")
    
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        return res.get("access_token")

def upload_to_youtube(video_path, title, description, tags=None, privacy="public"):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File video tidak ditemukan: {video_path}")
        
    token = get_yt_access_token()
    file_size = os.path.getsize(video_path)
    
    clean_title = title.replace("<", "").replace(">", "").strip()[:100]
    clean_desc = description.replace("<", "").replace(">", "").strip()[:5000]
    
    snippet = {
        "title": clean_title,
        "description": clean_desc,
        "categoryId": "27",
    }
    if tags:
        snippet["tags"] = tags
        
    meta = {
        "snippet": snippet,
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }
    
    init_req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(file_size)
        },
        method="POST"
    )
    with urllib.request.urlopen(init_req) as init_resp:
        upload_url = init_resp.headers.get("Location")
        
    if not upload_url:
        raise ValueError("YouTube tidak mengembalikan upload URL resumable")
        
    print(f"[YouTube] Mengunggah video ({file_size / (1024*1024):.2f} MB)...")
    chunk_size = 8 * 1024 * 1024
    with open(video_path, "rb") as vf:
        offset = 0
        video_id = None
        while offset < file_size:
            chunk = vf.read(min(chunk_size, file_size - offset))
            n = len(chunk)
            
            req = urllib.request.Request(
                upload_url,
                data=chunk,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(n),
                    "Content-Range": f"bytes {offset}-{offset + n - 1}/{file_size}"
                },
                method="PUT"
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    if resp.status in [200, 201]:
                        res_json = json.loads(resp.read().decode())
                        video_id = res_json.get("id")
                        break
            except urllib.error.HTTPError as e:
                if e.code == 308:
                    pass
                else:
                    raise e
            offset += n
            
    if not video_id:
        raise RuntimeError("Video upload selesai tetapi video ID tidak ditemukan")
        
    yt_url = f"https://youtu.be/{video_id}"
    print(f"[YouTube] ✅ BERHASIL -> {yt_url}")
    return {"platform": "youtube", "ok": True, "videoId": video_id, "url": yt_url}

# -------------------------------------------------------------
# 3. AUTONOMOUS DAY PUBLISHER
# -------------------------------------------------------------
def resolve_video_file(day_num):
    day_str = f"{day_num:03d}"
    local_out = os.path.join(OUTPUT_DIR, f"nash_stoik_day_{day_str}_compressed.mp4")
    if os.path.exists(local_out) and os.path.getsize(local_out) > 500000:
        return local_out

    # Download from GitHub Release
    tag = f"v-day-{day_str}"
    release_url = f"https://github.com/nashqroulm-rgb/nashstoik/releases/download/{tag}/nash_stoik_day_{day_str}_compressed.mp4"
    print(f"Mengunduh video dari GitHub Release {tag}...")
    try:
        req = urllib.request.Request(release_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(local_out, "wb") as f:
            f.write(resp.read())
        if os.path.exists(local_out) and os.path.getsize(local_out) > 500000:
            print(f"Video Day {day_str} berhasil diunduh dari cloud release ({os.path.getsize(local_out)/(1024*1024):.2f} MB)")
            return local_out
    except Exception as e:
        print(f"Gagal mengunduh dari release: {e}")

    # Fallback to render
    print(f"Merender video secara lokal untuk Day {day_str}...")
    import subprocess
    cmd = [sys.executable, os.path.join(DIR_PATH, "render-fast.py"), str(day_num)]
    subprocess.run(cmd, check=True)
    if os.path.exists(local_out):
        return local_out
    raise FileNotFoundError(f"Video tidak ditemukan untuk Day {day_str}")

def publish_day(day_num):
    day_str = f"{day_num:03d}"
    print("="*60)
    print(f"🚀 MEMULAI DISTRIBUSI AUTONOMOUS: DAY {day_str}")
    print("="*60)

    # 1. Resolve content packet
    pkt_file = os.path.join(CURRICULUM_DIR, f"content_packet_day_{day_str}.json")
    title = f"Nash Stoik Day {day_str}"
    caption = f"Nash Stoik Day {day_str} #nashstoik #ketenanganjiwa #mindset"
    tags = ["#nashstoik", "#ketenanganjiwa", "#mindset", "#shorts"]
    
    if os.path.exists(pkt_file):
        with open(pkt_file, "r", encoding="utf-8") as f:
            pkt = json.load(f)
            title = pkt.get("title", title)
            meta = pkt.get("metadata", {})
            caption = meta.get("caption", caption)
            tags = meta.get("tags", tags)

    full_caption = f"{title}\n\n{caption}\n\n{' '.join(tags)}"

    # 2. Resolve video file
    video_path = resolve_video_file(day_num)
    results = {"day": day_num, "day_str": day_str, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}

    # 3. Publish to Zernio (TikTok & Instagram)
    try:
        z_res = upload_to_zernio(video_path, full_caption)
        results["zernio"] = z_res
    except Exception as e:
        print(f"❌ [Zernio Error]: {e}")
        results["zernio"] = {"ok": False, "error": str(e)}

    # 4. Publish to YouTube (if credentials present)
    if ENV.get("YT_REFRESH_TOKEN"):
        try:
            yt_res = upload_to_youtube(video_path, f"{title} | Nash Stoik", full_caption, tags=tags)
            results["youtube"] = yt_res
        except Exception as e:
            print(f"❌ [YouTube Error]: {e}")
            results["youtube"] = {"ok": False, "error": str(e)}
    else:
        results["youtube"] = {"ok": False, "status": "skipped_no_token"}

    # 5. Record to published.json
    history = {}
    if os.path.exists(PUBLISHED_FILE):
        try:
            with open(PUBLISHED_FILE, "r", encoding="utf-8") as pf:
                history = json.load(pf)
        except Exception:
            history = {}

    history[day_str] = results
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as pf:
        json.dump(history, pf, indent=2, ensure_ascii=False)

    print(f"\n🎉 [SELESAI] Publikasi Day {day_str} tercatat di state/published.json!")
    return results

# -------------------------------------------------------------
# 4. STATUS & HEALTH CHECK
# -------------------------------------------------------------
def check_status():
    print("="*60)
    print("  STATUS INTEGRASI MULTI-PLATFORM NASH-03 (@nashstoik)")
    print("="*60)
    
    yt_token_set = bool(ENV.get("YT_REFRESH_TOKEN"))
    if yt_token_set:
        try:
            token = get_yt_access_token()
            req = urllib.request.Request(
                "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
                headers={"Authorization": f"Bearer {token}"}
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                items = data.get("items", [])
                if items:
                    ch = items[0]
                    print(f" [YouTube]   OK -> Channel: '{ch['snippet']['title']}' ({ch['snippet'].get('customUrl', 'no-custom-url')})")
                else:
                    print(" [YouTube]   WARNING -> Token valid tapi tidak ada channel yang ditemukan")
        except Exception as e:
            print(f" [YouTube]   ERROR -> {e}")
    else:
        print(" [YouTube]   PENDING -> YT_REFRESH_TOKEN belum diset di .env")
        
    z_key = ENV.get("ZERNIO_API_KEY")
    if z_key:
        try:
            req = urllib.request.Request(
                "https://api.zernio.com/v1/accounts",
                headers={"Authorization": f"Bearer {z_key}"}
            )
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                accs = data.get("accounts", [])
                print(f" [Zernio]    OK -> Terhubung {len(accs)} akun terdaftar:")
                for a in accs:
                    plat = a.get("platform")
                    u = a.get("username", a.get("name"))
                    acc_id = a.get("id") or a.get("_id")
                    status = a.get("platformStatus") or "active"
                    print(f"    - [{plat.upper()}] @{u} (ID: {acc_id}) - Status: {status}")
        except Exception as e:
            print(f" [Zernio]    ERROR -> {e}")
    else:
        print(" [Zernio]    ERROR -> ZERNIO_API_KEY tidak ada di .env")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "status":
            check_status()
        elif arg.isdigit():
            publish_day(int(arg))
        elif arg == "publish" and len(sys.argv) > 2 and sys.argv[2].isdigit():
            publish_day(int(sys.argv[2]))
        else:
            check_status()
    else:
        check_status()
