import requests, os, time, json

API_KEY = os.getenv("ROBLOX_API_KEY") 
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")
COLLAB_GROUP_ID = os.getenv("COLLABORATOR_GROUP_ID") # The group you want to share with
IDS_FILE = "Ids"

def grant_permissions(asset_id):
    # This grants "Use" permission to the specific collaborator group
    url = f"https://apis.roblox.com/asset-permissions-api/v1/assets/{asset_id}/permissions"
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    
    payload = {
        "requests": [{
            "subject": {
                "subjectType": "Group",
                "subjectId": COLLAB_GROUP_ID
            },
            "action": "Use" # Allows the group to use the audio in their games
        }]
    }
    
    res = requests.patch(url, headers=headers, json=payload)
    if res.status_code == 200:
        print(f"Successfully shared {asset_id} with Group {COLLAB_GROUP_ID}")
    else:
        print(f"Failed to share: {res.text}")

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
            asset_id = status["response"]["assetId"]
            # NEW: Grant permissions once the upload is done
            grant_permissions(asset_id)
            return asset_id
        time.sleep(5)

# (Rest of your Main Logic remains the same as before)
