import requests, os, time, json

# Configuration
API_KEY = os.getenv("ROBLOX_API_KEY") 
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")
COLLAB_GROUP_ID = os.getenv("COLLABORATOR_GROUP_ID")
TARGET_UNIVERSE_ID = os.getenv("TARGET_UNIVERSE_ID")
AUDIO_DIR = "sounds/"
IDS_FILE = "Ids"

def clean_file_name(filename):
    """Allows Thai characters but ensures length is correct."""
    name = filename.rsplit('.', 1)[0]
    
    # Roblox still requires names to be between 3 and 50 characters
    # Note: Thai characters sometimes count as more than 1 'byte'
    if len(name) > 50:
        name = name[:50]
    if len(name) < 3:
        name = name + "_Aud"
        
    return name

def grant_permissions(asset_id):
    """Grants 'Use' permission to the collaborator group and universe."""
    url = f"https://apis.roblox.com/asset-permissions-api/v1/assets/{asset_id}/permissions"
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    
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
    
    # Retry with XSRF token if needed
    if res.status_code == 403 and "X-CSRF-TOKEN" in res.headers:
        headers["X-CSRF-TOKEN"] = res.headers["X-CSRF-TOKEN"]
        res = requests.patch(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        print(f"✅ Permissions granted for {asset_id}")
    else:
        print(f"⚠️ Permission sync skipped: {res.text}")

def upload_audio(file_path, filename):
    """Handles the actual upload and polling for the ID."""
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"x-api-key": API_KEY}
    
    # We call the helper function we defined above
    clean_name = clean_file_name(filename)
    
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
        if res.status_code != 200:
            print(f"❌ Upload failed: {res.text}")
            return None
        
    operation_path = res.json()["path"]
    while True:
        status = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers).json()
        if status.get("done"):
            asset_id = status["response"]["assetId"]
            grant_permissions(asset_id)
            return asset_id
        time.sleep(5)

# --- Main Execution ---
if __name__ == "__main__":
    # Create sounds folder if it doesn't exist
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    # Read the current Ids file
    existing_ids = ""
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE, "r") as f:
            existing_ids = f.read()

    new_ids_text = ""
    # Find all .mp3 files
    files_to_upload = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]

    if not files_to_upload:
        print("No new audio files found in the sounds/ folder.")
    else:
        for file in files_to_upload:
            file_path = os.path.join(AUDIO_DIR, file)
            print(f"⏳ Processing: {file}")
            
            # Start the upload process
            asset_id = upload_audio(file_path, file)
            
            if asset_id:
                print(f"✅ Captured ID: {asset_id}")
                new_ids_text += f"{asset_id},\n"
                
                # Delete the file locally so it gets removed from GitHub
                os.remove(file_path)
                print(f"🗑️ Removed {file} from sounds folder.")

        # If we have new IDs, update the file
        if new_ids_text:
            with open(IDS_FILE, "w") as f:
                f.write(new_ids_text + existing_ids)
            print("✅ Ids file updated successfully.")
