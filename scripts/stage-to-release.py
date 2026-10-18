import os
import sys
import json
import urllib.request
import mimetypes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CURRICULUM_DIR = os.path.join(BASE_DIR, "curriculum")

def get_github_token():
    if "GITHUB_TOKEN" in os.environ:
        return os.environ["GITHUB_TOKEN"]
    if "GH_TOKEN" in os.environ:
        return os.environ["GH_TOKEN"]

    # Windows Credential Manager fallback
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            advapi32 = ctypes.windll.advapi32

            class CREDENTIAL(ctypes.Structure):
                _fields_ = [
                    ("Flags", wintypes.DWORD),
                    ("Type", wintypes.DWORD),
                    ("TargetName", wintypes.LPWSTR),
                    ("Comment", wintypes.LPWSTR),
                    ("LastWritten", wintypes.FILETIME),
                    ("CredentialBlobSize", wintypes.DWORD),
                    ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
                    ("Persist", wintypes.DWORD),
                    ("AttributeCount", wintypes.DWORD),
                    ("Attributes", ctypes.c_void_p),
                    ("TargetAlias", wintypes.LPWSTR),
                    ("UserName", wintypes.LPWSTR)
                ]

            PCREDENTIAL = ctypes.POINTER(CREDENTIAL)
            CredReadW = advapi32.CredReadW
            CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(PCREDENTIAL)]
            CredReadW.restype = wintypes.BOOL
            CredFree = advapi32.CredFree

            p_cred = PCREDENTIAL()
            if CredReadW("git:https://github.com", 1, 0, ctypes.byref(p_cred)):
                c = p_cred.contents
                blob = ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize).decode("utf-16-le", errors="ignore")
                if not blob.startswith("ghp_") and not blob.startswith("github_pat_"):
                    blob = ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize).decode("utf-8", errors="ignore")
                CredFree(p_cred)
                return blob.strip()
        except Exception as e:
            print("Failed to read credentials from Windows Credential Manager:", e)

    return ""

def stage_video_to_release(day_num, repo="nashqroulm-rgb/nashstoik"):
    day_str = f"{day_num:03d}"
    tag = f"v-day-{day_str}"
    video_file = os.path.join(OUTPUT_DIR, f"nash_stoik_day_{day_str}_compressed.mp4")

    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video file not found: {video_file}")

    token = get_github_token()
    if not token:
        raise ValueError("GitHub Token not found in environment or credential manager!")

    size_mb = os.path.getsize(video_file) / (1024 * 1024)
    print(f"Staging Day {day_str} ({size_mb:.2f} MB) to Release: {tag}...")

    # Load metadata title from content packet if available
    pkt_file = os.path.join(CURRICULUM_DIR, f"content_packet_day_{day_str}.json")
    title = f"Nash Stoik Day {day_str}"
    if os.path.exists(pkt_file):
        with open(pkt_file, "r", encoding="utf-8") as pf:
            pkt = json.load(pf)
            title = f"Nash Stoik Day {day_str}: {pkt.get('title', '')}"

    body = f"Episode {day_str} Shorts Master Video\nAsset: nash_stoik_day_{day_str}_compressed.mp4 ({size_mb:.2f} MB)\nAudio: ElevenLabs William\nZero Deja-Vu Calibrated Pipeline"

    headers = {"Authorization": f"token {token}", "User-Agent": "Mozilla/5.0"}

    # 1. Check or Create Release
    req_check = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/tags/{tag}", headers=headers)
    upload_url = None
    try:
        with urllib.request.urlopen(req_check) as resp:
            r = json.loads(resp.read().decode())
            upload_url = r["upload_url"].split("{")[0]
            print(f"Existing release found: {tag}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            create_payload = {
                "tag_name": tag,
                "target_commitish": "main",
                "name": title,
                "body": body,
                "draft": False,
                "prerelease": False
            }
            create_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases",
                data=json.dumps(create_payload).encode("utf-8"),
                headers={**headers, "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(create_req) as resp:
                r = json.loads(resp.read().decode())
                upload_url = r["upload_url"].split("{")[0]
                print(f"Created Release {tag} successfully!")
        else:
            raise

    # 2. Upload Video Asset
    asset_name = f"nash_stoik_day_{day_str}_compressed.mp4"
    with open(video_file, "rb") as vf:
        asset_bytes = vf.read()

    up_req = urllib.request.Request(
        f"{upload_url}?name={asset_name}",
        data=asset_bytes,
        headers={
            **headers,
            "Content-Type": "video/mp4",
            "Content-Length": str(len(asset_bytes))
        }
    )
    with urllib.request.urlopen(up_req) as resp:
        res = json.loads(resp.read().decode())
        print(f"Uploaded successfully to GitHub Release!")
        print(f"Download URL: {res.get('browser_download_url')}")
    return True

if __name__ == "__main__":
    day = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    stage_video_to_release(day)
