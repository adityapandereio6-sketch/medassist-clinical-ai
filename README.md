# 🏥 MedAssist Clinical AI

> A clinical decision-support prototype for medication safety analysis, combining rule-based drug interaction detection, allergy screening, statistical dosage anomaly detection, and cryptographic audit logging.

## 🚀 Live Demo

👉 [Open MedAssist Clinical AI Dashboard](https://medassist-clinical-ai-5vhsp5gsb6mah3xog2thp8.streamlit.app/)

---

## 📌 Overview

MedAssist Clinical AI is a Python-based clinical decision-support prototype designed to identify potential medication safety risks before a prescription is cleared.

The system evaluates:

- Patient allergies
- Active medications
- Drug-drug interactions
- Dosage anomalies
- Clinical safety alerts
- Cryptographic audit records

The project provides both a reusable Python safety engine and an interactive Streamlit dashboard.

---

## ⚡ Key Features

### ⚠️ Allergy Detection

Checks whether a newly prescribed medication matches a patient's recorded allergies.

### 🔄 Drug Interaction Detection

Performs bidirectional medication interaction checks against configured contraindicated drug combinations.

### 📊 Dosage Anomaly Detection

Uses historical dosage distributions and statistical Z-scores to identify unusually high dosage values.

### 🔐 SHA-256 Audit Logging

Clinical safety events are recorded with timestamps and SHA-256 hashes to provide an integrity-focused audit trail.

### 🖥️ Interactive Dashboard

The Streamlit interface allows users to enter:

- Patient ID
- Age
- Weight
- Allergies
- Active medications
- New medication
- Dosage

The dashboard then provides a structured clinical risk assessment.

---

## 🧠 Safety Decision Flow

```text
Patient Information
        ↓
Medication Input
        ↓
┌───────────────────────┐
│ Allergy Detection     │
├───────────────────────┤
│ Interaction Detection │
├───────────────────────┤
│ Dosage Analysis       │
└───────────────────────┘
        ↓
   Risk Assessment
        ↓
 ┌───────────────┐
 │ CLEAR / BLOCK │
 └───────────────┘
        ↓
Cryptographic Audit Log
🧪 Example Safety Scenarios
Drug Interaction
Active Medication: warfarin
New Medication: aspirin
Dosage: 81 mg

Result:

🚨 PRESCRIPTION BLOCKED
CRITICAL_INTERACTION
Allergy Detection
Allergy: penicillin
New Medication: penicillin

Result:

🚨 PRESCRIPTION BLOCKED
CRITICAL_ALLERGY
Dosage Anomaly
Medication: ibuprofen
Dosage: 5000 mg

Result:

🚨 PRESCRIPTION BLOCKED
DOSAGE_ANOMALY
🛠️ Technology Stack
Python
Streamlit
Object-Oriented Programming
Rule-Based Clinical Safety Logic
Statistical Z-Score Analysis
SHA-256 Cryptographic Hashing
JSON
Git & GitHub
📂 Project Structure
medassist-clinical-ai/
│
├── app.py
├── medassist.py
├── clinical_audit.log
└── README.md
▶️ Run Locally

Clone the repository:

git clone https://github.com/adityapandereio6-sketch/medassist-clinical-ai.git

Move into the project:

cd medassist-clinical-ai

Install Streamlit:

pip install streamlit

Run the dashboard:

streamlit run app.py
🔬 Core Safety Engine

The underlying ClinicalSafetyEngine performs three primary checks:

check_allergy()
        +
check_interaction()
        +
check_dosage_anomaly()
        ↓
     ALERTS
        ↓
CLEAR / BLOCKED

The system uses normalized medication names to improve consistency when checking medication and allergy inputs.

🔐 Audit Integrity

When a prescription is blocked, MedAssist generates an audit record containing information such as:

Patient identifier
Medication
Dosage
Detected alerts
UTC timestamp
SHA-256 hash

This demonstrates how cryptographic hashing can be incorporated into an audit-oriented clinical software workflow.

⚕️ Important Disclaimer

MedAssist Clinical AI is an educational and software-engineering prototype.

It is not intended for real-world clinical decision-making, diagnosis, treatment, or prescription authorization and should not replace qualified healthcare professionals or validated clinical systems.

👨‍💻 Author

Aditya Pandere

B.Tech — Computer Science & Engineering (AI/ML)

⭐ If you found this project interesting, consider giving the repository a star!
