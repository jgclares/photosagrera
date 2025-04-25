import unicodedata
import processFilename
import urllib.parse




part= "Sa%CC%81nchez"
part2= processFilename.hidrive_decode(part)
print(list(part2))

for i, c in enumerate(list(part)):
    print(c)
    if not c.isalpha() and c != ' ':
        part = part[:i]
        break

print (part)


