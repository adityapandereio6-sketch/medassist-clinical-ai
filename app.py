import streamlit as st
from medassist import Patient, ClinicalSafetyEngine


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="MedAssist Clinical AI",
    page_icon="🏥",
    layout="wide"
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        .main {
            background-color: #0e1117;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .hero {
            padding: 25px;
            border-radius: 15px;
            background: linear-gradient(
                135deg,
                #111827,
                #1e293b
            );
            border: 1px solid #334155;
            margin-bottom: 25px;
        }

        .hero h1 {
            margin-bottom: 5px;
        }

        .status-box {
            padding: 20px;
            border-radius: 12px;
            margin-top: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🏥 MedAssist Clinical AI</h1>
        <p>
            Clinical Decision Support & Medication Safety Engine
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write(
    "Analyze medication safety using allergy detection, "
    "drug interaction checks, dosage anomaly detection, "
    "and cryptographic audit logging."
)


# ---------------------------------------------------------
# INITIALIZE ENGINE
# ---------------------------------------------------------

engine = ClinicalSafetyEngine()


# ---------------------------------------------------------
# PATIENT INFORMATION
# ---------------------------------------------------------

st.divider()

st.header("👤 Patient Information")

col1, col2, col3 = st.columns(3)

with col1:
    patient_id = st.text_input(
        "Patient ID",
        value="P001"
    )

with col2:
    age = st.number_input(
        "Age",
        min_value=0,
        max_value=120,
        value=30
    )

with col3:
    weight = st.number_input(
        "Weight (kg)",
        min_value=1.0,
        value=70.0
    )


allergies = st.text_input(
    "Allergies",
    placeholder="Example: penicillin, aspirin"
)

active_meds = st.text_input(
    "Active Medications",
    placeholder="Example: warfarin, aspirin"
)


# ---------------------------------------------------------
# CREATE PATIENT
# ---------------------------------------------------------

patient = Patient(
    patient_id=patient_id,
    age=age,
    weight_kg=weight,
    allergies=allergies.split(",") if allergies else [],
    active_meds=active_meds.split(",") if active_meds else []
)


# ---------------------------------------------------------
# MEDICATION INPUT
# ---------------------------------------------------------

st.divider()

st.header("💊 Medication Safety Check")

col1, col2 = st.columns(2)

with col1:
    new_drug = st.text_input(
        "New Medication",
        placeholder="Example: aspirin"
    )

with col2:
    dosage = st.number_input(
        "Dosage (mg)",
        min_value=0.0,
        value=100.0
    )


# ---------------------------------------------------------
# SAFETY CHECK
# ---------------------------------------------------------

if st.button(
    "🔍 Run Clinical Safety Check",
    type="primary",
    use_container_width=True
):

    if not new_drug.strip():

        st.warning("Please enter a medication.")

    else:

        # Normalize medication name
        new_drug = new_drug.strip()

        # Run clinical checks
        allergy_alert = engine.check_allergy(
            patient,
            new_drug
        )

        interaction_alert = engine.check_interaction(
            patient,
            new_drug
        )

        dosage_alert = engine.check_dosage_anomaly(
            new_drug,
            dosage
        )

        # Combine all alerts
        alerts = (
            allergy_alert
            + interaction_alert
            + dosage_alert
        )


        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        st.divider()

        if alerts:

            st.error("🚨 PRESCRIPTION BLOCKED")

            st.subheader("⚠️ Safety Alerts")

            for alert in alerts:

                if isinstance(alert, dict):

                    st.warning(
                        alert.get(
                            "message",
                            str(alert)
                        )
                    )

                else:

                    st.warning(str(alert))


        else:

            st.success("✅ PRESCRIPTION CLEAR")

            st.write(
                "No clinical safety issues detected."
            )


        # -------------------------------------------------
        # DOSAGE ANALYSIS
        # -------------------------------------------------

        st.subheader("📊 Dosage Analysis")

        if dosage_alert:

            for result in dosage_alert:

                if isinstance(result, dict):

                    st.json(result)

                else:

                    st.write(result)

        else:

            st.success(
                "Dosage is within the expected range."
            )


        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------

        st.subheader("🔐 Clinical Audit Log")

        try:

            with open(
                "clinical_audit.log",
                "r"
            ) as f:

                audit_log = f.read()

            if audit_log.strip():

                st.code(
                    audit_log,
                    language="text"
                )

            else:

                st.info(
                    "No audit events recorded yet."
                )

        except FileNotFoundError:

            st.info(
                "No audit events recorded yet."
            )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "MedAssist Clinical AI • Clinical Decision Support System"
)
