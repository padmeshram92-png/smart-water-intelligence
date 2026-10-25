
from datetime import datetime

import pandas as pd
import psycopg2
import streamlit as st

from simulator import run_scenario, SCENARIOS

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------
st.set_page_config(
    page_title="Smart Water Intelligence",
    page_icon="💧",
    layout="wide"
)

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
def get_connection():
    database_url = st.secrets["DATABASE_URL"]
    return psycopg2.connect(
        database_url,
        sslmode="require",
        connect_timeout=10
    )


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS water_incidents (
                                id BIGSERIAL PRIMARY KEY,
                                created_at TIMESTAMPTZ DEFAULT NOW(),
                                location TEXT NOT NULL,
                                problem_type TEXT NOT NULL,
                                description TEXT NOT NULL,
                                source TEXT NOT NULL,
                                incident_date DATE,
                                severity TEXT NOT NULL,
                                priority_score INTEGER NOT NULL,
                                status TEXT DEFAULT 'Pending Review',
                                alert_draft TEXT
                )
            """)

def save_reading(scenario_name, result):
    reading = result["reading"]
    detection = result["detection"]

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO readings (
                    timestamp, scenario, flow_lpm, tank_level_pct,
                    observed_liters, baseline_liters, status,
                    alert_type, message, severity
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                timestamp,
                scenario_name,
                reading["flow_lpm"],
                reading["tank_level_pct"],
                reading["observed_liters"],
                reading["baseline_liters"],
                detection["status"],
                detection["alert_type"],
                detection["message"],
                detection["severity"]
            ))


def load_history():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM readings ORDER BY id DESC",
            conn
        )


def clear_history():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM readings")

# -------------------------------
# WATER INCIDENT ANALYSIS
# -------------------------------

def assess_incident(problem_type, description):
    """
    Transparent rule-based priority assessment.
    This is not an AI model or verified emergency assessment.
    """

    text = description.lower()

    # Initial score based on incident type
    type_scores = {
        "Major Pipeline Burst": 60,
        "Water Leakage": 40,
        "Tank Overflow": 30,
        "Water Shortage": 35,
        "Contaminated Water": 60,
        "Other": 20
    }

    score = type_scores.get(problem_type, 20)

    # Add points for evidence of wider public impact
    impact_keywords = {
        "multiple houses": 15,
        "hospital": 20,
        "school": 10,
        "main road": 10,
        "flooding": 15,
        "drinking water": 10,
        "no water supply": 10
    }

    for keyword, points in impact_keywords.items():
        if keyword in text:
            score += points

    score = min(score, 100)

    if score >= 80:
        severity = "Critical"
    elif score >= 60:
        severity = "High"
    elif score >= 35:
        severity = "Medium"
    else:
        severity = "Low"

    return severity, score


def save_incident(
    location,
    problem_type,
    description,
    source,
    incident_date,
    severity,
    score
):
    alert_draft = (
        f"Water incident report: {problem_type}. "
        f"Location: {location}. "
        f"Details: {description}. "
        f"Reported source: {source}. "
        f"Priority: {severity}. "
        "Please verify the report and inspect if necessary."
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO water_incidents (
                    location,
                    problem_type,
                    description,
                    source,
                    incident_date,
                    severity,
                    priority_score,
                    alert_draft
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                location,
                problem_type,
                description,
                source,
                incident_date,
                severity,
                score,
                alert_draft
            ))


def load_incidents():
    with get_connection() as conn:
        return pd.read_sql_query("""
            SELECT *
            FROM water_incidents
            ORDER BY priority_score DESC, created_at DESC
        """, conn)

# -------------------------------
# INITIALIZE DATABASE
# -------------------------------
try:
    init_db()
except Exception as e:
    st.error("Database connection failed. Check your DATABASE_URL secret.")
    st.caption(f"Error type: {type(e).__name__}")
    st.stop()


# -------------------------------
# HEADER
# -------------------------------
st.title("💧 Smart Water Intelligence")
st.subheader("Cloud-Based Water Monitoring Prototype")

st.info(
    "Demo mode: This application uses simulated water readings. "
    "Alerts indicate possible problems, not confirmed physical leaks."
)

# -------------------------------
# WATER INCIDENT REPORTING
# -------------------------------

st.divider()
st.header("🌊 Real-World Water Incident Reporting")

st.caption(
    "Enter a reported water problem for initial priority assessment. "
    "Reports are not independently verified."
)

with st.form("incident_form"):

    location = st.text_input(
        "Incident location",
        placeholder="Example: Gandhipuram, Coimbatore"
    )

    problem_type = st.selectbox(
        "Problem type",
        [
            "Water Leakage",
            "Major Pipeline Burst",
            "Tank Overflow",
            "Water Shortage",
            "Contaminated Water",
            "Other"
        ]
    )

    description = st.text_area(
        "Incident description",
        placeholder=(
            "Describe the reported problem, "
            "affected area and public impact."
        )
    )

    source = st.text_input(
        "Information source",
        placeholder="Example: Official complaint / News report / Citizen report"
    )

    incident_date = st.date_input(
        "Date of incident",
        value=datetime.now().date()
    )

    submitted = st.form_submit_button(
        "Analyse and Save Incident",
        type="primary"
    )

    if submitted:

        if not location.strip():
            st.error("Please enter the incident location.")

        elif not description.strip():
            st.error("Please enter the incident description.")

        elif not source.strip():
            st.error("Please identify the information source.")

        else:
            severity, score = assess_incident(
                problem_type,
                description
            )

            try:
                save_incident(
                    location.strip(),
                    problem_type,
                    description.strip(),
                    source.strip(),
                    incident_date,
                    severity,
                    score
                )

                st.success("Incident report saved to Supabase!")

                st.metric("Initial Priority", severity)
                st.metric("Priority Score", f"{score}/100")

                st.warning(
                    "This is an initial rule-based assessment, "
                    "not a verified emergency classification."
                )

                st.rerun()

            except Exception as e:
                st.error("Could not save the incident report.")
                st.caption(f"Error type: {type(e).__name__}")


# -------------------------------
# SIDEBAR
# -------------------------------
scenario_labels = {
    "normal": "Normal Water Usage",
    "continuous_flow": "Continuous Flow - Possible Leak",
    "tank_overflow": "Tank Overflow Risk",
    "usage_spike": "Unusual Water Consumption"
}

with st.sidebar:
    st.header("Water Monitoring Controls")

    selected_scenario = st.selectbox(
        "Select a scenario",
        options=list(scenario_labels.keys()),
        format_func=lambda x: scenario_labels[x]
    )

    run_button = st.button(
        "Run Simulation",
        type="primary",
        use_container_width=True
    )

    st.divider()
    st.caption("Smart Water Intelligence v1.0")


# -------------------------------
# RUN SIMULATION
# -------------------------------
if run_button:
    try:
        result = run_scenario(selected_scenario)
        save_reading(selected_scenario, result)

        st.session_state["last_result"] = result
        st.session_state["last_scenario"] = selected_scenario

        st.success("Simulation completed and saved to cloud database!")
    except Exception as e:
        st.error("Could not save the simulation to the cloud database.")
        st.caption(f"Error type: {type(e).__name__}")


# -------------------------------
# LATEST DETECTION
# -------------------------------
if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    detection = result["detection"]

    st.subheader("Latest Detection")

    if detection["status"] == "Normal":
        st.success(
            f'{detection["status"]}: {detection["message"]}'
        )
    elif detection["severity"] == "high":
        st.error(
            f'{detection["status"]}: {detection["message"]}'
        )
    else:
        st.warning(
            f'{detection["status"]}: {detection["message"]}'
        )

    st.write(
        "Scenario:",
        scenario_labels[st.session_state["last_scenario"]]
    )


# -------------------------------
# LOAD CLOUD HISTORY
# -------------------------------
try:
    history = load_history()
except Exception as e:
    st.error("Could not load readings from the cloud database.")
    st.caption(f"Error type: {type(e).__name__}")
    st.stop()

total = len(history)

if total > 0:
    alerts = int(
        history["status"].isin(["Alert", "Warning"]).sum()
    )
    latest = history.iloc[0]
    flow = float(latest["flow_lpm"])
    tank = float(latest["tank_level_pct"])
else:
    alerts = 0
    flow = 0.0
    tank = 0.0


# -------------------------------
# DASHBOARD METRICS
# -------------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Readings", total)
c2.metric("Alerts Generated", alerts)
c3.metric("Latest Flow", f"{flow:.1f} L/min" if total else "—")
c4.metric("Tank Level", f"{tank:.0f}%" if total else "—")


# -------------------------------
# CHARTS
# -------------------------------
st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Water Consumption")

    if total > 0:
        chart_data = history[
            ["timestamp", "observed_liters", "baseline_liters"]
        ].copy()

        chart_data["timestamp"] = pd.to_datetime(
            chart_data["timestamp"], errors="coerce"
        )

        chart_data = chart_data.dropna(
            subset=["timestamp"]
        ).sort_values("timestamp")

        chart_data = chart_data.set_index("timestamp")

        st.line_chart(chart_data)
    else:
        st.write("Run a simulation to view the chart.")


with right:
    st.subheader("Detection Summary")

    if total > 0:
        summary = (
            history["status"]
            .value_counts()
            .rename_axis("Status")
            .to_frame("Count")
        )
        st.bar_chart(summary)
    else:
        st.write("No readings available yet.")

# -------------------------------
# INCIDENT PRIORITY DASHBOARD
# -------------------------------

st.divider()
st.header("🚨 Water Incident Priority Dashboard")

try:
    incidents = load_incidents()

    if incidents.empty:
        st.info(
            "No incident reports yet. "
            "Submit a report using the form above."
        )

    else:
        critical_count = int(
            (incidents["severity"] == "Critical").sum()
        )

        high_count = int(
            (incidents["severity"] == "High").sum()
        )

        pending_count = int(
            (incidents["status"] == "Pending Review").sum()
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Incidents", len(incidents))
        c2.metric("Critical Incidents", critical_count)
        c3.metric("Pending Review", pending_count)

        st.subheader("Incident Reports")

        st.dataframe(
            incidents[
                [
                    "created_at",
                    "location",
                    "problem_type",
                    "severity",
                    "priority_score",
                    "status",
                    "source"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Prepare Water Board Alert")

        selected_id = st.selectbox(
            "Select an incident",
            incidents["id"].tolist(),
            format_func=lambda incident_id: (
                f"Incident #{incident_id} — "
                f"{incidents.loc[
                    incidents['id'] == incident_id,
                    'location'
                ].iloc[0]}"
            )
        )

        selected = incidents[
            incidents["id"] == selected_id
        ].iloc[0]

        st.text_area(
            "Complaint summary",
            value=selected["alert_draft"] or "",
            height=150,
            key=f"alert_draft_{selected_id}"
        )

        st.caption(
            "Review the source and incident details before forwarding. "
            "This prototype does not automatically notify the Water Board."
        )

        st.download_button(
            "Download Incident Report",
            data=incidents[
                incidents["id"] == selected_id
            ].to_csv(index=False).encode("utf-8"),
            file_name=f"water_incident_{selected_id}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error("Could not load incident reports.")
    st.caption(f"Error type: {type(e).__name__}")
# -------------------------------
# HISTORY
# -------------------------------
st.divider()
st.subheader("Reading and Alert History")

if total > 0:
    display = history.rename(columns={
        "timestamp": "Time",
        "scenario": "Scenario",
        "flow_lpm": "Flow (L/min)",
        "tank_level_pct": "Tank Level (%)",
        "observed_liters": "Observed (L)",
        "baseline_liters": "Baseline (L)",
        "status": "Status",
        "alert_type": "Alert Type",
        "message": "Message",
        "severity": "Severity"
    })

    columns = [
        "Time", "Scenario", "Flow (L/min)",
        "Tank Level (%)", "Observed (L)",
        "Baseline (L)", "Status", "Severity", "Message"
    ]

    st.dataframe(
        display[columns],
        use_container_width=True,
        hide_index=True
    )

    csv = display[columns].to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download History as CSV",
        data=csv,
        file_name="water_monitoring_history.csv",
        mime="text/csv"
    )

    if st.button("Clear History"):
        try:
            clear_history()
            st.session_state.pop("last_result", None)
            st.session_state.pop("last_scenario", None)
            st.rerun()
        except Exception as e:
            st.error("Could not clear cloud history.")
            st.caption(f"Error type: {type(e).__name__}")
else:
    st.write("No history yet. Run your first simulation!")


# -------------------------------
# FOOTER
# -------------------------------
st.caption(
    "Prototype uses simulated data and rule-based detection. "
    "Real-world leakage detection requires sensor readings and validation."
)
