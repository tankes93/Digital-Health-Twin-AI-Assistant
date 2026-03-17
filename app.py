import streamlit as st
import requests
import json
import os

# Configuration
API_URL = "http://localhost:8000/ask"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

st.set_page_config(
    page_title="Digital Health Twin AI",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    /* Reduce metric label size */
    div[data-testid="stMetricLabel"] > label {
        font-size: 14px;
        white-space: nowrap;
    }
    /* Adjust value size and ensure it wraps/shrinks if needed */
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
        white-space: normal;
        word-wrap: break-word;
        line-height: 1.2;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to get list of patients
def get_patient_ids():
    ids = ["General"]
    if os.path.exists(DATA_DIR):
        files = [f.replace('.json', '') for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        ids.extend(sorted(files))
    return ids

# Sidebar
with st.sidebar:
    # Try to find a local logo file (png, jpg, jpeg)
    logo_path = None
    for ext in ["png", "jpg", "jpeg"]:
        potential_path = os.path.join(os.path.dirname(__file__), f"logo.{ext}")
        if os.path.exists(potential_path):
            logo_path = potential_path
            break
            
    if logo_path:
        st.image(logo_path, width=200)
    else:
        st.image("https://img.icons8.com/color/96/000000/health-graph.png", width=80)

    st.title("Digital Health Twin")
    st.markdown("---")
    
    patient_ids = get_patient_ids()
    if patient_ids:
        selected_patient = st.selectbox("Select Patient ID", patient_ids)
    else:
        st.error("No patient data found in /data")
        selected_patient = None
        
    st.markdown("---")
    st.markdown("### System Status")
    try:
        if requests.get("http://localhost:8000/").status_code == 200:
            st.success("API Connected")
        else:
            st.error("API Error")
    except:
        st.error("API Offline")
        st.info("Run: `uvicorn main:app --reload`")

# Main Content
if selected_patient:
    st.title(f"Patient Dashboard: {selected_patient}")
    
    if selected_patient != "General":
        # Load raw patient data for display
        try:
            with open(os.path.join(DATA_DIR, f"{selected_patient}.json"), 'r') as f:
                patient_data = json.load(f)
                
            # Top Metrics Row
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Patient Name", patient_data.get('name', 'Unknown'))
            with col2:
                st.metric("Age", f"{patient_data.get('age')} years")
            with col3:
                st.metric("Heart Rate", f"{patient_data.get('heart_rate')} bpm")
            with col4:
                st.metric("Blood Pressure", patient_data.get('blood_pressure'))
            with col5:
                st.metric("Stress Level", patient_data.get('stress_level'))
        except Exception as e:
            st.error(f"Error loading patient data: {e}")
    else:
        st.info("You are in General Mode. Ask questions about the entire patient cohort or general health queries.")

    # Chat Interface
    st.markdown("---")
    st.subheader("AI Health Assistant")
    
    # Initialize chat history FOR THIS SPECIFIC PATIENT
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
        
    if selected_patient not in st.session_state.chat_sessions:
        st.session_state.chat_sessions[selected_patient] = []

    # Display chat messages from history on app rerun
    for message in st.session_state.chat_sessions[selected_patient]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask about this patient's health..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.chat_sessions[selected_patient].append({"role": "user", "content": prompt})

        # Call API
        with st.spinner("Analyzing Digital Twin..."):
            try:
                payload = {
                    "patient_id": selected_patient,
                    "user_question": prompt
                }
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    insight = data.get("health_insight")
                    anomalies = data.get("anomaly_flags", [])
                    
                    # Format response
                    full_response = insight
                    if anomalies:
                        full_response += "\n\n**🚨 Anomalies Detected:**\n" + "\n".join([f"- {a}" for a in anomalies])
                        
                    # Display assistant response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(full_response)
                        with st.expander("View Reason & Context"):
                            st.write("**Reasoning:**", data.get("reasoning"))
                            st.write("**Source Data:**")
                            for doc in data.get("retrieved_context", []):
                                st.info(doc)
                                
                    # Add assistant response to chat history
                    st.session_state.chat_sessions[selected_patient].append({"role": "assistant", "content": full_response})
                else:
                    error_msg = f"Error: {response.text}"
                    st.error(error_msg)
                    st.session_state.chat_sessions[selected_patient].append({"role": "assistant", "content": error_msg})
            except Exception as e:
                st.error(f"Connection failed: {e}")

else:
    st.info("Please select a patient to view their Digital Twin.")
