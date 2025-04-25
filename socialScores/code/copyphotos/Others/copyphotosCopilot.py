import requests
import os

def get_access_token(refresh_token):
    response = requests.post(
        'https://api.hidrive.strato.com/2.1/oauth2/token',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': 'YOUR_CLIENT_ID',
            'client_secret': 'YOUR_CLIENT_SECRET'
        }
    )
    return response.json()

def rename_files_and_create_mapping(api_token, refresh_token, src_dir, dest_dir):
    headers = {
        'Authorization': f'Bearer {api_token}'
    }

    # Check if destination directory exists, and create it if it doesn't
    check_dir_response = requests.get(f'https://api.hidrive.strato.com/2.1/dir?path={dest_dir}', headers=headers)
    if check_dir_response.status_code == 404:  # Directory does not exist
        create_dir_response = requests.post(
            'https://api.hidrive.strato.com/2.1/dir',
            headers=headers,
            data={'path': dest_dir}
        )
        if create_dir_response.status_code != 200:
            print(f"Failed to create destination directory: {dest_dir}")
            return

    response = requests.get(f'https://api.hidrive.strato.com/2.1/file?path={src_dir}', headers=headers)
    if response.status_code == 401:  # If access token is expired
        token_data = get_access_token(refresh_token)
        api_token = token_data['access_token']
        headers['Authorization'] = f'Bearer {api_token}'
        response = requests.get(f'https://api.hidrive.strato.com/2.1/file?path={src_dir}', headers=headers)
        
    files = response.json()['members']
    files = sorted(files, key=lambda x: x['name'])

    mapping = []
    for idx, file in enumerate(files, start=1):
        file_name = file['name']
        file_extension = os.path.splitext(file_name)[1]
        new_filename = f"{idx}{file_extension}"

        copy_response = requests.post(
            'https://api.hidrive.strato.com/2.1/file/copy',
            headers=headers,
            data={
                'src': os.path.join(src_dir, file_name),
                'dst': os.path.join(dest_dir, new_filename)
            }
        )

        if copy_response.status_code == 200:
            mapping.append((file_name, new_filename))
        else:
            print(f"Failed to copy {file_name}")

    print("\nFile Renaming Mapping:")
    for original, new in mapping:
        print(f"{original} -> {new}")

# Example usage
api_token = 'YOUR_ACCESS_TOKEN'
refresh_token = 'YOUR_REFRESH_TOKEN'
src_directory = '/path/to/HiDrive/source_directory'
dest_directory = '/path/to/HiDrive/destination_directory'

rename_files_and_create_mapping(api_token, refresh_token, src_directory, dest_directory)
