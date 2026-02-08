import requests, os, time, json

# Configuration
API_KEY = os.getenv("ROBLOX_API_KEY") 
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")
COLLAB_GROUP_ID = os.getenv("COLLABORATOR_GROUP_ID")
TARGET_UNIVERSE_ID = os.getenv("TARGET_UNIVERSE_ID") # New Secret
AUDIO_DIR = "sounds/"
IDS_FILE = "Ids"

def grant_permissions(asset_id):
    """Grants 'Use' permission ONLY to the collaborator group."""
    url = f"https://apis.roblox.com/asset-permissions-api/v1/assets/{asset_id}/permissions"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Focusing ONLY on Group permission to bypass Universe-related cookie errors
    payload = {
        "requests": [{
            "subject": { "subjectType": "Group", "subjectId": str(COLLAB_GROUP_ID) },
            "action": "Use"
        }]
    }
    
    # Step 1: Request XSRF Token
    res = requests.patch(url, headers=headers, json=payload)
    
    if res.status_code == 403 and "X-CSRF-TOKEN" in res.headers:
        headers["X-CSRF-TOKEN"] = res.headers["X-CSRF-TOKEN"]
        # Step 2: Retry with Token
        res = requests.patch(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        print(f"✅ Group {COLLAB_GROUP_ID} granted access to {asset_id}")
    else:
        print(f"⚠️ Group sharing skipped: {res.text}")

# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    existing_ids = ""
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE, "r") as f:
            existing_ids = f.read()

    new_ids_text = ""
    files = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]

    if not files:
        print("No new songs found in sounds/ folder.")
    else:
        for file in files:
            file_path = os.path.join(AUDIO_DIR, file)
            print(f"Processing: {file}")
            
            asset_id = upload_audio(file_path, file)
            
            if asset_id:
                new_ids_text += f"{asset_id},\n"
                # DELETE FILE after successful upload
                os.remove(file_path)
                print(f"🗑️ Deleted {file} from sounds/ folder.")

        if new_ids_text:
            # Update the Ids file with new IDs at the top
            with open(IDS_FILE, "w") as f:
                f.write(new_ids_text + existing_ids)
            print("✅ All new IDs saved to Ids file.")
            
def upload_audio(file_path, filename):
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"x-api-key": API_KEY}
    
    # Cleaning the Thai name for Roblox compatibility
    # Roblox Asset names must be alphanumeric/simple characters usually
    def clean_file_name(filename):
    # Remove extension
    name = filename.rsplit('.', 1)[0]
    
    # Check if name is purely English/Numbers and correct length
    # If it has Thai characters or is too short/long, use the Timestamp
    if name.isascii() and 3 <= len(name) <= 50:
        return name
    else:
        return "Audio_" + str(int(time.time()))

# Then inside upload_audio use:
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
