import os
import sys
import urllib.parse
import urllib.request
import json

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def load_env():
    env = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

def save_refresh_token(refresh_token):
    lines = []
    found = False
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("YT_REFRESH_TOKEN="):
                lines.append(f"YT_REFRESH_TOKEN={refresh_token}\n")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"YT_REFRESH_TOKEN={refresh_token}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\n[SUCCESS] Refresh token tersimpan di {env_path}")

def main():
    env = load_env()
    client_id = env.get("GOOGLE_CLIENT_ID")
    client_secret = env.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("[ERROR] GOOGLE_CLIENT_ID atau GOOGLE_CLIENT_SECRET belum diset di .env")
        print("Silakan masukkan GOOGLE_CLIENT_ID dan GOOGLE_CLIENT_SECRET dari Google Cloud Console akun nasheroulb@gmail.com.")
        return

    redirect_uri = "http://localhost"
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube",
        "access_type": "offline",
        "prompt": "consent",
        "login_hint": "nasheroulb@gmail.com"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(params)}"
    
    print("="*60)
    print("  GOOGLE OAUTH2 SETUP FOR YOUTUBE (NASH-03 @nashstoik)")
    print("="*60)
    print("\n1. Buka URL ini di browser (login dengan nasheroulb@gmail.com):\n")
    print(auth_url)
    print("\n2. Setelah klik izinkan (Allow/Lanjutkan), browser diarahkan ke:")
    print("   http://localhost/?code=4/0A...&scope=...")
    print("   (Halaman blank/error tidak apa-apa)")
    print("3. Salin seluruh URL dari address bar atau cukup salin nilai code-nya.\n")
    
    user_input = input("Tempel URL redirect atau nilai code di sini: ").strip()
    if not user_input:
        print("[ERROR] Input kosong.")
        return
        
    code = user_input
    if "code=" in user_input:
        parsed = urllib.parse.urlparse(user_input)
        qs = urllib.parse.parse_qs(parsed.query)
        if "code" in qs:
            code = qs["code"][0]
            
    print(f"\nMenukar authorization code...")
    token_url = "https://oauth2.googleapis.com/token"
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(token_url, data=token_data, headers={
            "Content-Type": "application/x-www-form-urlencoded"
        })
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            refresh_token = data.get("refresh_token")
            if refresh_token:
                save_refresh_token(refresh_token)
            else:
                print("[WARNING] Tidak ada refresh_token di response. Mungkin izin sudah pernah diberikan.")
                print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[ERROR] Gagal menukar code: {e}")

if __name__ == "__main__":
    main()
