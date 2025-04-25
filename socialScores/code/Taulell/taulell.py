from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import sys
 # 510806
base_url = "https://tauler.seu.cat/pagDetall.do?idEdicte="
start_id = 492001 
end_id = 500000
search_text = "ACC/3662/2021"
notfound_text = "Ho sentim,"
h3_search_text = "Programa 4"
log_file = r"c:\temp\matches.log"

for id_edicte in range(start_id, end_id + 1):
    url = f"{base_url}{id_edicte}&idens=1"
    
    try:
        current_time =datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Trying to match found for idEdicte: {id_edicte}")
        response = requests.get(url)
        response.raise_for_status()         
        
        if search_text in response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
                        
            with open(log_file, 'a', encoding='utf-8') as f:   
                print(f"[{current_time}] Match found for idEdicte: {id_edicte}")
                f.write(f"[{current_time}] Match found for idEdicte: {id_edicte} \n")
                h3_element = soup.select_one('div.box_mid_header.detall h3')
                if h3_element:
                    h3_text = h3_element.get_text(strip=True)
                    f.write(f"H3 Text: {h3_text}\n\n")
                
                    if h3_search_text in h3_text:
                        print(f"URL: {url}")
                        print(f"H3 Text: {h3_text}")
                        print("Program 4 Found, execution finalized.")
                        sys.exit(0)  # Exit the program

                else:
                     f.write(f"Not found: div.box_mid_header.detall h3 can't look for Programa 4 :\n\n")        
        else:
            if notfound_text in response.text:
                print(f"[{current_time}] Not Found idEdicte: {id_edicte} \n") 
            else:
                with open(log_file, 'a', encoding='utf-8') as f:   
                    print(f"[{current_time}] Found other topic for idEdicte: {id_edicte} \n") 
                    f.write(f"[{current_time}] Found other topic for idEdicte: {id_edicte} \n") 

        time.sleep(5)  # Add a delay to avoid overwhelming the server
    
    except requests.RequestException as e:
        print(f"Error occurred while processing idEdicte {id_edicte}: {e}")

print("Processing completed without finding a match for 'Programa 4'.")