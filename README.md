# Digital Health Twin AI Assistant

A complete RAG-based AI system that analyzes patient Digital Health Twins and provides actionable health insights via a FastAPI backend and Streamlit frontend.

## Key Features

*   **RAG Pipeline**: Retrieves specific patient context (medications, history, vitals) to answer queries grounded in data.
*   **Smart Context Injection**: "General" mode automatically aggregates system-wide patient statistics for high-level queries.
*   **Health Intelligence**: Automatically flags anomalies like High BP, Tachycardia, or Low Sleep using deterministic rules combined with LLM reasoning.
*   **Cloud-Powered**: Uses Groq API with LLaMA 3.3-70b-versatile for ultra-fast inference.
*   **Explainable**: Every insight cites the specific data points used.

## Project Structure

```
/project
├── data/                   # Simulated Patient JSON profiles
├── rag/
│   ├── vector_store.py     # Handles Embedding (HuggingFace) & ChromaDB
│   └── chain.py            # LangChain Pipeline with Groq API
├── utils/
│   ├── analytics.py        # Logic for health anomaly detection
│   ├── gen_data.py         # Script to create synthetic patients
│   └── ingest.py           # Script to vectorize patient data
├── main.py                 # FastAPI Application Entry Point
├── app.py                  # Streamlit Frontend
├── requirements.txt        # Python Dependencies
├── .env                    # API Keys (Groq)
└── README.md               # Documentation
```

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- A [Groq API Key](https://console.groq.com/keys)

### 2. Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (ensure pip is upgraded)
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory and add your Groq API Key:
```bash
GROQ_API_KEY=gsk_your_actual_api_key_here
```

### 4. Initialize Data & Vector Database
Generate synthetic patients and ingest them into the vector store (ChromaDB).
```bash
# 1. Generate Synthetic Data
python utils/gen_data.py

# 2. Build Vector Index
python utils/ingest.py
```

### 5. Run the Application

**Option A: Run Frontend & Backend Separately (Recommended for Dev)**

Terminal 1 (Backend API):
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.

Terminal 2 (Frontend UI):
```bash
streamlit run app.py
```
The UI will open at `http://localhost:8501`.

## System Architecture

### 1. Data Layer
Patient data is stored as structured JSON files. During ingestion, each file is processed into semantic chunks (e.g., "Medical History", "Vitals Summary") and embedded using `all-MiniLM-L6-v2`.

### 2. Retrieval (RAG)
When a user asks a question:
1.  **Patient Specific**: The system searches ChromaDB for the top pieces of information relevant to that specific patient.
2.  **General Mode**: The system injects a global "System Overview" document into the context, allowing the AI to answer questions about the entire patient population (e.g., "How many patients?").

### 3. Reasoning Engine
The system uses the **Groq API** (running LLaMA 3.3-70b) to generate insights. It combines:
- Retrieved clinical context.
- Deterministic anomaly detection rules (e.g., "HR > 100").
- AI reasoning to explain *why* a specific insight was generated.

## API Usage Example

**Endpoint**: `POST /ask`

**Request Body**:
```json
{
  "patient_id": "patient_04",
  "user_question": "Is the patient at risk of diabetes?"
}
```
