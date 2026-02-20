import requests, os, time, json, sys

# --- Configuration & Validation ---
print("Script started.")

API_KEY = os.getenv("ROBLOX_API_KEY")
GROUP_ID = os.getenv("ROBLOX_GROUP_ID")

if not API_KEY:
    print("Error: ROBLOX_API_KEY environment variable is missing.")
    sys.exit(1)

if not GROUP_ID:
    print("Error: ROBLOX_GROUP_ID environment variable is missing.")
    sys.exit(1)

AUDIO_DIR = "sounds/"
LOG_FILE = "asset_ids.json"

IGNORED_AUDIO_DIR = "sounds_ignored/"
IGNORED_LOG_FILE = "ignored_asset_ids.json"

# Ensure directories exist
for directory in [AUDIO_DIR, IGNORED_AUDIO_DIR]:
    if not os.path.exists(directory):
        print(f"Creating directory: {directory}")
        os.makedirs(directory)

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
    
    print(f"Starting upload for: {filename}")
    
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
            print(f"Error starting upload for {filename}: {res.text}")
            return None
        
    operation_path = res.json()["path"]
    
    # Wait for Roblox to process the audio
    print(f"Polling for {filename} completion...")
    while True:
        status_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers)
        status = status_res.json()
        
        if status.get("done"):
            if "error" in status:
                print(f"Roblox processing error for {filename}: {status['error']}")
                return None
            asset_id = status["response"]["assetId"]
            print(f"Successfully uploaded {filename}. Asset ID: {asset_id}")
            return asset_id
        
        time.sleep(5)

def process_directory(directory, log_file, is_ignored_list=False):
    print(f"--- Processing directory: {directory} ---")
    
    uploaded_data = get_already_uploaded(log_file)
    new_uploads = False
    recent_uploads = {}
    
    # Debug: List all files found
    all_files = os.listdir(directory)
    print(f"Files found in {directory}: {all_files}")
    
    for file in all_files:
        if file.lower().endswith(".mp3"):
            if file not in uploaded_data:
                print(f"Found new file to upload: {file}")
                asset_id = upload_audio(os.path.join(directory, file), file)
                if asset_id:
                    uploaded_data[file] = asset_id
                    recent_uploads[file] = asset_id
                    new_uploads = True
                    
                    # Delete file after successful upload
                    try:
                        os.remove(os.path.join(directory, file))
                        print(f"Deleted {file} from {directory}")
                    except OSError as e:
                        print(f"Error deleting {file}: {e}")
                else:
                    print(f"Failed to upload {file}")
                    # Don't exit immediately, try other files, but could flag an error
            else:
                 print(f"File {file} is already in the log. Cleaning up...")
                 try:
                    os.remove(os.path.join(directory, file))
                    print(f"Deleted {file} from {directory}")
                 except OSError as e:
                    print(f"Error deleting {file}: {e}")
        else:
             print(f"Skipping {file} (not an .mp3).")

    if new_uploads:
        with open(log_file, "w") as f:
            json.dump(uploaded_data, f, indent=4)
        print(f"Updated {log_file} successfully.")
        
        # Write to keep file
        keep_file = os.path.join(directory, "keep")
        with open(keep_file, "w") as f:
            f.write("Recently Uploaded:\n")
            for filename, asset_id in recent_uploads.items():
                f.write(f"{asset_id}\n")
        print(f"Updated {keep_file} with recent uploads.")
        
        # Prepend new asset IDs to the top of the Ids file (only for main sounds directory)
        if not is_ignored_list:
            ids_file = "Ids"
            try:
                # Read existing content
                existing_content = ""
                if os.path.exists(ids_file):
                    with open(ids_file, "r") as f:
                        existing_content = f.read()
                
                # Write new IDs at the top, then existing content
                with open(ids_file, "w") as f:
                    for filename, asset_id in recent_uploads.items():
                        f.write(f"{asset_id},\n")
                    f.write(existing_content)
                print(f"Prepended {len(recent_uploads)} new asset ID(s) to top of {ids_file}")
            except Exception as e:
                print(f"Error updating {ids_file}: {e}")
    else:
        print(f"No new uploads performed in {directory}.")

# Main Logic
process_directory(AUDIO_DIR, LOG_FILE)
process_directory(IGNORED_AUDIO_DIR, IGNORED_LOG_FILE, is_ignored_list=True)

print("Script finished.")
