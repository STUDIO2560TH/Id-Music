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
    
    # Remove extension from filename for the display name
    display_name = os.path.splitext(filename)[0]
    
    with open(file_path, "rb") as f:
        files = {
            'request': (None, json.dumps({
                "assetType": "Audio",
                "displayName": display_name,
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
recent_uploads_main = {}

if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

print(f"Scanning {AUDIO_DIR} for music list uploads...")
for file in os.listdir(AUDIO_DIR):
    if file.endswith(".mp3") and file not in uploaded_main:
        print(f"Uploading {file} to music list...")
        asset_id = upload_audio(os.path.join(AUDIO_DIR, file), file)
        if asset_id:
            uploaded_main[file] = asset_id
            recent_uploads_main[file] = asset_id
            new_uploads_main = True
            # Delete file after successful upload
            try:
                os.remove(os.path.join(AUDIO_DIR, file))
                print(f"Deleted {file} from {AUDIO_DIR}")
            except OSError as e:
                print(f"Error deleting {file}: {e}")

if new_uploads_main:
    with open(LOG_FILE, "w") as f:
        json.dump(uploaded_main, f, indent=4)
    print(f"Updated {LOG_FILE} successfully.")
    
    # Write to keep file
    with open(os.path.join(AUDIO_DIR, "keep"), "w") as f:
        f.write("Recently Uploaded:\n")
        for filename, asset_id in recent_uploads_main.items():
            f.write(f"{asset_id}\n")
    print(f"Updated {AUDIO_DIR}keep with recent uploads.")
else:
    print(f"No new audio files in {AUDIO_DIR}.")

# Process ignored sounds folder (NOT added to music list)
new_uploads_ignored = False
recent_uploads_ignored = {}

if not os.path.exists(IGNORED_AUDIO_DIR):
    os.makedirs(IGNORED_AUDIO_DIR)

print(f"Scanning {IGNORED_AUDIO_DIR} for ignored uploads...")
for file in os.listdir(IGNORED_AUDIO_DIR):
    if file.endswith(".mp3") and file not in uploaded_ignored:
        print(f"Uploading {file} (ignored from music list)...")
        asset_id = upload_audio(os.path.join(IGNORED_AUDIO_DIR, file), file)
        if asset_id:
            uploaded_ignored[file] = asset_id
            recent_uploads_ignored[file] = asset_id
            new_uploads_ignored = True
            # Delete file after successful upload
            try:
                os.remove(os.path.join(IGNORED_AUDIO_DIR, file))
                print(f"Deleted {file} from {IGNORED_AUDIO_DIR}")
            except OSError as e:
                print(f"Error deleting {file}: {e}")

if new_uploads_ignored:
    with open(IGNORED_LOG_FILE, "w") as f:
        json.dump(uploaded_ignored, f, indent=4)
    print(f"Updated {IGNORED_LOG_FILE} successfully.")

    # Write to keep file
    with open(os.path.join(IGNORED_AUDIO_DIR, "keep"), "w") as f:
        f.write("Recently Uploaded:\n")
        for filename, asset_id in recent_uploads_ignored.items():
            f.write(f"{asset_id}\n")
    print(f"Updated {IGNORED_AUDIO_DIR}keep with recent uploads.")
else:
    print(f"No new audio files in {IGNORED_AUDIO_DIR}.")
