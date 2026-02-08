import requests, os, time, json

API_KEY = os.getenv("ROBLOX_API_KEY") 
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")
AUDIO_DIR = "sounds/"
IDS_FILE = "Ids"  # Your specific file name

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
        if res.status_code != 200: return None
        
    operation_path = res.json()["path"]
    while True:
        status = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers).json()
        if status.get("done"):
            return status["response"]["assetId"]
        time.sleep(5)

# --- MAIN LOGIC ---
# 1. Read existing IDs to avoid duplicates
existing_ids = ""
if os.path.exists(IDS_FILE):
    with open(IDS_FILE, "r") as f:
        existing_ids = f.read()

new_content = ""
for file in os.listdir(AUDIO_DIR):
    if file.endswith(".mp3"):
        # We check if the filename is already "noted" or if we want to just upload
        # To keep it simple, we'll upload and prep the new string
        print(f"Uploading {file}...")
        asset_id = upload_audio(os.path.join(AUDIO_DIR, file), file)
        
        if asset_id:
            # Format: ID followed by a comma and newline
            new_content += f"{asset_id},\n"

# 2. Prepend new IDs to the top of the old file
if new_content:
    with open(IDS_FILE, "w") as f:
        f.write(new_content + existing_ids)
    print("Successfully updated Ids file.")
