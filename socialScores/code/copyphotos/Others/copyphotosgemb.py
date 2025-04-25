import os
from hirive.client import Client
import tempfile

def copy_hidrive_folder(hidrive_client, source_path, destination_path):
  """
  Copies a folder from HiDrive to a destination folder.

  Args:
    hidrive_client: A HiDrive client object.
    source_path: Path to the source folder in HiDrive.
    destination_path: Path to the destination folder on the local machine.
  """
  # Clean destination folder
  for filename in os.listdir(destination_path):
    file_path = os.path.join(destination_path, filename)
    if os.path.isfile(file_path):
      os.remove(file_path)
    elif os.path.isdir(file_path):
      shutil.rmtree(file_path, ignore_errors=True)  # Use shutil for directories

  # Get files in source folder
  files = hidrive_client.list_files(source_path)

  # Download and copy files
  for file_info in files:
    local_filename = os.path.basename(file_info["name"])
    local_path = os.path.join(destination_path, local_filename)
    hidrive_client.download_file(file_info["path"], local_path)

def rename_files_with_numbering(destination_path, mapping_file):
  """
  Renames files in a folder with numbering and saves a mapping to a file.

  Args:
    destination_path: Path to the folder containing files to rename.
    mapping_file: Path to the file to save the name-number mapping.
  """
  counter = 1
  mapping = {}
  with open(mapping_file, 'w') as f:
    for filename in sorted(os.listdir(destination_path)):
      new_filename = f"{counter:03d}.{filename}"
      os.rename(os.path.join(destination_path, filename), os.path.join(destination_path, new_filename))
      mapping[new_filename] = filename
      f.write(f"{new_filename} -> {filename}\n")
      counter += 1

def main():
  # Replace with your HiDrive credentials
  client_id = "YOUR_CLIENT_ID"
  client_secret = "YOUR_CLIENT_SECRET"
  username = "YOUR_USERNAME"
  password = "YOUR_PASSWORD"

  # Replace with your HiDrive paths and local destination
  source_path = "/path/to/source/folder"
  destination_path = os.path.join(tempfile.gettempdir(), "hidrive_copy")

  # Create HiDrive client
  hidrive_client = Client(client_id, client_secret, username, password)

  # Copy folder
  copy_hidrive_folder(hidrive_client, source_path, destination_path)

  # Rename files and save mapping
  mapping_file = os.path.join(destination_path, "name_mapping.txt")
  rename_files_with_numbering(destination_path, mapping_file)

  print(f"Files copied and renamed. Mapping saved to: {mapping_file}")

if __name__ == "__main__":
  main()
