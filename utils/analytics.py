from typing import Dict, List, Any

class HealthAnalytics:
    @staticmethod
    def check_anomalies(patient_data: Dict[str, Any]) -> List[str]:
        """
        Checks for health anomalies based on static rules.
        """
        anomalies = []
        
        # 1. Heart Rate check
        hr = patient_data.get("heart_rate")
        if hr and hr > 100:
            anomalies.append(f"High Heart Rate Detected: {hr} bpm (Normal < 100)")
            
        # 2. Sleep check
        sleep = patient_data.get("sleep_hours") 
        if sleep and sleep < 5:
            anomalies.append(f"Low Sleep Duration: {sleep} hours (Recommended > 7)")
            
        # 3. Blood Pressure check
        bp = patient_data.get("blood_pressure")
        if bp:
            try:
                systolic, diastolic = map(int, bp.split('/'))
                if systolic > 140 or diastolic > 90:
                    anomalies.append(f"High Blood Pressure: {bp} (Normal < 120/80)")
            except ValueError:
                pass # skip if format is bad
                
        # 4. Activity check
        steps = patient_data.get("daily_steps")
        if steps and steps < 3000:
            anomalies.append(f"Low Physical Activity: {steps} steps (Target > 5000)")
            
        return anomalies

        
        if score == 0: return "Low Risk"
        if score <= 2: return "Moderate Risk"
        return "High Risk"
