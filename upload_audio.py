import requests, os, time, json

# Configuration
API_KEY = os.getenv("ROBLOX_API_KEY") 
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")
COLLAB_GROUP_ID = os.getenv("COLLABORATOR_GROUP_ID")
TARGET_UNIVERSE_ID = os.getenv("TARGET_UNIVERSE_ID") # New Secret
AUDIO_DIR = "sounds/"
IDS_FILE = "Ids"

def grant_permissions(asset_id):
    url = f"https://apis.roblox.com/asset-permissions-api/v1/assets/{asset_id}/permissions"
    
    # We must include the API Key and Content-Type
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "requests": [
            {
                "subject": { "subjectType": "Group", "subjectId": str(COLLAB_GROUP_ID) },
                "action": "Use"
            },
            {
                "subject": { "subjectType": "Universe", "subjectId": str(TARGET_UNIVERSE_ID) },
                "action": "Use"
            }
        ]
    }
    
    # Attempt 1
    res = requests.patch(url, headers=headers, json=payload)
    
    # If it asks for a token (XSRF), we grab it and try again immediately
    if res.status_code == 403 and "X-CSRF-TOKEN" in res.headers:
        headers["X-CSRF-TOKEN"] = res.headers["X-CSRF-TOKEN"]
        res = requests.patch(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        print(f"✅ Permissions successfully granted for {asset_id}")
    else:
        # If it still says 'Authentication cookie is empty', it's a Roblox-side 
        # bug with this specific API. But usually, the ID is already public 
        # enough for your group to use.
        print(f"❌ Permission update failed: {res.text}")

def upload_audio(file_path, filename):
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"x-api-key": API_KEY}
    
    # 1. Clean the name: Remove ".mp3" extension
    clean_name = filename.replace(".mp3", "").replace(".MP3", "")
    
    # 2. Fix Length: Must be 3-50 characters
    if len(clean_name) < 3:
        clean_name = clean_name + "_Audio" # Add suffix if too short
    if len(clean_name) > 50:
        clean_name = clean_name[:50] # Cut it off if too long
    
    with open(file_path, "rb") as f:
        files = {
            'request': (None, json.dumps({
                "assetType": "Audio",
                "displayName": clean_name, # Use the cleaned name here
                "creationContext": {"creator": {"groupId": GROUP_ID}}
            }), 'application/json'),
            'fileContent': (file_path, f, 'audio/mpeg')
        }
        res = requests.post(url, headers=headers, files=files)
        
        if res.status_code != 200:
            print(f"❌ Error for {clean_name}: {res.text}")
            return None
        
    operation_path = res.json()["path"]
    print(f"⏳ Processing {filename}...")
    
    while True:
        status = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers).json()
        if status.get("done"):
            asset_id = status["response"]["assetId"]
            grant_permissions(asset_id)
            return asset_id
        time.sleep(5)

# --- Main Execution ---
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

existing_ids = ""
if os.path.exists(IDS_FILE):
    with open(IDS_FILE, "r") as f:
        existing_ids = f.read()

new_ids_text = ""
files_to_upload = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]

for file in files_to_upload:
    asset_id = upload_audio(os.path.join(AUDIO_DIR, file), file)
    if asset_id:
        new_ids_text += f"{asset_id},\n"
        # Delete file after upload to prevent re-uploading next time
        os.remove(os.path.join(AUDIO_DIR, file))

if new_ids_text:
    with open(IDS_FILE, "w") as f:
        f.write(new_ids_text + existing_ids)
    print("✅ Ids file updated.")
