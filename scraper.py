import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import streamlit as st

BASE_URL = "https://www.parliament.go.ke"

@st.cache_data(ttl="7d")
def get_bills():
    """
    Scrapes the Kenyan Parliament website for bills.
    Returns a list of dicts: {'title': str, 'url': str}
    """
    url = "https://www.parliament.go.ke/the-national-assembly/house-business/bills"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        bills = []
        
        # The website structure often puts bills in tables or lists.
        # We look for anchor tags linking to PDF files.
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if href.lower().endswith('.pdf') or 'sites/default/files' in href:
                # Ensure full URL
                #if not href.startswith('http'):
                    #full_url = f"https://www.parliament.go.ke{href}" if href.startswith('/') else href
                #else:
                full_url = urljoin(BASE_URL, href)
                
                # specific cleanup for this site might be needed, but generic approach:
                if len(text) > 5 and 'BILL' in text.upper(): # Filter out 'Download' or empty links
                    bills.append({'title': text, 'url': full_url})
        
        # Deduplicate based on URL
        unique_bills = {v['url']: v for v in bills}.values()
        return list(unique_bills)

    except Exception as e:
        print(f"Scraping Error: {e}")
        return []