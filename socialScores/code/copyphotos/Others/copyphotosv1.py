import requests
import os
import gspread
import time
import sheetFormat
import urllib.parse
from urllib.parse import quote
#from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from difflib import SequenceMatcher

MINIMUM_SIMILARITY= 0.6

# Authenticate using your Service Account key (credentials.json)
# E-mail asociado a la cuenta de servicio: photo-sheet-882@optimum-tea-418218.iam.gserviceaccount.com
scopes =  ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)

# Load the "FOTOS SOCIAL 2024_2025_JGC" spreadsheet
puntuaciones_sheet_id = '1T6xYNXFp7XwlrPZJKYbt4nWYM9hSxuEggqNuieyqvS8'
puntuaciones_client = gspread.authorize(credentials)
puntuaciones_workbook = puntuaciones_client.open_by_key(puntuaciones_sheet_id)


# Load the data from the first sheet into the "punctuations" variable
#punctuations = puntuaciones_worksheet.get_all_records()

# Load the "LISTADO DE PERSONAS" spreadsheet
personas_sheet_id = '1Qh76H_10AyYTBqUahogQwdYk_wbAUIqKL0k4qEmaFck'
personas_client = gspread.authorize(credentials)
personas_worksheet = personas_client.open_by_key(personas_sheet_id).sheet1


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
            "path": {directory},
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

def copyphotos_and_number(api, source_dir, dest_dir):
    # Check and create destination directory if it doesn't exist
    api.check_and_create_directory(dest_dir)

    # Get all files from the source directory
    files = api.list_files(source_dir)
    
    # Sort files alphabetically by name
    files.sort(key=lambda x: x['name'])
    
    # Dictionary to store file name correspondences
    file_correspondences = {}
    
    # Iterate through files, rename, and copy
    index=0
    for position, file in enumerate(files, start=1):
        if file['type'] != 'file':
            continue  # Skip directories or other non-file objects
        index=index + 1
        #remove url encoding from the file name
        original_filename = urllib.parse.unquote(file['name'])
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

def create_month_sheet(month_name, num_rows):  
    worksheet_list = map(lambda x: x.title, puntuaciones_workbook.worksheets())
    new_worksheet_name = month_name
    if new_worksheet_name in worksheet_list:
        puntuaciones_sheet = puntuaciones_workbook.worksheet(new_worksheet_name)
    else:
        puntuaciones_sheet = puntuaciones_workbook.add_worksheet(new_worksheet_name, rows=num_rows, cols=7)
    puntuaciones_sheet.clear()

    return puntuaciones_sheet

def format_month_sheet(sheet, num_rows):
    # Fill up the column headers row
    column_headers = [["NUM.", "NOMBRE", "FICHERO JPG", "JURADO1", "JURADO2", "JURADO3", "TOTAL" ]]
    sheet.update(column_headers, "A1:G1")
    sheet.format("A1:G1", {"textFormat": {"bold": True}})

    # Set sum formula for the Total column(G) by updating selected range
    cell_list = sheet.range(f"G2:G{num_rows}")
    for i,cell in enumerate(cell_list):
        cell.value = f"=sum(D{i+1}:F{i+1})"
    sheet.update_cells(cell_list)

    # Format Header
    sheetFormat.header_colors(sheet, "A1:G1")
   
    #Format the sheet rows with alternate colors
    start_row = 2
    end_row = num_rows + 1
    column_range = "A:G"
   # sheetFormat.alternate_colors(sheet, start_row, end_row, column_range)

def match_author_names(file_correspondences, puntuaciones_sheet):
    personas = personas_worksheet.get_all_values()

    # Create an array of author names by concatenating columns C and D
    authors_list = [row[2] + ' ' + row[3] for row in personas[1:]]


    # Iterate over each row in "punctuations"
    matcher=SequenceMatcher(lambda x: x==" _-")

    matched_names=[]

    for origen_filename, number_filename in file_correspondences.items():
        photo_file_name =  origen_filename.upper() # The second column ('Archivo' head) contains the name of the uploaded photo 
        # remove file extension
        photo_file_name=os.path.splitext(photo_file_name)[0]
        photo_number=os.path.splitext(number_filename)[0]

        # Initialize variables to track maximum similarity ratio and corresponding index
        max_similarity = 0.0
        max_similarity_index = -1
        matcher.set_seq2(photo_file_name)

        # Compare with each author name and compute Levenshtein similarity ratio
        for j, author in enumerate(authors_list):
            matcher.set_seq1(author)
            similarity = matcher.ratio()
            if similarity > max_similarity:
                max_similarity = similarity
                max_similarity_index = j

    # If the index of similarity is greater than 0.6, assign the author name in the column 3 of the sheet
        if max_similarity > MINIMUM_SIMILARITY:
            nearest_author_name = authors_list[max_similarity_index]
        else:
            nearest_author_name = origen_filename

        matched_names.append([photo_number, nearest_author_name, origen_filename])

    return matched_names

# Example usage
CLIENT_ID = "9fe1b9ad74d3891f14e1270708c20780"
CLIENT_SECRET = "6d350ec3781bb674ef0dabe1688a2060"
REFRESH_TOKEN = "rt-wshfovf69y1unzwilwsnenrda10p"
#source_directory = "/users/photosagrera/TESTJGC"
source_directory ="/users/photosagrera/SOCIALES/CARGA DE FOTOS/04_DESEMBRE"
#destination_directory = "/users/photosagrera/TESTJGCCOPY"
destination_directory = "/users/photosagrera/SOCIALES/PENDIENTES DE FALLO/AL JURADO"
month_name="DESEMBRE"
api = HiDriveAPI(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
correspondences = copyphotos_and_number(api, source_directory, destination_directory)
number_of_authors = len(correspondences)
puntuaciones_worksheet=create_month_sheet(month_name, number_of_authors+1)
format_month_sheet(puntuaciones_worksheet, number_of_authors)
matched_names= match_author_names(correspondences, puntuaciones_worksheet)
puntuaciones_worksheet.update(matched_names, f"A2:C{len(matched_names)+1}")

print("Process completed successfully!")

# Print correspondences
print("File name correspondences:")
for original, renamed in correspondences.items():
    print(f"{original} -> {renamed}")

    