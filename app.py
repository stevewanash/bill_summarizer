import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Import custom modules
import scraper
import pdf_utils
import llm_utils
import feedback_utils
import shutil
import platform

# Page Config
st.set_page_config(page_title="KeLegislate AI", layout="wide")


# --- Session State Management ---
if 'bills' not in st.session_state:
    st.session_state['bills'] = []
if 'current_bill_text' not in st.session_state:
    st.session_state['current_bill_text'] = ""
if 'current_summary' not in st.session_state:
    st.session_state['current_summary'] = ""

# --- Main Layout ---
st.title("🇰🇪 AI Legislative Summarizer & Citizen Voice")
st.markdown("Empowering Kenyan citizens with AI-driven bill analysis and feedback.")

# Tabs
tab1, tab2, tab3 = st.tabs(["📄 Select & Summarize", "🗳️ Give Feedback", "📊 Insights Dashboard"])

# ==========================================
# TAB 1: Bill Scraper & Summarizer
# ==========================================
with tab1:
    st.header("Find and Analyze Bills")
    
    if st.button("🔄 Refresh Bill List from Parliament.go.ke"):
        with st.spinner("Scraping Parliament website..."):
            st.session_state['bills'] = scraper.get_bills()
            if not st.session_state['bills']:
                st.error("Could not find bills. The website structure might have changed.")
            else:
                st.success(f"Found {len(st.session_state['bills'])} bills.")

    # Dropdown
    bill_options = {b['title']: b['url'] for b in st.session_state['bills']}
    selected_bill_title = st.selectbox("Select a Bill", options=list(bill_options.keys()) if bill_options else [])
    
    if selected_bill_title:
        st.caption(f"Source: {bill_options[selected_bill_title]}")
        
        if st.button("🚀 Generate AI Summary"):        
            url = bill_options[selected_bill_title]
            
            with st.status("Processing Bill...", expanded=True) as status:
                st.write("📥 Downloading PDF...")
                
                if st.button("Check Server Status"):
                    st.write(f"OS: {platform.system()}")
                    st.write(f"Tesseract Path: {shutil.which('tesseract')}")
                text = pdf_utils.download_and_extract_text(url)
                st.session_state['current_bill_text'] = text

                if "Error:" in text: # Check for the error string returned by pdf_utils
                    st.error("PDF Text Extraction Failed. Check the browser console for details.")
                    status.update(label="Failed to Extract Text", state="error", expanded=True)
                    st.stop() # Stop here if extraction failed!
                
                st.write("🤖 Analyzing with Gemini AI...")
                summary = llm_utils.summarize_bill(text)
                st.session_state['current_summary'] = summary
                
                status.update(label="Complete!", state="complete", expanded=False)

    # Display Result
    if st.session_state['current_summary']:
        st.divider()
        st.markdown(st.session_state['current_summary'])

# ==========================================
# TAB 2: Citizen Feedback Form
# ==========================================
with tab2:
    st.header("Citizen Feedback Form")
    
    if not selected_bill_title:
        st.warning("Please select a bill in Tab 1 first.")
    else:
        st.subheader(f"Feedback for: {selected_bill_title}")
        
        with st.form("feedback_form"):
            col1, col2 = st.columns(2)
            with col1:
                support = st.radio("Do you support this bill?", ["Yes", "No", "Not Sure"])
            with col2:
                rating = st.slider("Perceived Benefit (1-5)", 1, 5, 3)
            
            concerns = st.text_area("What are your concerns or suggestions?")
            
            submitted = st.form_submit_button("Submit Feedback")
            
            if submitted:
                with st.spinner("Saving to database..."):
                    success = feedback_utils.save_feedback(selected_bill_title, support, rating, concerns)
                    if success:
                        st.success("Thank you! Your voice has been recorded.")
                    else:
                        st.error("Failed to save. Check Firebase configuration.")

# ==========================================
# TAB 3: Insights Dashboard
# ==========================================
with tab3:
    st.header("Public Sentiment Dashboard")
    
    # Load Data
    if not selected_bill_title:
        st.info("Select a bill in Tab 1 to see specific insights, or view global stats below.")
        feedback_data = feedback_utils.fetch_feedback() # Fetch all
    else:
        st.subheader(f"Data for: {selected_bill_title}")
        feedback_data = feedback_utils.fetch_feedback(selected_bill_title)
    
    if not feedback_data:
        st.write("No feedback data available yet.")
    else:
        df = pd.DataFrame(feedback_data)
        
        # 1. Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Responses", len(df))
        col2.metric("Avg. Benefit Rating", f"{df['rating'].mean():.2f}/5")
        
        # Calculate Support %
        if not df.empty and 'support' in df.columns:
            support_pct = (df['support'] == 'Yes').mean() * 100
            col3.metric("Support Level", f"{support_pct:.1f}%")

        st.divider()

        # 2. Charts
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Support Distribution")
            fig_pie = px.pie(df, names='support', title='Support vs Opposition', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Rating Distribution")
            fig_bar = px.bar(df['rating'].value_counts().reset_index(), x='rating', y='count', labels={'rating': 'Rating (1-5)'})
            st.plotly_chart(fig_bar, use_container_width=True)

        # 3. Word Cloud
        st.subheader("Common Concerns (Word Cloud)")
        text_concerns = " ".join(df['concerns'].dropna().tolist())
        if text_concerns:
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text_concerns)
            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

        # 4. AI Insights
        st.divider()
        st.subheader("🤖 AI-Generated Policy Insights")
        
        if st.button("Generate AI Insights Report"):
            # Prepare a string summary of data for the LLM
            data_summary = f"Total feedback count: {len(df)}\n"
            data_summary += f"Support counts: {df['support'].value_counts().to_dict()}\n"
            data_summary += f"Sample citizen comments: {text_concerns[:4000]}" # Truncate for context limit
            
            with st.spinner("Analyzing feedback patterns..."):
                insight_report = llm_utils.generate_insights(data_summary)
                st.markdown(insight_report)