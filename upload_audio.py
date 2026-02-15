import requests, os, time, json

# These now pull safely from GitHub Secrets
API_KEY = os.getenv("ROBLOX_API_KEY") 
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")
AUDIO_DIR = "sounds/"
LOG_FILE = "asset_ids.json"

IGNORED_AUDIO_DIR = "sounds_ignored/"
IGNORED_LOG_FILE = "ignored_asset_ids.json"

# Ensure the sounds directory exists so the script doesn't crash
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)
if not os.path.exists(IGNORED_AUDIO_DIR):
    os.makedirs(IGNORED_AUDIO_DIR)

def get_already_uploaded(log_filename):
    if os.path.exists(log_filename):
        with open(log_filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def upload_audio(file_path, filename):
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"x-api-key": API_KEY}
    
    with open(file_path, "rb") as f:
        files = {
            'request': (None, json.dumps({
                "assetType": "Audio",
                "displayName": filename,
                "creationContext": {"creator": {"groupId": GROUP_ID}}
            }), 'application/json'),
            'fileContent': (file_path, f, 'audio/mpeg')
        }
        res = requests.post(url, headers=headers, files=files)
        
        if res.status_code != 200:
            print(f"Error starting upload: {res.text}")
            return None
        
    operation_path = res.json()["path"]
    
    # Wait for Roblox to process the audio
    print(f"Polling for {filename} completion...")
    while True:
        status_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers)
        status = status_res.json()
        
        if status.get("done"):
            if "error" in status:
                print(f"Roblox processing error: {status['error']}")
                return None
            return status["response"]["assetId"]
        
        time.sleep(5)

# Main Logic
uploaded_main = get_already_uploaded(LOG_FILE)
uploaded_ignored = get_already_uploaded(IGNORED_LOG_FILE)

# Process main sounds folder (added to music list)
new_uploads_main = False
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

print(f"Scanning {AUDIO_DIR} for music list uploads...")
for file in os.listdir(AUDIO_DIR):
    if file.endswith(".mp3") and file not in uploaded_main:
        print(f"Uploading {file} to music list...")
        asset_id = upload_audio(os.path.join(AUDIO_DIR, file), file)
        if asset_id:
            uploaded_main[file] = asset_id
            new_uploads_main = True

if new_uploads_main:
    with open(LOG_FILE, "w") as f:
        json.dump(uploaded_main, f, indent=4)
    print(f"Updated {LOG_FILE} successfully.")
else:
    print(f"No new audio files in {AUDIO_DIR}.")

# Process ignored sounds folder (NOT added to music list)
new_uploads_ignored = False
if not os.path.exists(IGNORED_AUDIO_DIR):
    os.makedirs(IGNORED_AUDIO_DIR)

print(f"Scanning {IGNORED_AUDIO_DIR} for ignored uploads...")
for file in os.listdir(IGNORED_AUDIO_DIR):
    if file.endswith(".mp3") and file not in uploaded_ignored:
        print(f"Uploading {file} (ignored from music list)...")
        asset_id = upload_audio(os.path.join(IGNORED_AUDIO_DIR, file), file)
        if asset_id:
            uploaded_ignored[file] = asset_id
            new_uploads_ignored = True

if new_uploads_ignored:
    with open(IGNORED_LOG_FILE, "w") as f:
        json.dump(uploaded_ignored, f, indent=4)
    print(f"Updated {IGNORED_LOG_FILE} successfully.")
else:
    print(f"No new audio files in {IGNORED_AUDIO_DIR}.")
