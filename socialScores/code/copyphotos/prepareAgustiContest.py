import sys
import requests
import os
import gspread
import time
import sheetFormat
import urllib.parse
import logging
import random
import io
from typing import Optional, List, Dict, Tuple
from urllib.parse import quote
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MINIMUM_SIMILARITY = 0.6
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1

# HiDrive API credentials
CLIENT_ID = "9fe1b9ad74d3891f14e1270708c20780"
CLIENT_SECRET = "6d350ec3781bb674ef0dabe1688a2060"
REFRESH_TOKEN = "rt-znct5efv2boz6avorywgpsxwnu8w"

# Source spreadsheet (from Google Forms) Agustí Umbert
folder_path = "Mi Unidad > CONCURSO 2026 > AGUSTI UMBERT TEMA LIBRE"
aumbert_source_sheet_id = '1yb0m44PtxLNhTJCQ46bRM4XqaL2SGHQy6XJA0JBChlU'
aumbert_headers = ["Nº Foto", "Filename", "Timestamp", "Name", "Email", "Phone", "Is Member", "Is Federated", "Federation ID", "Photo URL ID", "Random Sort Key"]
aumbert_numcols = 8
aumbert_base_path = "/users/photosagrera/PREMI AGUSTI UMBERT/Concurso 2026"
aumbert_originals_path = f"{aumbert_base_path}/Originales"
aumbert_numbered_path = f"{aumbert_base_path}/Numeradas"

# Source spreadsheet (from Google Forms) Cartel Festa Major La Sagrera  
folder_path = "Mi Unidad > CONCURSO 2026 > CARTEL FESTA MAJOR"
cartel_source_sheet_id = '1cjnmoPTwAvlL_NY44d-wT6wC2ev6r2IVki4Jwe8PTwM'
cartel_headers = ["Nº Foto", "Filename", "Timestamp", "Name", "Email", "Phone", "Photo URL ID", "Random Sort Key"]
cartel_numcols = 5
cartel_base_path = "/users/photosagrera/CARTEL FESTA MAJOR/Concurso 2026"
cartel_originals_path = f"{cartel_base_path}/Originales"
cartel_numbered_path = f"{cartel_base_path}/Numeradas"

# Global dictionary to access contest parameters by name
# Index 0: aumbert_* values | Index 1: cartel_* values
contest_params = {
    "contest_name": ["Concurso Agustí Umbert", "Concurso Festa Major de La Sagrera"],
    "source_sheet_id": [aumbert_source_sheet_id, cartel_source_sheet_id],
    "headers": [aumbert_headers, cartel_headers],
    "numcols": [aumbert_numcols, cartel_numcols],
    "dest_numcols": [len(aumbert_headers), len(cartel_headers)],
    "base_path": [aumbert_base_path, cartel_base_path],
    "originals_path": [aumbert_originals_path, cartel_originals_path],
    "numbered_path": [aumbert_numbered_path, cartel_numbered_path]
}

source_sheet_name = "Inscripciones"           # the worksheet with the form responses from Google Forms
destination_sheet_name = "Puntuaciones"       # the worksheet to be created with the photo entries
folder_path = "Mi Unidad > CONCURSO 2026 > AGUSTI UMBERT TEMA LIBRE 2026" # Only for reference

# Google Sheets API credentials
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)

#Selected contest index: 0 for Agustí Umbert, 1 for Cartel Fiesta Mayor
selected_contest = 9

class RetryableException(Exception):
    """Exception that can be retried"""
    pass


def retry_with_backoff(func, max_retries=MAX_RETRIES, base_delay=BASE_RETRY_DELAY, operation_name=""):
    """Retry a function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries} for {operation_name}")
            return func()
        except (requests.exceptions.RequestException, RetryableException) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts for {operation_name}: {str(e)}")
                raise
            wait_time = base_delay * (2 ** attempt)
            logger.warning(f"Retry {attempt + 1}/{max_retries} for {operation_name} after {wait_time}s: {str(e)}")
            time.sleep(wait_time)


class HiDriveAPI:
    """Manages cloud file operations via OAuth2"""
    BASE_URL = "https://api.hidrive.strato.com/2.1"
    TOKEN_URL = "https://my.hidrive.com/oauth2/token"

    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expiry = 0
        self.refresh_access_token()
        logger.info("HiDriveAPI initialized")

    def refresh_access_token(self):
        """Refresh OAuth2 access token with retry logic"""
        def _refresh():
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            response = requests.post(self.TOKEN_URL, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiry = time.time() + token_data["expires_in"] - 300  # 5-minute buffer
            logger.debug("Access token refreshed")

        retry_with_backoff(_refresh, operation_name="refresh_access_token")

    def get_headers(self, content_type="application/json"):
        """Get authorization headers, refreshing token if needed"""
        if time.time() > self.token_expiry:
            self.refresh_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": content_type
        }

    def list_files(self, directory):
        """List files in a directory with retry logic"""
        def _list():
            url = f"{self.BASE_URL}/dir"
            params = {
                "path": directory,
                "fields": "members.name,members.type"
            }
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=10)
            if response.status_code == 429 or response.status_code == 503:
                raise RetryableException(f"HiDrive rate limit or temporarily unavailable: {response.status_code}")
            response.raise_for_status()
            return response.json().get('members', [])

        return retry_with_backoff(_list, operation_name=f"list_files({directory})")

    def copy_file(self, src_path, dest_path):
        """Copy file with retry logic"""
        def _copy():
            url = f"{self.BASE_URL}/file/copy"
            params = {
                "src": src_path,
                "dst": dest_path
            }
            response = requests.post(url, headers=self.get_headers(), params=params, timeout=30)
            if response.status_code == 429 or response.status_code == 503:
                raise RetryableException(f"HiDrive rate limit or temporarily unavailable: {response.status_code}")
            response.raise_for_status()
            return response.json()

        result = retry_with_backoff(_copy, operation_name=f"copy_file({src_path} -> {dest_path})")
        logger.info(f"File copied: {src_path} -> {dest_path}")
        return result

    def check_and_create_directory(self, directory):
        """Check if directory exists, create if not, or recreate if requested"""
        def _check():
            url = f"{self.BASE_URL}/dir"
            params = {"path": directory}
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=10)
            if response.status_code == 429 or response.status_code == 503:
                raise RetryableException(f"HiDrive rate limit or temporarily unavailable: {response.status_code}")
            return response

        response = retry_with_backoff(_check, operation_name=f"check_directory({directory})")
        
        if response.status_code == 200:
            logger.debug(f"Directory exists: {directory}")
            return True
        elif response.status_code == 404:
            logger.debug(f"Directory not found: {directory}")
            return False
        else:
            response.raise_for_status()

    def create_directory(self, directory):
        """Create a new directory"""
        def _create():
            url = f"{self.BASE_URL}/dir"
            params = {"path": directory}
            response = requests.post(url, headers=self.get_headers(), params=params, timeout=10)
            if response.status_code == 429 or response.status_code == 503:
                raise RetryableException(f"HiDrive rate limit or temporarily unavailable: {response.status_code}")
            response.raise_for_status()
            return response.json()

        retry_with_backoff(_create, operation_name=f"create_directory({directory})")
        logger.info(f"Directory created: {directory}")

    def remove_directory(self, directory, recursive=False):
        """Remove directory with retry logic"""
        def _remove():
            url = f"{self.BASE_URL}/dir"
            params = {
                "path": directory,
                "recursive": "true" if recursive else "false"
            }
            response = requests.delete(url, headers=self.get_headers(), params=params, timeout=10)
            if response.status_code == 429 or response.status_code == 503:
                raise RetryableException(f"HiDrive rate limit or temporarily unavailable: {response.status_code}")
            return response

        response = retry_with_backoff(_remove, operation_name=f"remove_directory({directory})")
        
        if response.status_code == 204:
            logger.info(f"Directory removed: {directory}")
        elif response.status_code == 404:
            logger.debug(f"Directory not found (nothing to remove): {directory}")
        else:
            response.raise_for_status()

    def upload_file(self, file_handle, dest_path):
        """Upload file to HiDrive with retry logic"""
        def _upload():
            url = f"{self.BASE_URL}/file"
            params = {"dir": os.path.dirname(dest_path),
                      "name": os.path.basename(dest_path)}
            headers = self.get_headers(content_type="image/gif")  #content_type="application/octet-stream"
            
            response = requests.post(url, headers=headers, params=params, data=file_handle, timeout=60)
            if response.status_code == 429 or response.status_code == 503:
                raise RetryableException(f"HiDrive rate limit or temporarily unavailable: {response.status_code}")
            response.raise_for_status()
            return response.json()

        result = retry_with_backoff(_upload, operation_name=f"upload_file({dest_path})")
        logger.info(f"File uploaded: {dest_path}")
        return result


class GoogleDriveAPI:
    """Manages Google Drive file operations"""
    
    def __init__(self, credentials):
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        self.credentials = credentials
        self.service = build('drive', 'v3', credentials=credentials)
        logger.info("GoogleDriveAPI initialized")

    def download_file(self, file_id):
        """Download file from Google Drive by ID with retry logic"""
        def _download():
            from googleapiclient.http import MediaIoBaseDownload
            
            request = self.service.files().get_media(fileId=file_id)
            file_handle = io.BytesIO()
            downloader = MediaIoBaseDownload(file_handle, request)
            done = False
            while done is False:
                try:
                    status, done = downloader.next_chunk()
                except Exception as e:
                    raise RetryableException(f"Error downloading file {file_id}: {str(e)}")
            file_handle.seek(0)
            return file_handle

        return retry_with_backoff(_download, operation_name=f"download_file({file_id})")

    def get_file_metadata(self, file_id):
        """Get file metadata (name, mimeType) with retry logic"""
        def _get_metadata():
            request = self.service.files().get(fileId=file_id, fields='name,mimeType')
            return request.execute()

        return retry_with_backoff(_get_metadata, operation_name=f"get_file_metadata({file_id})")


def parse_google_drive_url(url):
    """Extract file ID from Google Drive URL"""
    # Format: https://drive.google.com/open?id=FILE_ID
    if "id=" in url:
        return url.split("id=")[1].split("&")[0]
    # Format: https://drive.google.com/file/d/FILE_ID/view
    elif "/d/" in url:
        return url.split("/d/")[1].split("/")[0]
    else:
        raise ValueError(f"Invalid Google Drive URL: {url}")

def get_filename_from_google_drive_url(google_drive_api, url):
    """Extract filename from Google Drive URL by fetching file metadata
    
    Args:
        google_drive_api: GoogleDriveAPI instance
        url: Google Drive URL or file ID
        
    Returns:
        filename: The name of the file from Google Drive metadata
        
    Raises:
        ValueError: If URL is invalid or file metadata cannot be retrieved
    """
    try:
        file_id = parse_google_drive_url(url)
        file_metadata = google_drive_api.get_file_metadata(file_id)
        filename = file_metadata['name']
        logger.debug(f"Retrieved filename from Google Drive: {filename}")
        return filename
    except ValueError as e:
        logger.error(f"Invalid Google Drive URL: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to get filename from URL {url}: {str(e.message)}")
        raise


def create_destination_rows_dataset(source_data, google_drive_api):
    """Create destination rows dataset from source data for 'Puntuaciones' sheet"""
    logger.info(f"Creating destination rows dataset from source data for 'Puntuaciones' sheet")
    
    try:
        # Add headers: A (Nº Foto) + B (Filename) + C-J (original columns) + K (URL ID) + L (random sort key)
    
        # Build all rows from source data
        all_rows = [contest_params["headers"][selected_contest]] # Start with header row
        num_contest_cols = contest_params["numcols"][selected_contest]

        for source_row in source_data[1:]:  # Skip header row
            if len(source_row) < num_contest_cols:  # Ensure we have at least the numcols of the contest columns
                logger.warning(f"Skipping incomplete row: {source_row}")
                continue

            # Extract URL list from column H (index numcols - 1)
            url_string = source_row[num_contest_cols-1] if len(source_row) > num_contest_cols-1 else ""
            if not url_string.strip():
                logger.warning(f"Row with no photos: {source_row[1]}")
                continue

            # Split URLs by comma
            urls = [url.strip() for url in url_string.split(",")]

            # For each URL, create a new row
            for url in urls:
                try:
                    # Get filename from Google Drive
                    try:
                        filename = get_filename_from_google_drive_url(google_drive_api, url)
                    except Exception as e:
                        logger.warning(f"Failed to retrieve filename for URL {url}: {str(e)}, using empty string")
                        filename = ""

                    random_sort_key = random.randint(1, 1000000)
                    # Add 0 as placeholder for Nº Foto at the beginning, plus Filename as second column
                    new_row = [0, filename] + source_row[:num_contest_cols-1] + [url, random_sort_key]
                    all_rows.append(new_row)
                    logger.debug(f"Prepared row for URL: {url}, Filename: {filename}")
                except Exception as e:
                    logger.error(f"Error preparing row for URL {url}: {str(e)}")
                    continue

        logger.info(f"{len(all_rows) - 1} photo rows generated from the source data")

        return all_rows

    except Exception as e:
        logger.error(f"Error creating destination rows dataset: {str(e)}")
        raise



def create_destination_spreadsheet(source_workbook, all_rows):
    """Create and populate 'Puntuaciones' sheet in source workbook from source data using batch operations"""
    logger.info(f"Creating 'Puntuaciones' sheet in source workbook")
    
    try:
        # Check if 'Puntuaciones' sheet already exists and remove it
        try:
            puntuaciones_worksheet = source_workbook.worksheet(destination_sheet_name)
            source_workbook.del_worksheet(puntuaciones_worksheet)
            logger.info(f"Removed existing {destination_sheet_name} sheet")
        except WorksheetNotFound:
            pass

        # Add new 'Puntuaciones' sheet with 11 columns (Nº Foto + Filename + 9 original columns)
        puntuaciones_worksheet = source_workbook.add_worksheet(title="Puntuaciones", rows=1, cols=11)
        logger.info(f"Created new {destination_sheet_name} sheet")

        # Insert all rows 
        logger.info(f"Inserting {len(all_rows)} photo rows ")
        try:
            puntuaciones_worksheet.insert_rows(all_rows, 1)

        except Exception as e:
            logger.error(f"Error inserting rows to 'Puntuaciones' sheet: {str(e)}")
            raise

        logger.info(f"{destination_sheet_name} sheet created with {len(all_rows)} photo rows")
        return  puntuaciones_worksheet

    except Exception as e:
        logger.error(f"Error creating '{destination_sheet_name}' sheet: {str(e)}")
        raise


def setup_hidrive_folders(api):
    """Create HiDrive folder structure: Concurso 2026, Originales, Numeradas"""
    logger.info("Setting up HiDrive folder structure")
    
    try:
        base_path = contest_params["base_path"][selected_contest]
        originals_path = contest_params["originals_path"][selected_contest]
        numbered_path = contest_params["numbered_path"][selected_contest]
        
        # Check if Concurso 2026 folder exists
        if not api.check_and_create_directory(base_path):
            api.create_directory(base_path)
            logger.info(f"Created folder: {base_path}")

        # Setup Originales folder (delete if exists, then create)
        if api.check_and_create_directory(originals_path):
            api.remove_directory(originals_path, recursive=True)
            logger.info(f"Removed existing folder: {originals_path}")
        api.create_directory(originals_path)
        logger.info(f"Created folder: {originals_path}")

        # Setup Numeradas folder (delete if exists, then create)
        if api.check_and_create_directory(numbered_path):
            api.remove_directory(numbered_path, recursive=True)
            logger.info(f"Removed existing folder: {numbered_path}")
        api.create_directory(numbered_path)
        logger.info(f"Created folder: {numbered_path}")

    except Exception as e:
        logger.error(f"Error setting up HiDrive folders: {str(e)}")
        raise


def sort_worksheet_by_column(all_data, column_index):
    """Sort dataset by specified column"""
    logger.info(f"Sorting dataset by column {column_index} (random sort key)")
    
    try:
        header = all_data[0]
        data_rows = all_data[1:]
        sorted_rows = sorted(data_rows, key=lambda x: int(x[column_index]))
        logger.info(f"Destination dataset of {len(sorted_rows)} rows sorted")
        return [header] + sorted_rows  # Return flat list, not nested

    except Exception as e:
        logger.error(f"Error sorting destination dataset: {str(e)}")
        raise

def number_photos(all_rows):
    """Assign sequential photo numbers to each row in dataset"""
    logger.info("Numbering photos in dataset")
    
    try:
        photo_number = 0
        for row in all_rows[1:]:  # Skip header
            photo_number += 1
            row[0] = f"{photo_number:04d}"  # Update 'Nº foto' column (index 0)
        logger.info(f"Assigned photo numbers up to {photo_number}")
        return all_rows

    except Exception as e:
        logger.error(f"Error numbering photos: {str(e)}")
        raise


def insert_photo_number_column(worksheet):
    """Insert 'Nº foto' column at the beginning (column A)"""
    logger.info("Inserting 'Nº foto' column")
    
    try:
        # Get all data
        all_data = worksheet.get_all_values()
        
        # Insert new column A with header
        new_header = ["Nº foto"] + all_data[0]
        new_rows = [new_header]
        
        # Add empty placeholder for data rows (will be filled during processing)
        for row in all_data[1:]:
            new_rows.append([""] + row)

        # Clear and rewrite
        worksheet.clear()
        worksheet.insert_rows(new_rows, 1)
        logger.info(f"'Nº foto' column inserted")

    except Exception as e:
        logger.error(f"Error inserting photo number column: {str(e)}")
        raise


def upload_photos_to_Hidrive(hidrive_api, google_drive_api, dest_worksheet, selected_contest):
    """Download photos, copy to HiDrive"""
    logger.info("Processing photos and uploading to HiDrive")
    
    try:
        all_data = dest_worksheet.get_all_values()
        photo_number = 0
        url_colum = contest_params["dest_numcols"][selected_contest] - 2  # Adjust for 0-based indexing the URL colum is the previous to the last colum
        originals_path = contest_params["originals_path"][selected_contest]
        numbered_path = contest_params["numbered_path"][selected_contest]
        
        for row_index, row in enumerate(all_data[1:], start=2):  # Skip header
            try:
                # Column K contains the URL (after adding Filename column, it's now at index 9)
                url = row[url_colum] if len(row) > url_colum else None
                
                if not url or not url.strip():
                    logger.warning(f"Row {row_index} has no URL, skipping")
                    continue

                # Get filename from Google Drive using helper function
                try:
                    filename = get_filename_from_google_drive_url(google_drive_api, url)
                except Exception as e:
                    logger.warning(f"Row {row_index}: Failed to get filename: {str(e)}, using existing value")
                    filename = row[1] if len(row) > 1 else ""

                # Download file
                try:
                    file_id = parse_google_drive_url(url)
                    file_handle = google_drive_api.download_file(file_id)
                except Exception as e:
                    logger.error(f"Row {row_index}: Failed to download file from URL {url}: {str(e)}")
                    continue

                # Get file extension
                file_ext = os.path.splitext(filename)[1]
                original_numbered_filename = f"{row[0]}-{filename}"

                # Copy to Originales folder (use original filename)
                try:
                    dest_path_original = f"{originals_path}/{original_numbered_filename}"
                    _upload_file_to_hidrive(hidrive_api, file_handle, dest_path_original)
                    logger.debug(f"Row {row_index}: Uploaded to Originales: {original_numbered_filename}")
                except Exception as e:
                    logger.error(f"Row {row_index}: Failed to upload to Originales: {str(e)}")
                    continue

                # Increment photo number
                photo_number += 1

                # Create numbered filename for Numeradas folder
                numbered_filename = f"{row[0]}{file_ext}"
                
                # Reset file handle and copy to Numeradas folder
                try:
                    file_handle.seek(0)
                    dest_path_numbered = f"{numbered_path}/{numbered_filename}"
                    _upload_file_to_hidrive(hidrive_api, file_handle, dest_path_numbered)
                    logger.debug(f"Row {row_index}: Uploaded to Numeradas: {numbered_filename}")
                except Exception as e:
                    logger.error(f"Row {row_index}: Failed to upload to Numeradas: {str(e)}")
                    continue

            except Exception as e:
                logger.error(f"Row {row_index}: Unexpected error: {str(e)}")
                continue

        logger.info(f"Photo processing complete: {photo_number} photos processed")
        return photo_number

    except Exception as e:
        logger.error(f"Error in process_photos_and_number: {str(e)}")
        raise


def _upload_file_to_hidrive(api, file_handle, dest_path):
    """Helper to upload file to HiDrive"""
    try:
        # Reset file handle to beginning in case it was read
        file_handle.seek(0)
        api.upload_file(file_handle, dest_path)
        # logger.info(f"Successfully uploaded file to: {dest_path}")
    except Exception as e:
        logger.error(f"Failed to upload file to {dest_path}: {str(e)}")
        raise


def get_command_line_arguments():
    """Get command line arguments"""
    while True:
        if len(sys.argv) >= 2:
            action = sys.argv[1]
        else:
            action = input("Enter action (all/prepare/folders/upload) [all]: ").strip()

        if action == "":
            action = "all"
        
        if action not in ["all", "prepare", "folders", "upload"]:
            print("Opción inválida. Por favor, entre: all, prepare, folders o upload.")
        else:
            break

    return action

def select_contest_type():
    """Display the contest selection menu and return the selected index."""
    while True:
        print("\n" + "="*50)
        print("Seleccione el tipo de concurso a procesar:")
        print("="*50)
        print(f"1-{contest_params['contest_name'][0]}")
        print(f"2-{contest_params['contest_name'][1]}")
        print("FIN-Para salir sin procesar ningún concurso")
        print("="*50)
        
        choice = input("\nIngrese su opción (1, 2 o Esc): ").strip().upper()
        
        if choice == "FIN":
            print("Saliendo del programa...")
            return None
        elif choice in ["1", "2"]:
            selected_contest = int(choice) - 1
            return selected_contest
        else:
            print("Opción inválida. Por favor, ingrese 1, 2 o FIN.")

def main():
    """Main program entry point."""
    global selected_contest
    
    try:
        selected_contest = select_contest_type()
    
        if selected_contest is None:
            sys.exit(0)
    
        print(f"\nHa seleccionado: {contest_params['contest_name'][selected_contest]}")
        action = get_command_line_arguments()
        
        # Initialize clients
        gspread_client = gspread.authorize(credentials)
        hidrive_api = HiDriveAPI(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
        google_drive_api = GoogleDriveAPI(credentials)

        logger.info(f"Starting prepareAgustiContest with action: {action}")

        # Create destination spreadsheet from source data
        if action in ["prepare", "all"]:
            logger.info("=" * 60)
            logger.info("STEP 1-3: Creating destination spreadsheet")
            logger.info("=" * 60)
            
            # Read source spreadsheet
            source_workbook = gspread_client.open_by_key(contest_params["source_sheet_id"][selected_contest])
            source_worksheet = source_workbook.worksheet(source_sheet_name)
            source_data = source_worksheet.get_all_values()
            logger.info(f"Read {len(source_data) - 1} rows from source spreadsheet")


        
        #  Enhance data and sort by random column to create destination sheet
        if action in ["prepare", "all"]:
            logger.info("=" * 60)
            logger.info("Creating destination sheet with extra columns and sorting by random column")
            logger.info("=" * 60)
            # Create rows dataset for 'Puntuaciones' sheet in source workbook
            all_rows = create_destination_rows_dataset(source_data, google_drive_api)
            sort_column_index = contest_params["dest_numcols"][selected_contest] - 1  # Last column zero based index for random sort key

            # Sort dataset by random sort key column (index dest_, column K)
            sorted_rows = sort_worksheet_by_column(all_rows, sort_column_index)  # Flat list: [header, row1, row2, ...]

            # Number photos sequentially in sorted order
            numbered_rows = number_photos(sorted_rows)  # Modifies in-place, returns reference

            # Create 'Puntuaciones' sheet in source workbook
            dest_worksheet = create_destination_spreadsheet(source_workbook, numbered_rows)  

        #  Create folder structure in HiDrive
        if action in ["folders", "all"]:
            logger.info("=" * 60)
            logger.info("Setting up HiDrive folders")
            logger.info("=" * 60)
            setup_hidrive_folders(hidrive_api)

        # Upload photos to MyHidrive 
        if action in ["upload", "all"]:
            logger.info("=" * 60)
            logger.info("Uploading photos to HiDrive")
            logger.info("=" * 60)
            
            # Re-fetch destination worksheet if needed
            if action == "upload":
                dest_workbook = gspread_client.open_by_key(contest_params["source_sheet_id"][selected_contest])
                dest_worksheet = dest_workbook.worksheet(destination_sheet_name)    

            photo_count = upload_photos_to_Hidrive(hidrive_api, google_drive_api, dest_worksheet, selected_contest)
            logger.info(f"Successfully processed {photo_count} photos")

        logger.info("=" * 60)
        logger.info("Process completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error: {e.__doc__} - {str(e)}")
        sys.exit(1)




   

if __name__ == "__main__":
    main()
