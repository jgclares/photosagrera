import unicodedata
import urllib.parse
import processFilename

def is_alphabetic(char):
    # Normalize the character to decompose accented characters
    # NFD normalization separates the base character from its accent
    normalized = unicodedata.normalize('NFD', char)
    
    # Check if the base character is alphabetic
    # We take the first character since normalization may create multiple characters
    return normalized[0].isalpha()

def hidrive_decode(encoded_string):
    # First do standard URL decoding
    decoded = urllib.parse.unquote(encoded_string)
    # Then compose the unicode characters (NFC)
    return unicodedata.normalize('NFC', decoded)

def hidrive_encode(string):
    # First decompose the string (NFD)
    decomposed = unicodedata.normalize('NFD', string)
    # Then URL encode
    return urllib.parse.quote(decomposed)

def SplitAndEdit(filename: str):
    # Initialize return variables
    part1 = ""
    part2 = ""
    
    # Split by hyphen
    parts = filename.split(' - ', 1)
    
    def process_part(part: str):
        if not part:
            return ""
            
        # Replace underline with space
        part = part.replace('_', ' ')
        part = part.replace('-', ' ')
        part = part.replace('.', ' ')

        # Remove everything from first non-alphabetic char
    
        for i, c in enumerate(list(part)):
            print(c)
            if not c.isalpha and c != ' ':
                part = part[:i]
                break

        # Remove non-alphabetic chars
        #part = ''.join(char for char in part if is_alphabetic(char) or char == ' ')
        
        # Remove jpg/JPG
        part = part.replace('jpg', '').replace('JPG', '')
        
        # Trim spaces
        part = part.strip()
        
        # Check if it has at least two words
        if len(part.split()) < 2:
            return ""
            
        return part.upper()
    
    partsList =[]
    # Process first part
    part1 = process_part(parts[0])
    if len(part1) > 0:
        partsList.append(part1)
    
    # Process second part if it exists
    if len(parts) > 1:
        part2 = process_part(parts[1])
        if len(part2) > 0:
            partsList.append(part2)

    return partsList