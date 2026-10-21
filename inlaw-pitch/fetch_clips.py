"""Download finished clips from a JSON list: [{"scene": 2, "url": "..."}, ...] passed on stdin."""
import json, sys, subprocess, os
items = json.load(sys.stdin)
os.makedirs('audio', exist_ok=True)
for it in items:
    out = f"audio/scene-{it['scene']}.mp3"
    r = subprocess.run(['curl', '-sS', '-o', out, '-w', '%{http_code} %{size_download}', '--max-time', '60', it['url']], capture_output=True, text=True)
    print(out, r.stdout, r.stderr.strip())
