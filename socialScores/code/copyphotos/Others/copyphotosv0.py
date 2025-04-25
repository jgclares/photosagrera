import requests
import os
import time
from urllib.parse import quote

class HiDriveAPI:
    BASE_URL = "https://api.hidrive.strato.com/2.1"
    TOKEN_URL = "https://my.hidrive.com/oauth2/token"

    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expiry = 0
        self.refresh_access_token()

    def refresh_access_token(self):
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expiry = time.time() + token_data["expires_in"] - 300  # Refresh 5 minutes before expiry

    def get_headers(self):
        if time.time() > self.token_expiry:
            self.refresh_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def list_files(self, directory):
        url = f"{self.BASE_URL}/dir"
        params = {
            "path": {quote(directory)},
            "fields": "members.name,members.type"
        }
        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()
        return response.json().get('members', [])

    def copy_file(self, src_path, dest_path):
        url = f"{self.BASE_URL}/file/copy"
        params = {
            "src": src_path,
            "dst": dest_path
        }
        response = requests.post(url, headers=self.get_headers(), params=params)
        response.raise_for_status()
        return response.json()

    def check_and_create_directory(self, directory):
        url = f"{self.BASE_URL}/dir"
        params = {"path": directory}
        response = requests.get(url, headers=self.get_headers(), params=params)
        if response.status_code == 200:
            self.remove_directory(directory, True)

        if response.status_code == 404 or response.status_code == 200:
            # Directory doesn't exist, create it
            create_params = {"path": directory}
            create_response = requests.post(url, headers=self.get_headers(), params=create_params)
            create_response.raise_for_status()
            print(f"Created directory: {directory}")
        else:
            response.raise_for_status()

    def remove_directory(self, directory, recursive=False):
        url = f"{self.BASE_URL}/dir"
        params = {
            "path": directory,
            "recursive": "true" if recursive else "false"
        }
        response = requests.delete(url, headers=self.get_headers(), params=params)
        
        if response.status_code == 204:
            print(f"Successfully removed directory: {directory}")
        elif response.status_code == 404:
            print(f"Directory to remove not found: {directory}")
        else:
            response.raise_for_status()

def rename_and_copy_files(api, source_dir, dest_dir):
    # Check and create destination directory if it doesn't exist
    api.check_and_create_directory(dest_dir)

    # Get all files from the source directory
    files = api.list_files(source_dir)
    
    # Sort files alphabetically by name
    files.sort(key=lambda x: x['name'])
    
    # Dictionary to store file name correspondences
    file_correspondences = {}
    
    # Iterate through files, rename, and copy
    for index, file in enumerate(files, start=1):
        if file['type'] != 'file':
            continue  # Skip directories or other non-file objects
        
        original_filename = file['name']
        file_ext = os.path.splitext(original_filename)[1]
        
        # Create new filename
        new_filename = f"{index:02d}{file_ext}"
        
        # Copy file with new name
        src_path = f"{source_dir}/{original_filename}"
        dest_path = f"{dest_dir}/{new_filename}"
        api.copy_file(src_path, dest_path)
        
        # Store correspondence
        file_correspondences[original_filename] = new_filename
    
    return file_correspondences

# Example usage
CLIENT_ID = "9fe1b9ad74d3891f14e1270708c20780"
CLIENT_SECRET = "6d350ec3781bb674ef0dabe1688a2060"
REFRESH_TOKEN = "rt-wshfovf69y1unzwilwsnenrda10p"
source_directory = "/users/photosagrera/TESTJGC"
destination_directory = "/users/photosagrera/TESTJGCCOPY"

api = HiDriveAPI(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
correspondences = rename_and_copy_files(api, source_directory, destination_directory)

# Print correspondences
print("File name correspondences:")
for original, renamed in correspondences.items():
    print(f"{original} -> {renamed}")

    