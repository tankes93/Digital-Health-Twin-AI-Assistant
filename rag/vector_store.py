import os
import json
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Persistence path for the vector DB
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

class PatientVectorStore:
    def __init__(self):
        # Initialize embeddings - using a lightweight local model
        self.embedding_function = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize Vector DB
        self.vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=self.embedding_function
        )

    def ingest_patient_data(self, data_dir: str):
        """
        Reads all JSON files from data_dir and ingests them into ChromaDB.
        """
        documents = []
        
        if not os.path.exists(data_dir):
            print(f"Data directory {data_dir} does not exist.")
            return

        files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        
        print(f"Found {len(files)} patient files to ingest...")
        
        for filename in files:
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r') as f:
                patient_data = json.load(f)
                
            patient_id = patient_data.get("patient_id", "UNKNOWN")
            
            # semantic chunking strategy
            # 1. Demographics & Vitals Summary
            summary_text = (
                f"Patient {patient_id} Profile:\n"
                f"Name: {patient_data.get('name')}\n"
                f"Age: {patient_data.get('age')}, Gender: {patient_data.get('gender')}\n"
                f"BMI: {patient_data.get('bmi')}, Status: {patient_data.get('stress_level')} Stress\n"
                f"Current Vitals: HR {patient_data.get('heart_rate')} bpm, "
                f"BP {patient_data.get('blood_pressure')}, "
                f"Sleep {patient_data.get('sleep_hours')} hrs, "
                f"Steps {patient_data.get('daily_steps')}"
            )
            documents.append(Document(
                page_content=summary_text,
                metadata={"patient_id": patient_id, "name": patient_data.get('name'), "type": "summary"}
            ))
            
            # 2. Medical History
            for condition in patient_data.get("medical_history", []):
                hist_text = (
                    f"Patient {patient_id} ({patient_data.get('name')}) Medical History: "
                    f"Diagnosed with {condition.get('condition')} on {condition.get('diagnosed_date', 'unknown date')}. "
                    f"Status: {condition.get('status')}."
                )
                documents.append(Document(
                    page_content=hist_text,
                    metadata={"patient_id": patient_id, "name": patient_data.get('name'), "type": "history"}
                ))
                
            # 3. Medications
            for med in patient_data.get("medications", []):
                med_text = (
                    f"Patient {patient_id} ({patient_data.get('name')}) Medication: "
                    f"Takes {med.get('name')} {med.get('dosage')} with frequency {med.get('frequency')}."
                )
                documents.append(Document(
                    page_content=med_text,
                    metadata={"patient_id": patient_id, "name": patient_data.get('name'), "type": "medication"}
                ))
                
            # 4. Doctor Notes
            if patient_data.get("doctor_notes"):
                note_text = f"Patient {patient_id} ({patient_data.get('name')}) Doctor Notes: {patient_data.get('doctor_notes')}"
                documents.append(Document(
                    page_content=note_text,
                    metadata={"patient_id": patient_id, "name": patient_data.get('name'), "type": "notes"}
                ))

        if documents:
            # Add to Chroma
            print(f"Adding {len(documents)} document chunks to Vector DB...")
            self.vector_db.add_documents(documents)
            # self.vector_db.persist() # Chroma 0.4+ persists automatically or via specific calls depending on config, but usually auto.
            print("Ingestion complete.")
        else:
            print("No documents created.")

    def retrieve_context(self, patient_id: str, query: str, k: int = 4) -> List[Document]:
        """
        Retrieves context relevant to the query for a specific patient.
        If patient_id is "General", retrieves from all patients.
        """
        search_kwargs = {"k": k}
        if patient_id != "General":
            search_kwargs["filter"] = {"patient_id": patient_id}
            
        return self.vector_db.similarity_search(query, **search_kwargs)
