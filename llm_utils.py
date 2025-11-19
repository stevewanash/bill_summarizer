import google.generativeai as genai
import os
import streamlit as st
from google.api_core import exceptions as g_exceptions

@st.cache_data(ttl='90d', max_entries=50, show_spinner=False)
def summarize_bill(bill_text):
    """
    Sends bill text to Gemini for summarization and extraction.
    """
    try:
        # 1. Retrieve the API key securely from Streamlit Secrets
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        # Fallback error if the secret isn't configured in the environment
        return "Error: GEMINI_API_KEY not found in Streamlit secrets."
    
    if not bill_text or len(bill_text) < 100:
        return "Error: Bill text was empty or unreadable."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite') # Flash is faster/cheaper for large context

    prompt = f"""
    You are an expert policy analyst. Summarize the following Kenyan legislative bill text into simple English and simple Swahili.
    Avoid complex legal jargon.

    Structure the output exactly as follows:
    
    ## Simple English Summary
    [Write summary here]

    ## 1. Key Implications for Citizens
    * [Point 1]
    * [Point 2]

    ## 2. Key Implications for Businesses/Government
    * [Point 1]
    * [Point 2]

    ---

    ## Muhtasari (Simple Swahili Summary, use the same content from the english section)
    [Toa muhtasari rahisi, usiotumia lugha ya kisheria.]

    ## 1. Athari kwa Wananchi (Key Implications for Citizens - Swahili)
    * [Athari 1]
    * [Athari 2]
    
    ## 2. Athari kwa Biashara/Serikali (Key Implications for Businesses/Government - Swahili)
    * [Athari 1]
    * [Athari 2]

    ---

    Bill Text:
    {bill_text[:30000]} 
    """ 
    # Note: truncated text to 30k chars to be safe, though 1.5 Flash handles much more.

    try:
        response = model.generate_content(prompt)
        return response.text
    except g_exceptions.ResourceExhausted:
        return (
            "**AI Service Temporarily Unavailable**\n\n"
            "We've hit the daily usage limit (quota) for the AI service. "
            "Please try again later or tomorrow. This ensures the service remains free to use!"
        )
    except Exception as e:
        return f"Unexpected AI Error:** A technical issue occurred. Details: {e}"

@st.cache_data(ttl='1h', max_entries=10, show_spinner=False)
def generate_insights(feedback_text):
    """
    Analyzes aggregated citizen feedback.
    """
    try:
        # 1. Retrieve the API key securely from Streamlit Secrets
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        # Fallback error if the secret isn't configured in the environment
        return "Error: GEMINI_API_KEY not found in Streamlit secrets."    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    prompt = f"""
    Analyze the following citizen feedback regarding a legislative bill:
    {feedback_text}

    Produce:
    1. Overall sentiment analysis (approximate % support vs opposition).
    2. Top 5 specific citizen concerns.
    3. Suggested improvements for policymakers based on this data.
    4. A 3-5 bullet executive summary for decision-makers.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Analysis Error: {e}"