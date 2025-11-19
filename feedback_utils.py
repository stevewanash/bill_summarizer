import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from datetime import datetime

def get_db():
    """
    Initializes Firebase safely (prevents double init error).
    """
    if not firebase_admin._apps:
        try:
            # Assumes firebase_key.json is in the root folder
            key_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
            cred = credentials.Certificate(key_json)
            firebase_admin.initialize_app(cred)
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