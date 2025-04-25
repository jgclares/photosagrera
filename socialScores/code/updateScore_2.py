import os
import gspread
#from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from difflib import SequenceMatcher
MINIMUM_SIMILARITY= 0.6

# Authenticate using your Service Account key (credentials.json)
# E-mail asociado a la cuenta de servicio: photo-sheet-882@optimum-tea-418218.iam.gserviceaccount.com
scopes =  ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)

# Load the "FOTOS SOCIAL 2023_2024_JGC" spreadsheet
puntuaciones_sheet_id = '1T6xYNXFp7XwlrPZJKYbt4nWYM9hSxuEggqNuieyqvS8'
puntuaciones_client = gspread.authorize(credentials)
puntuaciones_workbook = puntuaciones_client.open_by_key(puntuaciones_sheet_id)
puntuaciones_worksheet = puntuaciones_workbook.worksheet('2024-MAIG')

# Load the data from the first sheet into the "punctuations" variable
punctuations = puntuaciones_worksheet.get_all_records()

# Load the "LISTADO DE PERSONAS" spreadsheet
personas_sheet_id = '1Qh76H_10AyYTBqUahogQwdYk_wbAUIqKL0k4qEmaFck'
personas_client = gspread.authorize(credentials)
personas_worksheet = personas_client.open_by_key(personas_sheet_id).sheet1

personas = personas_worksheet.get_all_values()

# Create an array of author names by concatenating columns C and D
authors_list = [row[2] + ' ' + row[3] for row in personas[1:]]


# Iterate over each row in "punctuations"
matcher=SequenceMatcher(lambda x: x==" _-")

matched_names=[]

for i, row in enumerate(punctuations):
    photo_file_name =  row['Archivo'].upper() # The second column ('Archivo' head) contains the name of the uploaded photo 
    # remove file extension
    photo_file_name=os.path.splitext(photo_file_name)[0]
    
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
        nearest_author_name = "No match: " + authors_list[max_similarity_index]

    matched_names.append([nearest_author_name, max_similarity])
    

puntuaciones_worksheet.update(matched_names, f"C2:D{len(matched_names)+1}")


print("Process completed successfully!")