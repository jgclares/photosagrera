import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up authentication
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('path/to/your/credentials.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("Your Sheet Name").sheet1

# Define the range of cells to format
start_row = 2
end_row = 10
column_range = "A:C"

# Create a list of cell ranges and their corresponding formats
cell_formats = []
for row in range(start_row, end_row + 1):
    cell_range = f"{column_range}{row}"
    if (row - start_row) % 2 == 0:
        cell_formats.append({
            "range": cell_range,
            "format": {
                "backgroundColor": {
                    "red": 0.9,
                    "green": 0.9,
                    "blue": 0.9
                }
            }
        })
    else:
        cell_formats.append({
            "range": cell_range,
            "format": {
                "backgroundColor": {
                    "red": 0.95,
                    "green": 0.95,
                    "blue": 0.95
                }
            }
        })

# Apply the cell formats using the batch_format method
sheet.batch_format(cell_formats)