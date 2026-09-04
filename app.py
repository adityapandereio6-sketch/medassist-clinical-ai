import streamlit as st
from medassist import Patient, ClinicalSafetyEngine
st.set_page_config(
    page_title="MedAssist Clinical AI",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 MedAssist Clinical AI")
st.subheader("Clinical Decision Support & Medication Safety Engine")

st.write(
    "Analyze medication safety using allergy detection, "
    "drug interaction checks, and dosage anomaly detection."
)
st.divider()

st.header("👤 Patient Information")

patient_id = st.text_input("Patient ID", "P001")
age = st.number_input("Age", min_value=0, max_value=120, value=30)
weight = st.number_input("Weight (kg)", min_value=1.0, value=70.0)

allergies = st.text_input(
    "Allergies",
    placeholder="e.g. penicillin, aspirin"
)

active_meds = st.text_input(
    "Active Medications",
    placeholder="e.g. warfarin, aspirin"
)
