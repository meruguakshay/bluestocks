import urllib.request
import re
import os

ids = [
    "17G1_VUQkwPQgMBMt72KT0kGLE7rpOg_K",
    "1OyqYLX1aHLtFaSPfs0gP5_IsVJWoXV4o",
    "1ecGhiVfH1Qv5PFAExsNTh_Ig5_IbBLOY",
    "11xfvXksr-n80Y1QEYfHvFRiRCwcmWpGS",
    "1a6NFu43mESTuqWJ_VmZsvFmW0knpQ7SO",
    "1QHf-2SeVdHxGV-3dkyH1Ann0uVtUbU-m",
    "1XGhHl8ct_n1uwWAsj4yG-Z5yJyJsX1Us"
]

os.makedirs("data/raw", exist_ok=True)

for idx, file_id in enumerate(ids):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print(f"\n[{idx+1}/7] Requesting ID {file_id}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            content_disposition = response.info().get('Content-Disposition', '')
            filename = None
            if content_disposition:
                match = re.search(r'filename="([^"]+)"', content_disposition)
                if match:
                    filename = match.group(1)
            
            if not filename:
                # Fallback to temp name
                filename = f"file_{file_id}.dat"
                
            dest = os.path.join("data/raw", filename)
            print(f"  Detected filename: {filename}")
            
            with open(dest, 'wb') as out_file:
                out_file.write(response.read())
            print(f"  [OK] Downloaded {filename} ({os.path.getsize(dest)} bytes)")
    except Exception as e:
        print(f"  [ERROR] Failed to download {file_id}: {e}")
