import streamlit as st

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
