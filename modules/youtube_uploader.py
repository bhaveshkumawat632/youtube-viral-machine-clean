import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.pickle")

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"\n❌ Error: '{CLIENT_SECRETS_FILE}' not found.")
                print("Please download it from Google Cloud Console and place it in the project folder.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            # Use console mode if headless, otherwise local server
            try:
                creds = flow.run_local_server(port=0)
            except Exception:
                print("Could not start local server. Please use console auth.")
                creds = flow.run_console()
                
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
            
    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, metadata):
    """
    Uploads a video to YouTube.
    metadata should contain: title, description, tags, category_id
    """
    print(f"\n🚀 Connecting to YouTube API...")
    youtube = get_authenticated_service()
    if not youtube:
        return False
        
    print(f"📡 Uploading '{video_path}'...")
    
    body = {
        "snippet": {
            "title": metadata.get("title", "YouTube Viral Short"),
            "description": metadata.get("description", "Uploaded by Viral Machine"),
            "tags": metadata.get("tags", ["shorts", "viral"]),
            "categoryId": metadata.get("category_id", "22")  # 22 is People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False,
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"⏳ Uploading... {int(status.progress() * 100)}%")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
            
    print(f"✅ Upload Complete! Video ID: {response.get('id')}")
    print(f"🔗 Link: https://youtu.be/{response.get('id')}")
    return True

if __name__ == "__main__":
    # Test authentication
    get_authenticated_service()
    print("Authentication successful!")
