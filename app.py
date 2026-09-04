import streamlit as st
from medassist import Patient, ClinicalSafetyEngine

st.set_page_config(
    page_title="MedAssist Clinical AI",
    page_icon="🏥",
    layout="wide"
)

# =========================
# CUSTOM STYLING
# =========================

st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .hero {
        padding: 30px;
        border-radius: 18px;
        background: linear-gradient(135deg, #111827, #1e293b);
        border: 1px solid #334155;
        margin-bottom: 25px;
    }

    .hero h1 {
        font-size: 42px;
        margin-bottom: 8px;
    }

    .hero p {
        font-size: 18px;
        color: #cbd5e1;
    }

    .footer {
        text-align: center;
        color: #64748b;
        padding-top: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# HEADER
# =========================

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

engine = ClinicalSafetyEngine()

# =========================
# PATIENT INFORMATION
# =========================

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

allergies_input = st.text_input(
    "Allergies",
    placeholder="Example: penicillin, aspirin"
)

active_meds_input = st.text_input(
    "Active Medications",
    placeholder="Example: warfarin, aspirin"
)

patient = Patient(
    patient_id=patient_id,
    age=age,
    weight_kg=weight,
    allergies=(
        allergies_input.split(",")
        if allergies_input.strip()
        else []
    ),
    active_medications=(
        active_meds_input.split(",")
        if active_meds_input.strip()
        else []
    )
)

# =========================
# MEDICATION SAFETY CHECK
# =========================

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

# =========================
# RUN SAFETY CHECK
# =========================

if st.button(
    "🔍 Run Clinical Safety Check",
    type="primary",
    use_container_width=True
):

    if not new_drug.strip():

        st.warning(
            "Please enter a medication before running the analysis."
        )

    else:

        new_drug = new_drug.strip()

        allergy_alerts = engine.check_allergy(
            patient,
            new_drug
        )

        interaction_alerts = engine.check_interaction(
            patient,
            new_drug
        )

        dosage_alerts = engine.check_dosage_anomaly(
            new_drug,
            dosage
        )

        alerts = (
            allergy_alerts
            + interaction_alerts
            + dosage_alerts
        )

        # =========================
        # RISK ASSESSMENT
        # =========================

        st.divider()
        st.header("📋 Clinical Risk Assessment")

        risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)

        with risk_col1:
            st.metric(
                "Allergy Check",
                "⚠️ ALERT" if allergy_alerts else "✅ CLEAR"
            )

        with risk_col2:
            st.metric(
                "Interaction Check",
                "⚠️ ALERT" if interaction_alerts else "✅ CLEAR"
            )

        with risk_col3:
            st.metric(
                "Dosage Check",
                "⚠️ ANOMALY" if dosage_alerts else "✅ CLEAR"
            )

        with risk_col4:
            st.metric(
                "Safety Alerts",
                len(alerts)
            )

        st.divider()

        # =========================
        # BLOCKED PRESCRIPTION
        # =========================

        if alerts:

            st.error(
                "🚨 PRESCRIPTION BLOCKED"
            )

            st.write(
                f"MedAssist detected **{len(alerts)} safety alert(s)** "
                "and recommends that the prescription is not cleared."
            )

            st.subheader("⚠️ Safety Alerts")

            for index, alert in enumerate(
                alerts,
                start=1
            ):

                severity = alert.get(
                    "severity",
                    "UNKNOWN"
                )

                rationale = alert.get(
                    "rationale",
                    "No rationale provided."
                )

                with st.expander(
                    f"Alert {index}: {severity}"
                ):

                    st.write(
                        f"**Severity:** `{severity}`"
                    )

                    st.write(
                        f"**Rationale:** {rationale}"
                    )

                    if "z_score" in alert:

                        st.write(
                            f"**Dosage:** "
                            f"{alert['dosage_mg']} mg"
                        )

                        st.write(
                            f"**Historical Mean:** "
                            f"{alert['mean_mg']} mg"
                        )

                        st.write(
                            f"**Standard Deviation:** "
                            f"{alert['std_dev_mg']} mg"
                        )

                        st.write(
                            f"**Z-Score:** "
                            f"`{alert['z_score']}`"
                        )

            # Generate audit record
            engine.generate_audit_log(
                patient,
                new_drug,
                dosage,
                alerts
            )

            st.success(
                "🔐 Secure SHA-256 audit record generated."
            )

        # =========================
        # CLEAR PRESCRIPTION
        # =========================

        else:

            st.success(
                "✅ PRESCRIPTION CLEAR"
            )

            st.write(
                f"No clinical safety issues were detected for "
                f"**{new_drug} {dosage:g} mg**."
            )

            normalized_drug = new_drug.lower()

            if normalized_drug not in patient.active_medications:

                patient.active_medications.append(
                    normalized_drug
                )

            st.info(
                f"💊 {new_drug} has been cleared and added "
                "to the patient's active medications for this session."
            )

        # =========================
        # DOSAGE ANALYSIS
        # =========================

        st.divider()
        st.subheader("📊 Dosage Analysis")

        if dosage_alerts:

            dosage_data = dosage_alerts[0]

            d1, d2, d3, d4 = st.columns(4)

            with d1:
                st.metric(
                    "Prescribed",
                    f"{dosage_data['dosage_mg']} mg"
                )

            with d2:
                st.metric(
                    "Historical Mean",
                    f"{dosage_data['mean_mg']} mg"
                )

            with d3:
                st.metric(
                    "Standard Deviation",
                    f"{dosage_data['std_dev_mg']} mg"
                )

            with d4:
                st.metric(
                    "Z-Score",
                    dosage_data["z_score"]
                )

            st.warning(
                "The prescribed dosage is statistically anomalous "
                "according to the configured Z-score threshold."
            )

        else:

            st.success(
                "📊 Dosage is within the expected historical range."
            )

        # =========================
        # AUDIT TRAIL
        # =========================

        st.divider()
        st.subheader("🔐 Cryptographic Audit Trail")

        try:

            with open(
                "clinical_audit.log",
                "r",
                encoding="utf-8"
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

# =========================
# CAPABILITIES
# =========================

st.divider()
st.subheader("🛡️ Safety Engine Capabilities")

cap1, cap2, cap3 = st.columns(3)

with cap1:
    st.markdown(
        """
        **⚠️ Allergy Detection**

        Identifies prescriptions that match
        documented patient allergies.
        """
    )

with cap2:
    st.markdown(
        """
        **🔄 Drug Interaction Detection**

        Performs bidirectional checks against
        configured dangerous medication pairs.
        """
    )

with cap3:
    st.markdown(
        """
        **📊 Statistical Dosage Analysis**

        Uses historical dosage distributions
        and Z-score anomaly detection.
        """
    )

# =========================
# DISCLAIMER
# =========================

st.divider()

st.warning(
    "⚕️ **Prototype / Educational System:** "
    "MedAssist is a software engineering demonstration "
    "and is not intended to replace qualified clinical judgment "
    "or real-world medical decision-making."
)

# =========================
# FOOTER
# =========================

st.markdown(
    """
    <div class="footer">
        MedAssist Clinical AI • Clinical Decision Support System
    </div>
    """,
    unsafe_allow_html=True
)
