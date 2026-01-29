# Copilot Instructions for Photo Contest Scoring System

## Project Overview
This is a photo contest workflow automation system for PhotosAgrera. It manages photo numbering, copying, and author matching across multiple photo contests (Social, Agustí Umbert) using HiDrive cloud storage and Google Sheets.

## Architecture

### Core Components
1. **HiDriveAPI Class**: Manages cloud file operations via OAuth2
   - Token refresh mechanism (5-minute buffer before expiry)
   - Methods: `list_files()`, `copy_file()`, `check_and_create_directory()`, `remove_directory()`
   - Located in: `numberSocialContest.py` and `numberAgustiContest.py`

2. **Google Sheets Integration**: Uses `gspread` library with service account credentials
   - Scores sheet (`puntuaciones_sheet_id`)
   - Participants sheet (`personas_sheet_id`)
   - Credentials: `credentials.json` (service account auth)
   - Formatting via `sheetFormat.py` module

3. **File Processing Pipeline**:
   - `copyphotos_and_number()`: Copy files from HiDrive, rename with sequential numbers (01, 02...)
   - `match_author_names()`: Fuzzy match filenames to author names using `SequenceMatcher`
   - `create_month_sheet()` / `format_month_sheet()`: Sheet setup and formatting

### Data Flow
```
HiDrive source folder 
  ? copyphotos_and_number() 
  ? numbered copies in destination folder 
  ? filename?author mapping
  ? Google Sheet update (NUM, NOMBRE, FICHERO JPG, TOTAL PUNTOS)
```

## Key Patterns & Conventions

### Contest Scripts
- **`numberSocialContest.py`**: Social contest (standard scoring)
- **`numberAgustiContest.py`**: Agustí Umbert contest (uses `processFilename.py` for name extraction)
- Both follow identical workflow but with different Google Sheet IDs and source directories

### Author Matching
- Uses `SequenceMatcher.ratio()` from `difflib` with `MINIMUM_SIMILARITY = 0.6` threshold
- Compares uppercase photo filenames against author names (columns C+D from `personas_worksheet`)
- Falls back to original filename if similarity < 0.6

### Unicode/Encoding Handling
- **HiDrive URLs**: Files are URL-encoded; always use `urllib.parse.unquote()` before processing
- **`processFilename.py`** utilities:
  - `hidrive_decode()`: URL decode + NFC normalization
  - `hidrive_encode()`: NFD decomposition + URL encode
  - Handles accented characters (e.g., "Sánchez" stored as "Sa%CC%81nchez")

### Command-Line Arguments
- Scripts accept folder name as CLI argument: `python numberSocialContest.py 05_GENER`
- Falls back to interactive `input()` if not provided

## Dependencies & Services

### External APIs
- **HiDrive API**: Cloud storage (OAuth2 with refresh tokens)
- **Google Sheets API**: Spreadsheet access (service account credentials)

### Python Packages
- `gspread`: Google Sheets client
- `gspread_formatting`: Sheet formatting (colors, alignment, fonts)
- `requests`: HTTP calls to HiDrive API
- `difflib`: String similarity matching
- `unicodedata`: Unicode normalization
- `urllib.parse`: URL encoding/decoding

### Credentials
- `credentials.json`: Google service account key
- HiDrive credentials hardcoded in scripts (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)

## Common Workflows

### Adding a New Contest
1. Duplicate `numberSocialContest.py` or `numberAgustiContest.py`
2. Update `puntuaciones_sheet_id` and `personas_sheet_id` with new Google Sheet IDs
3. Update `load_directory` and `destination_directory` HiDrive paths
4. Run: `python scriptname.py <folder_name>`

### Debugging File Matching
- Check `processFilename.py:SplitAndEdit()` for filename parsing rules
- Verify author list in Google Sheets (persons worksheet, columns C+D)
- Adjust `MINIMUM_SIMILARITY` threshold if matches are too strict/loose

### Sheet Formatting
- Headers: Black background, white text, 12pt bold, centered (see `sheetFormat.header_colors()`)
- Columns: A (50px - NUM), B (300px - NOMBRE), C (200px - FICHERO JPG), D (150px - TOTAL PUNTOS)
- Formula in D column: `=SI.ERROR(SUMA(INDIRECTO("E" & FILA()); INDIRECTO("F" & FILA()); INDIRECTO("G" & FILA()));"")` (sums columns E-G)

## Testing Notes
- `test.py`: Quick filename encoding/decoding tests for URL encoding/decoding behavior

## Error Recovery & Resilience

### Current Approach
- **Minimal error handling**: Uses `response.raise_for_status()` which throws exceptions on HTTP errors
- **No retry logic**: Failed API calls are not retried; exceptions propagate immediately
- **Transaction consistency**: Entire workflow fails if any single operation fails (no partial recovery)

### Suggested Improvements
1. **Add retry logic with exponential backoff** for HiDrive API calls (handle transient 429/503 errors):
   ```python
   def retry_with_backoff(func, max_retries=3, base_delay=1):
       for attempt in range(max_retries):
           try:
               return func()
           except requests.exceptions.RequestException as e:
               if attempt == max_retries - 1:
                   raise
               wait_time = base_delay * (2 ** attempt)
               print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
               time.sleep(wait_time)
   ```

2. **Add logging** with timestamps and operation context (use `logging` module)

3. **Consider partial success recovery**: Track which files copied successfully, allow resuming from checkpoint

4. **Validate Google Sheets operations** separately (catch gspread exceptions like `SpreadsheetNotFound`, `WorksheetNotFound`)

## Authentication Pattern (Current Implementation)

**Reuse existing approach:**
- Google Sheets: Service account key in `credentials.json` ? `google.oauth2.service_account.Credentials`
- HiDrive: OAuth2 refresh token ? `HiDriveAPI.refresh_access_token()` with 5-minute buffer
- **Token management**: Automatic refresh in `get_headers()` before expiry
- **No token storage**: Credentials loaded at module initialization (stateless per script run)

For new features, instantiate `HiDriveAPI` and use `gspread.authorize(credentials)` following the same pattern.

## Important Gotchas
- **Token expiry**: HiDrive tokens refresh automatically via `time.time() > self.token_expiry` check (5-minute buffer)
- **Rate limiting**: HiDrive API calls may throttle; consider adding delays in bulk operations (currently absent)
- **Case sensitivity**: File sorting uses uppercase (`x['name'].upper()`) for consistency
- **Directory cleanup**: `check_and_create_directory()` **removes existing destination** if present (destructive!)
- **No partial recovery**: If workflow fails mid-process, no state persisted to resume; entire operation must restart
