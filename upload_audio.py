import requests, os, time, json

# These now pull safely from GitHub Secrets
API_KEY = os.getenv("ROBLOX_API_KEY") 
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")
AUDIO_DIR = "sounds/"
LOG_FILE = "asset_ids.json"

# Ensure the sounds directory exists so the script doesn't crash
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

def get_already_uploaded():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
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
uploaded = get_already_uploaded()
new_uploads = False

for file in os.listdir(AUDIO_DIR):
    if file.endswith(".mp3") and file not in uploaded:
        print(f"Uploading {file}...")
        asset_id = upload_audio(os.path.join(AUDIO_DIR, file), file)
        if asset_id:
            uploaded[file] = asset_id
            new_uploads = True

if new_uploads:
    with open(LOG_FILE, "w") as f:
        json.dump(uploaded, f, indent=4)
    print("Updated asset_ids.json successfully.")
else:
    print("No new audio files to upload.")
