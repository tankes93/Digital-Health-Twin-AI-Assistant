import streamlit as st
import json
import os
import time

# --- STANDALONE MODE IMPORT ---
# This allows the app to run on Streamlit Cloud without a separate URL
try:
    from rag.vector_store import PatientVectorStore
    from rag.chain import RAGChain
    from utils.analytics import HealthAnalytics
    from langchain_core.documents import Document
    STANDALONE_MODE = True
except ImportError:
    STANDALONE_MODE = False

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

st.set_page_config(
    page_title="Digital Health Twin AI",
    page_icon="🏥",
    layout="wide"
)

# --- SYSTEM INITIALIZATION (CACHE) ---
@st.cache_resource
def initialize_system():
    """
    Initializes the RAG components and ingests data if needed.
    This runs once on startup.
    """
    if not STANDALONE_MODE:
        return None, None
        
    # 1. Initialize Vector Store
    vs = PatientVectorStore()
    
    # Check if we need to ingest data (if vector store is empty or needs refresh)
    # Simple check: if collection count is 0, ingest.
    try:
        if vs.vector_db._collection.count() == 0:
            st.toast("Ingesting patient data...", icon="⚙️")
            vs.ingest_patient_data(DATA_DIR)
    except:
        # Fallback if specific collection check fails
        pass

    # 2. Initialize RAG Chain
    # Ensure API Key is available
    if not os.environ.get("GROQ_API_KEY"):
        # Check Streamlit secrets
        if "GROQ_API_KEY" in st.secrets:
            os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
            
    chain = RAGChain()
    return vs, chain

# Helper: General Context for Standalone Mode
def get_general_context() -> Document:
    if not os.path.exists(DATA_DIR):
        return Document(page_content="No patient data directory found.")
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    total_patients = len(files)
    patient_summaries = []
    
    for filename in sorted(files):
        try:
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                data = json.load(f)
                p_id = data.get("patient_id", filename.replace(".json", ""))
                name = data.get("name", "Unknown")
                age = data.get("age", "N/A")
                conditions = [c.get("condition") for c in data.get("medical_history", [])]
                patient_summaries.append(f"- {p_id}: {name} ({age}y) - Conditions: {', '.join(conditions)}")
        except Exception:
            continue
            
    summary_text = (
        f"SYSTEM OVERVIEW:\n"
        f"Total Patients in Database: {total_patients}\n"
        f"List of All Patients:\n" + "\n".join(patient_summaries)
    )
    return Document(page_content=summary_text, metadata={"type": "system_overview"})


# Initialize
if STANDALONE_MODE:
    vector_store, rag_chain = initialize_system()

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
    
    # Only show system status in API mode
    if not STANDALONE_MODE:
        st.markdown("### System Status")
        try:
            import requests # Lazy import for non-standalone
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
        p_path = os.path.join(DATA_DIR, f"{selected_patient}.json")
        if os.path.exists(p_path):
            with open(p_path, 'r') as f:
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
        else:
            st.error("Patient data not found locally.")
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
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        if selected_patient not in st.session_state.chat_sessions:
            st.session_state.chat_sessions[selected_patient] = []
        st.session_state.chat_sessions[selected_patient].append({"role": "user", "content": prompt})

        # --- LOGIC SELECTION: STANDALONE VS API ---
        
        response_data = {}
        error_message = None

        with st.spinner("Analyzing Digital Twin..."):
            if STANDALONE_MODE:
                # RUN LOGIC DIRECTLY (For Streamlit Cloud Deployment)
                try:
                    # 1. Retrieve Context
                    k_val = 6 if selected_patient == "General" else 4
                    retrieved_docs = vector_store.retrieve_context(selected_patient, prompt, k=k_val)
                    
                    if selected_patient == "General":
                         # Inject global context
                         global_doc = get_general_context()
                         retrieved_docs.insert(0, global_doc)

                    # 2. Generate LLM Response
                    rag_response = rag_chain.generate_response(retrieved_docs, prompt)
                    raw_output = rag_response["answer"]
                    
                    # 3. Parse Output
                    health_insight = raw_output
                    reasoning_text = "Derived from patient context."
                    if "Reasoning:" in raw_output:
                        parts = raw_output.split("Reasoning:")
                        health_insight = parts[0].replace("Health Insight:", "").strip()
                        reasoning_text = parts[1].strip()
                        
                    # 4. Anomaly Check
                    anomalies = []
                    if selected_patient != "General":
                         # Need raw patient data
                         p_file = os.path.join(DATA_DIR, f"{selected_patient}.json")
                         if os.path.exists(p_file):
                             with open(p_file, 'r') as f:
                                 p_data = json.load(f)
                             anomalies = HealthAnalytics.check_anomalies(p_data)

                    # Form response object similar to API
                    response_data = {
                        "health_insight": health_insight,
                        "anomaly_flags": anomalies,
                        "reasoning": reasoning_text,
                        "retrieved_context": [d.page_content for d in retrieved_docs]
                    }
                    
                except Exception as e:
                    error_message = f"Internal Logic Error: {str(e)}"
                    import traceback
                    print(traceback.format_exc())
                    
            else:
                # CALL API (Local Dev Mode)
                import requests
                API_URL = "http://localhost:8000/ask"
                response = requests.post(API_URL, json={
                    "patient_id": selected_patient,
                    "user_question": prompt
                })
                
                if response.status_code == 200:
                    response_data = response.json()
                else:
                    error_message = f"API Error: {response.text}"


            # --- DISPLAY RESPONSE ---
            if not error_message:
                insight = response_data.get("health_insight", "No insight generated.")
                anomalies = response_data.get("anomaly_flags", [])
                
                # Format response
                full_response = insight
                if anomalies:
                    full_response += "\n\n**🚨 Anomalies Detected:**\n" + "\n".join([f"- {a}" for a in anomalies])
                    
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(full_response)
                    with st.expander("View Reason & Context"):
                        st.write("**Reasoning:**")
                        st.write(response_data.get("reasoning", "N/A"))
                        st.write("**Source Data:**")
                        for doc in response_data.get("retrieved_context", []):
                            st.info(doc)
                            
                # Add to history
                st.session_state.chat_sessions[selected_patient].append({"role": "assistant", "content": full_response})
            else:
                st.error(error_message)
                st.session_state.chat_sessions[selected_patient].append({"role": "assistant", "content": error_message})

else:
    st.info("Please select a patient to view their Digital Twin.")
