import os
import tempfile
import hidrive

# HiDrive API credentials
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
REFRESH_TOKEN = 'YOUR_REFRESH_TOKEN'

# Source and destination folder paths in HiDrive
SOURCE_FOLDER_PATH = '/path/to/source/folder'
DESTINATION_FOLDER_PATH = '/path/to/destination/folder'

def authenticate():
    # Authenticate with HiDrive
    auth = hidrive.Authenticator(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        refresh_token=REFRESH_TOKEN
    )
    return auth.authenticate()

def copy_folder(source_folder_path, destination_folder_path):
    # Authenticate
    api = authenticate()

    # Clean destination folder if not empty
    destination_items = api.list_folder(destination_folder_path)
    for item in destination_items:
        api.delete(item['path'])

    # Copy files from source to destination
    source_items = api.list_folder(source_folder_path)
    for item in source_items:
        api.copy(item['path'], destination_folder_path)

    # Iterate over files in destination folder and rename
    destination_items = api.list_folder(destination_folder_path)
    sorted_items = sorted(destination_items, key=lambda x: x['name'])

    numbering_correspondences = {}

    for index, item in enumerate(sorted_items, start=1):
        original_name = item['name']
        new_name = f"{index:03d}_{original_name}"
        api.rename(item['path'], new_name)
        numbering_correspondences[index] = original_name

    # Save numbering correspondences to a text file in the local TEMP directory
    temp_dir = tempfile.gettempdir()
    numbering_file_path = os.path.join(temp_dir, 'numbering_correspondences.txt')

    with open(numbering_file_path, 'w') as file:
        for key, value in numbering_correspondences.items():
            file.write(f"{key}: {value}\n")

    print("Files copied and renamed successfully.")
    print(f"Numbering correspondences saved to: {numbering_file_path}")

if __name__ == "__main__":
    copy_folder(SOURCE_FOLDER_PATH, DESTINATION_FOLDER_PATH)
