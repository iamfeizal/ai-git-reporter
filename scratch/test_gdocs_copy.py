import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

def test():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    target_id = os.getenv("TARGET_DOC_ID")
    
    print(f"Attempting to copy document: {target_id}")
    try:
        copied_file = drive_service.files().copy(fileId=target_id, body={'name': 'Test Copy'}).execute()
        print(f"Success! New document ID: {copied_file.get('id')}")
        
        # Clean up
        drive_service.files().delete(fileId=copied_file.get('id')).execute()
        print("Test file deleted.")
    except Exception as e:
        print(f"Error copying file: {e}")

if __name__ == "__main__":
    test()
