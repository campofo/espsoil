import streamlit as st
import pandas as pd
import requests
import altair as alt
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# === Config ===
st.set_page_config(page_title="🌿 IoT Sensor Dashboard", layout="centered")
st.title("🌿 Smart Soil Monitor (Live Data)")

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

# === If data available ==s=
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
