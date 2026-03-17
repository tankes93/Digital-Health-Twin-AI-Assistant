import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from rag.vector_store import PatientVectorStore

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def main():
    print("Initializing Vector Store...")
    vs = PatientVectorStore()
    
    print(f"Ingesting data from {DATA_DIR}...")
    vs.ingest_patient_data(DATA_DIR)
    
    print("Done!")

if __name__ == "__main__":
    main()
