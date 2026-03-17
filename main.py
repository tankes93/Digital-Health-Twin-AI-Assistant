from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import json

# Import custom modules
from rag.vector_store import PatientVectorStore
from rag.chain import RAGChain
from utils.analytics import HealthAnalytics

# Initialize App
app = FastAPI(
    title="Digital Health Twin AI Assistant",
    description="RAG-based API for analyzing patient health records.",
    version="1.0.0"
)

from langchain_core.documents import Document

# Initialize Components (Lazy loading recommended for production, but eager for now)
print("Loading Vector Store...")
vector_store = PatientVectorStore()  # Connects to ChromaDB

print("Loading RAG Chain...")
rag_chain = RAGChain() # Connects to Ollama

# Add path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def get_general_context() -> Document:
    """
    Constructs a global summary document containing metadata for all patients.
    This helps the 'General' mode answer questions about total patient count, names, etc.
    """
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
                gender = data.get("gender", "N/A")
                conditions = [c.get("condition") for c in data.get("medical_history", [])]
                patient_summaries.append(f"- {p_id}: {name} ({age}y, {gender}) - Conditions: {', '.join(conditions)}")
        except Exception:
            continue
            
    summary_text = (
        f"SYSTEM OVERVIEW:\n"
        f"Total Patients in Database: {total_patients}\n"
        f"List of All Patients:\n" + "\n".join(patient_summaries)
    )
    
    return Document(page_content=summary_text, metadata={"type": "system_overview"})

# Pydantic Models
class QueryRequest(BaseModel):
    patient_id: str = "patient_05"
    user_question: str = "Is the patient at risk of diabetes?"

class InsightResponse(BaseModel):
    patient_id: str
    patient_data_summary: Dict[str, Any]
    retrieved_context: List[str]
    health_insight: str
    anomaly_flags: List[str]
    reasoning: str

@app.get("/")
async def root():
    return {"message": "Digital Health Twin API is running."}

@app.post("/ask", response_model=InsightResponse)
async def ask_health_assistant(request: QueryRequest):
    patient_id = request.patient_id
    question = request.user_question
    
    # 1. Fetch Raw Patient Data (for analysis)
    patient_data = {}
    if patient_id == "General":
        patient_data = {
            "name": "General Population",
            "age": "N/A",
            "medical_history": [],
            "medications": []
        }
    else:
        patient_file = os.path.join(DATA_DIR, f"{patient_id}.json")
        if not os.path.exists(patient_file):
            raise HTTPException(status_code=404, detail=f"Patient ID {patient_id} not found.")
        
        with open(patient_file, 'r') as f:
            patient_data = json.load(f)

    # 2. Retrieve Context (RAG)
    # Get relevant chunks from vector store
    # If General, k is increased to get broader context
    k_val = 6 if patient_id == "General" else 4
    retrieved_docs = vector_store.retrieve_context(patient_id, question, k=k_val)
    
    # [FIX] For 'General' mode, inject the global overview doc to handle counting/listing questions
    if patient_id == "General":
        global_doc = get_general_context()
        # Prepend so it has high visibility in context window
        retrieved_docs.insert(0, global_doc)

    context_text_list = [d.page_content for d in retrieved_docs]

    # 3. Generate LLM Response
    rag_response = rag_chain.generate_response(retrieved_docs, question)
    raw_llm_output = rag_response["answer"]
    
    # Parse Structured Output (Health Insight vs. Reasoning)
    health_insight = raw_llm_output
    reasoning_text = "Derived from patient context."
    
    if "Reasoning:" in raw_llm_output:
        parts = raw_llm_output.split("Reasoning:")
        health_insight = parts[0].replace("Health Insight:", "").strip()
        reasoning_text = parts[1].strip()
    
    # 4. Run Anomaly Detection (Deterministic) - Skip for General
    anomalies = []
    if patient_id != "General":
        anomalies = HealthAnalytics.check_anomalies(patient_data)
    
    # 5. Build Dynamic Reasoning
    # Combine LLM reasoning with deterministic anomaly flags for full explainability
    final_reasoning = reasoning_text
    if anomalies:
        # Safer split in case colon is missing
        flags = [a.split(':')[0] if ':' in a else a for a in anomalies]
        final_reasoning += f"\n\n[System Alert] The following anomalies were independently detected: {', '.join(flags)}."
    
    # 6. Construct Response
    return InsightResponse(
        patient_id=patient_id,
        patient_data_summary={
            "age": patient_data.get("age"),
            "diagnosis": [c["condition"] for c in patient_data.get("medical_history", [])],
            "medications": [m["name"] for m in patient_data.get("medications", [])]
        },
        retrieved_context=context_text_list,
        health_insight=health_insight,
        anomaly_flags=anomalies,
        reasoning=final_reasoning
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
