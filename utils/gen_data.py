import json
import random
import os
from datetime import datetime, timedelta

# Configuration
NUM_PATIENTS = 10
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def generate_patient_data(patient_idx):
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
    current_date = datetime.now()
    if systolic > 130 or diastolic > 85:
        # random date in last 5 years
        days_ago = random.randint(100, 1800)
        diagnosis_date = (current_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        conditions.append({"condition": "Hypertension", "diagnosed_date": diagnosis_date, "status": "Active"})
    
    if bmi > 30:
        days_ago = random.randint(100, 1800)
        diagnosis_date = (current_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        conditions.append({"condition": "Obesity", "diagnosed_date": diagnosis_date, "status": "Active"})
        
    if random.random() < 0.2:
        days_ago = random.randint(100, 1800)
        diagnosis_date = (current_date - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        conditions.append({"condition": "Type 2 Diabetes", "diagnosed_date": diagnosis_date, "status": "Managed"})
        
    # Medications based on conditions
    meds = []
    for c in conditions:
        if c["condition"] == "Hypertension":
            meds.append({"name": "Lisinopril", "dosage": "10mg", "frequency": "Daily"})
        elif c["condition"] == "Type 2 Diabetes":
            meds.append({"name": "Metformin", "dosage": "500mg", "frequency": "Twice Daily"})
            
    # Notes - Simple templates to avoid Faker dependency
    notes_templates = [
        "Patient is generally healthy but needs to improve sleep schedule. Recommend cutting caffeine.",
        "Patient reports occasional headaches in the morning. Monitoring BP.",
        "Follow-up required in 3 months for cholesterol check.",
        "Weight management plan discussed. Dietician referral provided.",
        "Patient is compliant with medication. No side effects reported.",
        "Blood pressure is slightly elevated compared to last visit.",
        "Patient is active and exercising regularly."
    ]
    
    notes = random.choice(notes_templates)
    
    if stress_level == "High":
        notes += " Patient reports high work-related stress affecting sleep."
    if sleep < 5:
        notes += " Patient complains of insomnia and fatigue."

    # Simple name generation
    first_names_m = ["James", "Robert", "John", "Michael", "David", "William", "Richard", "Joseph", "Thomas", "Charles"]
    first_names_f = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    nm = ""
    if gender == "Male":
        nm = f"{random.choice(first_names_m)} {random.choice(last_names)}"
    else:
        nm = f"{random.choice(first_names_f)} {random.choice(last_names)}"

    return {
        "patient_id": f"patient_{patient_idx:02d}",
        "name": nm,
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
    
    # Use fixed seed for reproducibility if needed, but random is fine here
    for i in range(1, NUM_PATIENTS + 1):
        # Generate patient_01, patient_02, etc.
        patient = generate_patient_data(i)
        
        # Ensure filename and ID match
        final_id = patient['patient_id']
        filepath = os.path.join(DATA_DIR, f"{final_id}.json")
        
        with open(filepath, 'w') as f:
            json.dump(patient, f, indent=2)
        print(f"Created {final_id}")

if __name__ == "__main__":
    main()
