"""
NASH-03 Unified Multi-Platform Publisher & Health Check
Handles publishing and health check for:
- TikTok (@nashstoik via Zernio)
- Instagram (@nashstoik via Zernio)
- YouTube (@nashstoik via Direct YouTube Data API v3)
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import time

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(DIR_PATH, ".env")

def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

ENV = load_env()

# -------------------------------------------------------------
# 1. YOUTUBE PUBLISHING (Direct YouTube Data API v3)
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

def upload_to_youtube(video_path, title, description, tags=None, privacy="public", thumbnail_path=None):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File video tidak ditemukan: {video_path}")
        
    token = get_yt_access_token()
    file_size = os.path.getsize(video_path)
    
    # Sanitasi angle brackets (Rule 62)
    clean_title = title.replace("<", "").replace(">", "").strip()[:100]
    clean_desc = description.replace("<", "").replace(">", "").strip()[:5000]
    
    snippet = {
        "title": clean_title,
        "description": clean_desc,
        "categoryId": "27", # Education / Philosophy
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
    print(f"[YouTube] BERHASIL -> {yt_url}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            with open(thumbnail_path, "rb") as tf:
                thumb_bytes = tf.read()
            t_req = urllib.request.Request(
                f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}",
                data=thumb_bytes,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "image/jpeg"
                },
                method="POST"
            )
            with urllib.request.urlopen(t_req) as t_resp:
                if t_resp.status in [200, 201]:
                    print("[YouTube] Custom thumbnail berhasil diset!")
        except Exception as e:
            print(f"[YouTube] Set thumbnail dilewati (non-fatal): {e}")
            
    return {"platform": "youtube", "ok": True, "videoId": video_id, "url": yt_url}

# -------------------------------------------------------------
# 2. STATUS & HEALTH CHECK
# -------------------------------------------------------------
def check_status():
    print("="*60)
    print("  STATUS INTEGRASI MULTI-PLATFORM NASH-03 (@nashstoik)")
    print("="*60)
    
    # Check YouTube
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
        print(" [YouTube]   PENDING -> YT_REFRESH_TOKEN belum diset (Jalankan python auth_youtube.py)")
        
    # Check Zernio (TikTok & Instagram)
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
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        check_status()
    else:
        check_status()
        print("\nPenggunaan modul:")
        print(" python publish.py status")
