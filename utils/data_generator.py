import json
import random
from faker import Faker
import os
from datetime import datetime, timedelta

fake = Faker()

# Configuration
NUM_PATIENTS = 10
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def generate_patient_data(patient_id):
    gender = random.choice(["Male", "Female"])
    age = random.randint(25, 85)
    
    # Generate somewhat realistic correlated data
    bmi = round(random.uniform(18.5, 35.0), 1)
    
    # Heart rate logic based on age/health
    resting_hr = random.randint(55, 95)
    if bmi > 30: resting_hr += random.randint(5, 15)
        
    # BP logic
    systolic = random.randint(110, 160)
    diastolic = random.randint(70, 100)
    bp_str = f"{systolic}/{diastolic}"
    
    # Steps & Sleep
    steps = random.randint(2000, 12000)
    sleep = round(random.uniform(4.0, 9.0), 1)
    
    stress_level = random.choice(["Low", "Moderate", "High"])
    
    # Conditions
    conditions = []
    if systolic > 130 or diastolic > 85:
        conditions.append({"condition": "Hypertension", "date": fake.date_this_decade().isoformat()})
    if bmi > 30:
        conditions.append({"condition": "Obesity", "date": fake.date_this_decade().isoformat()})
    if random.random() < 0.2:
        conditions.append({"condition": "Type 2 Diabetes", "date": fake.date_this_decade().isoformat()})
        
    # Medications based on conditions
    meds = []
    for c in conditions:
        if c["condition"] == "Hypertension":
            meds.append({"name": "Lisinopril", "dosage": "10mg", "frequency": "Daily"})
        elif c["condition"] == "Type 2 Diabetes":
            meds.append({"name": "Metformin", "dosage": "500mg", "frequency": "Twice Daily"})
            
    # Notes
    notes = fake.paragraph(nb_sentences=3)
    if stress_level == "High":
        notes += " Patient reports high work-related stress."
    if sleep < 5:
        notes += " Patient complains of insomnia and fatigue."

    return {
        "patient_id": f"PT-{patient_id:04d}",
        "name": fake.name() if gender == "Male" else fake.name_female(), # Simple gender handling for name
        "age": age,
        "gender": gender,
        "heart_rate": resting_hr,
        "sleep_hours": sleep,
        "daily_steps": steps,
        "blood_pressure": bp_str,
        "stress_level": stress_level,
        "bmi": bmi,
        "medical_history": conditions,
        "medications": meds,
        "doctor_notes": notes,
        "last_updated": datetime.now().isoformat()
    }

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print(f"Generating {NUM_PATIENTS} patients in {DATA_DIR}...")
    
    for i in range(1, NUM_PATIENTS + 1):
        patient = generate_patient_data(i)
        filepath = os.path.join(DATA_DIR, f"{patient['patient_id']}.json")
        with open(filepath, 'w') as f:
            json.dump(patient, f, indent=2)
        print(f"Created {patient['patient_id']}")

if __name__ == "__main__":
    main()
