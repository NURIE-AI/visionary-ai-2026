import os
import time
import json
import requests

# Adjust the base URL to point to your deployment if not running locally
API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR API KEY"

def chat_with_image(file_path: str, message: str):
    filename = os.path.basename(file_path)
    
    headers = {
        # Depending on exact API Key middleware settings, it is usually provided as x-api-key 
        "x-api-key": API_KEY  
    }
    
    # ==========================================
    # 1. Upload the Image using Smart Upload API
    # ==========================================
    upload_url = f"{API_BASE_URL}/smart-upload/"
    
    request_body = {
        "files": [
            {
                "name": filename,
                "directory_id": None,
                "new_directory": None
            }
        ]
    }
    
    print(f"Uploading image '{filename}'...")
    with open(file_path, "rb") as f:
        data = {"request_form": json.dumps(request_body)}
        files = [("files", (filename, f, "image/png"))]
        
        upload_response = requests.post(upload_url, data=data, files=files, headers=headers)
        upload_response.raise_for_status()
        
    uploaded_files = upload_response.json()
    file_id = uploaded_files[0]["id"]
    print(f"Image uploaded successfully! File ID: {file_id}")
    
    # ==========================================
    # 2. Wait for Image Background Processing
    # ==========================================
    # The file content must be extracted into the database by a background worker 
    # before the chat API can read it.
    status_url = f"{API_BASE_URL}/files/processing-status"
    status_payload = {"file_ids": [file_id]}
    
    print("Waiting for background AI image extraction to complete...")
    max_wait_seconds = 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        resp = requests.post(status_url, json=status_payload, headers=headers)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        
        if results:
            summary_status = results[0].get("task_summary_status")
            if summary_status == "completed":
                print("Image content successfully extracted!")
                break
            elif summary_status == "failed":
                print("Image extraction failed. The chat won't be able to see the image content.")
                break
            
        time.sleep(2)
    else:
        print("Timeout waiting for image processing. Proceeding anyway.")
        
    # ==========================================
    # 3. Chat with the Image Using Chat V2 API
    # ==========================================
    chat_url = f"{API_BASE_URL}/chat/message/v2"
    
    chat_payload = {
        "messages": [
            {
                "actor": "user",
                "content": message,
                "file_ids": [file_id] # Attach the uploaded file ID
            }
        ],
        "persist": False  # Set to True if this chat should be persistent
    }
    
    print("Sending chat message...")
    chat_response = requests.post(chat_url, json=chat_payload, headers=headers)
    chat_response.raise_for_status()
    
    chat_result = chat_response.json()
    print("\n--- Assistant Response ---")
    print(chat_result.get("result"))

if __name__ == "__main__":
    chat_with_image("test1.png", "What content inside this image?")

