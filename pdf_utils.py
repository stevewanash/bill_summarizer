import requests
import io
import streamlit as st
from PIL import Image
import pytesseract
import pdfplumber

# --- CONFIGURATION (Crucial for Windows users) ---
# If you are on Windows, you MUST specify the path to your tesseract executable.
# Example: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# If on macOS/Linux and installed via brew/apt, this line can often be omitted.
# If you run into errors, uncomment and update the line below:
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 

def pdf_page_to_image(page, scale=300):
    """
    Renders a pdfplumber page object to a PIL Image using .to_image().
    
    Checks for the .original attribute which holds the PIL Image object.
    If the .original attribute is missing, it falls back to the .to_to_image() result.
    """
    # 1. Render the page to a PageImage object
    img_wrapper = page.to_image(resolution=scale)
    
    # 2. Extract the underlying PIL Image object:
    # In older pdfplumber versions, it was img_wrapper.original.
    # In newer versions, the object returned by .to_image() is often the PIL Image itself,
    # or the PIL Image is available via .original.
    
    try:
        # Try the common attribute that holds the PIL Image
        # This is where your old code failed: img.original_size
        # The correct attribute is usually just .original
        return img_wrapper.original 
    except AttributeError:
        # If .original isn't available, return the wrapper object itself, 
        # as newer versions might have merged the functionality.
        return img_wrapper 
    
    # NOTE: If this fails, we will resort to a different library (PyMuPDF/fitz)
    # in the next troubleshooting step, but try this fix first.

@st.cache_data(ttl="180d", max_entries=40)
def download_and_extract_text(url, max_pages=50):
    """
    Downloads PDF and extracts text, prioritizing OCR if initial extraction fails.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/pdf',
    }
    extracted_text = ""
    
    try:
        response = requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' not in content_type:
             return f"Error: Content received was not PDF ({content_type})."

        pdf_stream = io.BytesIO(response.content)

        with pdfplumber.open(pdf_stream) as pdf:
            pages_to_read = min(len(pdf.pages), max_pages)

            with st.spinner(f"Running OCR on {pages_to_read} pages..."):
                for i in range(pages_to_read):
                    page = pdf.pages[i]
                    
                    # 1. Attempt basic extraction first (fastest method)
                    page_text = page.extract_text()
                    
                    if page_text and len(page_text.strip()) > 50:
                        # Success: Use the fast text
                        extracted_text += page_text.strip() + "\n"
                        st.caption(f"Page {i+1} extracted digitally.")
                    else:
                        # 2. Failure: Run OCR on the page image (slow, but works on scans)
                        try:
                            # Render page to PIL image
                            page_img = pdf_page_to_image(page)
                            
                            # Use Tesseract to read text from the image
                            ocr_text = pytesseract.image_to_string(page_img)
                            
                            if ocr_text:
                                extracted_text += ocr_text.strip() + "\n"
                                st.caption(f"Page {i+1} extracted via OCR.")
                            else:
                                st.caption(f"Page {i+1} skipped (OCR failed).")
                        except Exception as ocr_e:
                            st.caption(f"Page {i+1} OCR failed: {ocr_e}")

        if not extracted_text:
            return "Error: Downloaded PDF, but neither digital extraction nor OCR found text."

        return extracted_text.strip()

    except requests.exceptions.HTTPError as e:
        return f"🚨 HTTP Error during download: {e}"
    except Exception as e:
        return f"🚨 Critical PDF Processing Error: {e}"