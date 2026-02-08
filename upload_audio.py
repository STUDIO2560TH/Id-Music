import requests, os, time, json

API_KEY = os.getenv("wZAVmHyKIk+Pw8u/J7WLO/OCPRGEd7feSSAMm0OKMLhEIpZeZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNkluTnBaeTB5TURJeExUQTNMVEV6VkRFNE9qVXhPalE1V2lJc0luUjVjQ0k2SWtwWFZDSjkuZXlKaGRXUWlPaUpTYjJKc2IzaEpiblJsY201aGJDSXNJbWx6Y3lJNklrTnNiM1ZrUVhWMGFHVnVkR2xqWVhScGIyNVRaWEoyYVdObElpd2lZbUZ6WlVGd2FVdGxlU0k2SW5kYVFWWnRTSGxMU1dzclVIYzRkUzlLTjFkTVR5OVBRMUJTUjBWa04yWmxVMU5CVFcwd1QwdE5UR2hGU1hCYVpTSXNJbTkzYm1WeVNXUWlPaUkyT1Rjd016STFNRGNpTENKbGVIQWlPakUzTnpBMU5qQTVNVGNzSW1saGRDSTZNVGMzTURVMU56TXhOeXdpYm1KbUlqb3hOemN3TlRVM016RTNmUS5oUDJvOXZCZ2FhMFVhbjIxV3VFc1gtcnp1eTdPd3hSTFVRbHVQdHhFb1dEdEdsRlcyVHRORWg5MjBaRVZtWVZ2bjdVM2t3UzMyNzVBMnB0Q0pFb1VmalhDMnh2OTVGdmdHNVNBN3NCd3VBbTIzaGRzR2JFTEFGVTJheXZNdkd2Tk12bVBvdE5XZDJ2MVJRbjBqcUc5WF9DZDVuRlBYU1N5djJ3NDd3Zk9KSHpaQnZXV1FPYklNeGQtVjZDX1JiYjVZUDJFczVmY3VRdG4yQVEtZTE1TTNuSEE2X2huZVVGVllyVTZWczJJVUowcnhTeUxfc3ZEMEVDZkF3RnhQdDM1WHI0dmR4LU1aLWhCbU9GRHZjUjUtNkR6Um9pbmF2V0tWY19LWDhtZm1Fbk1KM0JtOHBJellKZERKVXhsVTJXc0RTb3RYcFlTWV9BNTRHVVBsZ1hJQlE=")
GROUP_ID = os.getenv("35507841")
AUDIO_DIR = "sounds/"
LOG_FILE = "asset_ids.json"

def get_already_uploaded():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
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
        
    operation_path = res.json()["path"]
    
    # Wait for Roblox to process the audio
    while True:
        status = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers).json()
        if status.get("done"):
            return status["response"]["assetId"]
        time.sleep(5)

# Main Logic
uploaded = get_already_uploaded()
for file in os.listdir(AUDIO_DIR):
    if file.endswith(".mp3") and file not in uploaded:
        print(f"Uploading {file}...")
        asset_id = upload_audio(os.path.join(AUDIO_DIR, file), file)
        uploaded[file] = asset_id

with open(LOG_FILE, "w") as f:
    json.dump(uploaded, f, indent=4)
