import streamlit as st
import pandas as pd
from supabase import create_client
import os
from datetime import datetime

# Connect to Supabase
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

st.set_page_config(page_title="JointGuard", page_icon="🦴", layout="wide")
st.title("🦴 JointGuard — RA Flare Prediction")
st.caption("AI-Powered 48-hour flare prediction using MedGemma 4B")
st.divider()

# Sidebar
st.sidebar.title("Patient")
patient_id = st.sidebar.selectbox("Select Patient", ["patient_demo", "patient_001"])
st.sidebar.divider()
st.sidebar.subheader("📱 Fitbit Data")
st.sidebar.metric("Sleep", "5.2 hrs", "-2.3 hrs")
st.sidebar.metric("HRV", "28 ms", "-15 ms")
st.sidebar.metric("Steps", "3,200", "-4,800")
st.sidebar.caption("⚠️ All metrics below baseline")

# Current Risk
st.subheader("🚨 Current Flare Risk")
data = sb.table("risk_scores").select("*").eq(
    "patient_id", patient_id
).order("created_at", desc=True).limit(1).execute().data

if data:
    latest = data[0]
    score = latest["risk_score"]
    level = latest["risk_level"]
    color = {"GREEN": "green", "AMBER": "orange", "RED": "red"}[level]

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", f"{score}/100")
    col2.markdown(f"### :{color}[{level} ALERT]")
    col3.metric("Time", datetime.now().strftime("%H:%M %d/%m/%Y"))
    st.info(f"🧠 {latest.get('reasoning', '')}")

    # Action Card
    if latest.get("action_card"):
        st.subheader("📋 Action Card")
        ac = latest["action_card"]
        col1, col2, col3 = st.columns(3)
        col1.error(f"🛏️ Rest\n\n{ac.get('rest', '')}")
        col2.warning(f"💊 Medication\n\n{ac.get('medication', '')}")
        col3.error(f"👨‍⚕️ Doctor\n\n{ac.get('doctor_contact', '')}")

st.divider()

# 30 Day Trend
st.subheader("📈 30-Day Risk Trend")
history = sb.table("risk_scores").select("*").eq(
    "patient_id", patient_id
).order("created_at").execute().data

if history:
    df = pd.DataFrame(history)
    df["created_at"] = pd.to_datetime(df["created_at"])
    st.line_chart(df.set_index("created_at")["risk_score"])

    if st.button("🔍 Reveal Flare Event"):
        st.error("⚠️ Flare at Day 11 — JointGuard predicted 48hrs earlier!")

st.divider()

# Wearable Trend
st.subheader("⌚ Wearable Trends")
wear = sb.table("wearable_readings").select("*").eq(
    "patient_id", patient_id
).order("created_at").execute().data

if wear:
    wdf = pd.DataFrame(wear)
    wdf["created_at"] = pd.to_datetime(wdf["created_at"])
    wdf = wdf.set_index("created_at")
    col1, col2 = st.columns(2)
    col1.caption("HRV (ms)")
    col1.line_chart(wdf["hrv_rmssd"])
    col2.caption("Sleep (hrs)")
    col2.line_chart(wdf["sleep_hours"])

st.divider()

# Doctor Report
st.subheader("📄 Doctor Report")
if st.button("Generate Report", type="primary"):
    if history:
        df2 = pd.DataFrame(history)
        report = f"""
JOINTGUARD PATIENT REPORT
==========================
Patient ID: {patient_id}
Generated: {datetime.now().strftime("%d/%m/%Y %H:%M")}

CURRENT STATUS: {level} — {score}/100

AI REASONING:
{latest.get("reasoning", "")}

30-DAY SUMMARY:
- Average Risk: {int(df2["risk_score"].mean())}/100
- Peak Risk: {int(df2["risk_score"].max())}/100
- RED days: {len(df2[df2["risk_score"] >= 70])}
- AMBER days: {len(df2[(df2["risk_score"] >= 40) & (df2["risk_score"] < 70)])}
- GREEN days: {len(df2[df2["risk_score"] < 40])}
        """
        st.text(report)
        st.download_button(
            "⬇️ Download Report",
            data=report,
            file_name=f"jointguard_{patient_id}.txt",
            mime="text/plain"
        )
```