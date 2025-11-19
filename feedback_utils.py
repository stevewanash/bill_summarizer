import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from datetime import datetime
import json

def get_db():
    """
    Initializes Firebase safely (prevents double init error).
    """
    if not firebase_admin._apps:
        try:
            # Assumes firebase_key.json is in the root folder
            json_string = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
            
            # 2. CRITICAL STEP: Convert the JSON string into a Python dictionary
            # json.loads() is what you need to parse the text into an object.
            key_dict = json.loads(json_string)
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        except KeyError:
            st.error("Firebase Init Error: Secret FIREBASE_SERVICE_ACCOUNT not found. Please check .streamlit/secrets.toml or Streamlit Cloud Secrets.")
            return None
        except Exception as e:
            st.error(f"Firebase Init Error: {e}")
            return None
    return firestore.client(database_id='legislation')

def save_feedback(bill_title, support, rating, concerns):
    db = get_db()
    if db:
        data = {
            "bill_title": bill_title,
            "support": support,
            "rating": int(rating),
            "concerns": concerns,
            "timestamp": datetime.now()
        }
        db.collection("bill_feedback").add(data)
        return True
    return False

def fetch_feedback(bill_title=None):
    db = get_db()
    if not db:
        return []
    
    collection = db.collection("bill_feedback")
    
    if bill_title:
        # Filter by specific bill
        docs = collection.where("bill_title", "==", bill_title).stream()
    else:
        docs = collection.stream()
        
    return [doc.to_dict() for doc in docs]