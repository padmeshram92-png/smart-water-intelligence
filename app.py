
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
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

DB_PATH = Path(__file__).resolve().parent / "water_monitoring.db"


# -------------------------------
# DATABASE
# -------------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scenario TEXT NOT NULL,
                flow_lpm REAL,
                tank_level_pct REAL,
                observed_liters REAL,
                baseline_liters REAL,
                status TEXT,
                alert_type TEXT,
                message TEXT,
                severity TEXT
            )
        """)
        conn.commit()


def save_reading(scenario_name, result):
    reading = result["reading"]
    detection = result["detection"]

    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO readings (
                timestamp, scenario, flow_lpm, tank_level_pct,
                observed_liters, baseline_liters, status,
                alert_type, message, severity
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn.commit()


def load_history():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM readings ORDER BY id DESC",
            conn
        )


init_db()


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
    result = run_scenario(selected_scenario)
    save_reading(selected_scenario, result)

    st.session_state["last_result"] = result
    st.session_state["last_scenario"] = selected_scenario

    st.success("Simulation completed and saved!")


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
# DASHBOARD METRICS
# -------------------------------
history = load_history()

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
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM readings")
            conn.commit()

        st.session_state.pop("last_result", None)
        st.session_state.pop("last_scenario", None)
        st.rerun()

else:
    st.write("No history yet. Run your first simulation!")


# -------------------------------
# FOOTER
# -------------------------------
st.caption(
    "Prototype uses simulated data and rule-based detection. "
    "Real-world leakage detection requires sensor readings and validation."
)
