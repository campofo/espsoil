import streamlit as st
import pandas as pd
import requests
import altair as alt
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import cloudpickle
import numpy as np

# === Config ===
st.set_page_config(page_title="🌿 IoT Sensor Dashboard", layout="centered")
st.title(":seedling: Smart Soil Monitor (Live Data)")

st_autorefresh(interval=1 * 1000)

API_URL = "https://hunterperry08.pythonanywhere.com/get-data"

# === Fetch data ===
@st.cache_data(ttl=3)
def fetch_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = fetch_data()

# === Load ML model ===
with open("plant_predictor.pkl", "rb") as f:
    model = cloudpickle.load(f)

with open("plant_label_encoder.pkl", "rb") as f:
    label_encoder = cloudpickle.load(f)

# === If data available ===
if df.empty:
    st.warning("No sensor data available yet.")
else:
    # Preprocess
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    latest = df.iloc[-1]

    # === Moisture interpretation ===
    def interpret_moisture(value):
        if value >= 4095:
            return "Very Dry 🌵"
        elif value <= 2400:
            return "Wet 🌊"
        else:
            return "Moist 🌱"

    # === Latest values ===
    st.subheader("📊 Latest Sensor Readings")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🌡 Temperature", f"{latest['temperature']} °C")
        st.metric("💧 Humidity", f"{latest['humidity']} %")
    with col2:
        st.metric("🪴 Moisture", latest['moisture'])
        st.success(f"Soil Status: {interpret_moisture(latest['moisture'])}")

    # === Gauge Charts ===
    st.subheader("🎯 Gauges (Latest Readings)")
    col1, col2 = st.columns(2)

    with col1:
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest['humidity'],
            title={'text': "💧 Humidity (%)"},
            gauge={'axis': {'range': [0, 100]}}
        ))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest['moisture'],
            title={'text': "🪴 Moisture"},
            gauge={'axis': {'range': [2000, 4095]}}
        ))
        st.plotly_chart(fig2, use_container_width=True)

    # === ML Prediction: Suitable Plants ===
    st.subheader("🌿 Suitable Plants & Viability Score")
    input_data = np.array([[latest['temperature'], latest['moisture'], latest['humidity']]])
    probabilities = model.predict_proba(input_data)[0]

    plant_classes = label_encoder.inverse_transform(np.arange(len(probabilities)))
    viability_df = pd.DataFrame({
        "Plant": plant_classes,
        "Viability Score (%)": (probabilities * 100).round(2)
    })
    viability_df = viability_df[viability_df["Viability Score (%)"] > 20.0]
    viability_df = viability_df.sort_values(by="Viability Score (%)", ascending=False)

    if not viability_df.empty:
        st.dataframe(viability_df.reset_index(drop=True))

        st.bar_chart(viability_df.set_index("Plant"))
    else:
        st.warning("⚠️ No suitable plants found for the current conditions.")

    # === Trend Visualization ===
    st.subheader("📈 Humidity & Moisture Trends")
    df_reset = df.reset_index()[['timestamp', 'humidity', 'moisture']]

    base = alt.Chart(df_reset).encode(x='timestamp:T')

    line_humidity = base.mark_line(color='skyblue').encode(
        y=alt.Y('humidity:Q', axis=alt.Axis(title='Humidity (%)'))
    )
    line_moisture = base.mark_line(color='green').encode(
        y=alt.Y('moisture:Q', axis=alt.Axis(title='Moisture', titleColor='green'))
    )

    st.altair_chart(
        alt.layer(line_humidity, line_moisture).resolve_scale(y='independent'),
        use_container_width=True
    )

    # === Raw data ===
    with st.expander("📋 View All Sensor Data"):
        st.dataframe(df)

st.caption("Dashboard powered by Streamlit, Altair, Plotly, and PythonAnywhere 🐍")
