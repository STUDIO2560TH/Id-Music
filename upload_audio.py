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
    
    # Adding a User-Agent can sometimes bypass 'Cookie' requirement errors
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" 
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
    
    # Step 1: Get the XSRF Token
    first_res = requests.patch(url, headers=headers, json=payload)
    
    if first_res.status_code == 403 and "X-CSRF-TOKEN" in first_res.headers:
        headers["X-CSRF-TOKEN"] = first_res.headers["X-CSRF-TOKEN"]
        # Step 2: Retry with the token
        final_res = requests.post(url, headers=headers, json=payload) # Try POST if PATCH fails
        if final_res.status_code == 200:
            print(f"✅ Permissions granted for {asset_id}")
            return
            
    print(f"⚠️ Permission sync skipped (Roblox API limitation). You may need to manually allow this ID in your other game's settings.")

def upload_audio(file_path, filename):
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"x-api-key": API_KEY}
    
    # Cleaning the Thai name for Roblox compatibility
    # Roblox Asset names must be alphanumeric/simple characters usually
    clean_name = "Audio_" + str(int(time.time())) 
    
    with open(file_path, "rb") as f:
        files = {
            'request': (None, json.dumps({
                "assetType": "Audio",
                "displayName": clean_name,
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
            asset_id = status["response"]["assetId"]
            grant_permissions(asset_id) # Attempt sharing
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
    file_path = os.path.join(AUDIO_DIR, file)
    asset_id = upload_audio(file_path, file)
    
    if asset_id:
        print(f"✅ Captured ID: {asset_id}")
        new_ids_text += f"{asset_id},\n"
        
        # REMOVE THE FILE LOCALLY AFTER SUCCESSFUL UPLOAD
        os.remove(file_path)
        print(f"🗑️ Removed {file} from sounds folder.")

if new_ids_text:
    # Prepend new IDs to the top of the file
    with open(IDS_FILE, "w") as f:
        f.write(new_ids_text + existing_ids)
    print("✅ Ids file updated in workspace.")
