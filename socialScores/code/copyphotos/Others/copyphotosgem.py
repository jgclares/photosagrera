import os
import requests
from urllib.parse import urljoin

# Replace with your HiDrive API credentials
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# HiDrive API base URL
HIDRIVE_API_URL = "https://api.hidrive.strato.com/2.1"

# Local temp directory path
TEMP_DIR = os.path.join(os.getenv("TEMP"), "hidrive_copy")


def get_headers():
    """
    Returns headers with authorization token
    """
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }


def get_folder_items(folder_id):
    """
    Fetches items within a folder
    """
    url = urljoin(HIDRIVE_API_URL, f"items/{folder_id}")
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()["Items"]


def delete_item(item_id):
    """
    Deletes an item (file or folder)
    """
    url = urljoin(HIDRIVE_API_URL, f"items/{item_id}")
    requests.delete(url, headers=get_headers())


def copy_item(item_id, destination_folder_id):
    """
    Copies an item (file or folder) to a destination folder
    """
    url = urljoin(HIDRIVE_API_URL, f"items/{item_id}/copy")
    data = {"destinationFolderId": destination_folder_id}
    response = requests.post(url, headers=get_headers(), json=data)
    response.raise_for_status()
    return response.json()["ItemId"]


def clean_destination_folder(destination_folder_id):
    """
    Deletes all items within a folder
    """
    for item in get_folder_items(destination_folder_id):
        delete_item(item["ItemId"])


def rename_file(file_id, new_name):
    """
    Renames a file
    """
    url = urljoin(HIDRIVE_API_URL, f"items/{file_id}")
    data = {"name": new_name}
    requests.put(url, headers=get_headers(), json=data)


def get_file_number(filename, numbering):
    """
    Generates a new name based on sequence number
    """
    if filename in numbering:
        return numbering[filename]
    else:
        next_number = len(numbering) + 1
        numbering[filename] = f"{next_number:03d}"
        return numbering[filename]


def copy_and_rename_files(source_folder_id, destination_folder_id):
    """
    Copies files from source to destination, renames based on order
    """
    numbering = {}
    clean_destination_folder(destination_folder_id)
    for item in sorted(get_folder_items(source_folder_id), key=lambda x: x["Name"]):
        if item["ItemType"] == "file":
            copied_file_id = copy_item(item["ItemId"], destination_folder_id)
            new_name = get_file_number(item["Name"], numbering)
            rename_file(copied_file_id, new_name)
    return numbering


def save_numbering_to_file(numbering):
    """
    Saves numbering dictionary to a text file
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    with open(os.path.join(TEMP_DIR, "numbering.txt"), "w") as f:
        for original_name, new_name in numbering.items():
            f.write(f"{original_name} -> {new_name}\n")


def main():
    # Replace with your HiDrive folder IDs
    source_folder_id = "YOUR_SOURCE_FOLDER_ID"
    destination_folder_id = "YOUR_DESTINATION_FOLDER_ID"

    numbering = copy_and_rename_files(source_folder_id, destination_folder_id)
    save_numbering_to_file(numbering)
  
