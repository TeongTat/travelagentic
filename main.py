import streamlit as st
import requests
from datetime import date
from openai import OpenAI
from PIL import Image

# ---------------------------
# 🔑 Setup
# ---------------------------
st.set_page_config(page_title="🌍 Agentic AI Travel Planner", layout="centered")
st.title("🌍 Agentic AI Travel Planner")

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------------------
# 🖼️ Header Image
# ---------------------------
try:
    st.image("summertravel.jpg", use_container_width=True)
except:
    st.info("Upload a header image called `summertravel.jpg` for better visuals.")

st.write("Your personal multi-agent travel assistant ✈️🌦️ Plan smarter, travel better!")

# ---------------------------
# 📍 Inputs
# ---------------------------
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("🛫 From (Airport Code)", "KUL")
    destination = st.text_input("📍 To (Airport Code)", "NRT")
with col2:
    start_date = st.date_input("🗓️ Departure Date", date.today())
    end_date = st.date_input("🗓️ Return Date", date.today())
weather_question = st.text_input("☁️ Weather or packing question?", "What should I pack?")
flight_pref = st.text_area("✈️ Flight preference", "Prefer direct flight, budget airline OK.")

# ---------------------------
# 🧠 Define Agents
# ---------------------------

class IntroAgent:
    """Generates travel intro and cultural overview"""
    def run(self, origin, destination):
        prompt = f"Give a friendly, concise travel introduction for a traveler from {origin} to {destination}. Include main attractions, food highlights, and safety/cultural tips."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return resp.choices[0].message.content


class FlightAgent:
    """Fetches flight details using AviationStack (Free API)"""
    def run(self, origin, destination):
        try:
            api_key = st.secrets["AVIATIONSTACK_KEY"]
            url = f"http://api.aviationstack.com/v1/flights?access_key={api_key}&dep_iata={origin}&arr_iata={destination}&limit=3"
            res = requests.get(url)
            data = res.json()

            flights = data.get("data", [])
            if not flights:
                return "🚫 No recent flight data found. Try different airports."

            output = ""
            for i, f in enumerate(flights, 1):
                airline = f.get("airline", {}).get("name", "Unknown Airline")
                flight_no = f.get("flight", {}).get("iata", "N/A")
                dep = f.get("departure", {}).get("airport", "Unknown")
                arr = f.get("arrival", {}).get("airport", "Unknown")
                dep_time = f.get("departure", {}).get("scheduled", "N/A")
                arr_time = f.get("arrival", {}).get("scheduled", "N/A")

                output += (
                    f"**#{i} {airline}** — Flight {flight_no}\n"
                    f"- 🛫 {dep} → 🛬 {arr}\n"
                    f"- 🕒 {dep_time} → {arr_time}\n\n"
                )
            return output
        except Exception as e:
            return f"❌ Flight data error: {e}"


class SummaryAgent:
    """Summarizes itinerary and gives packing/weather tips"""
    def run(self, origin, destination, weather_question, intro, flights):
        # Get weather data (Free Open-Meteo)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={destination}"
        geo_data = requests.get(geo_url).json()
        if not geo_data.get("results"):
            return "Could not retrieve weather data."
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=3"
        weather = requests.get(weather_url).json()
        temps = weather["daily"]
        avg_temp = sum(temps["temperature_2m_max"]) / len(temps["temperature_2m_max"])

        summary_prompt = f"""
You are a friendly AI travel assistant.
Trip: {origin} → {destination}
Flights:
{flights}
Average temperature: {avg_temp:.1f}°C

Weather/packing question: {weather_question}

Intro info:
{intro}

Summarize everything beautifully in markdown format.
Include:
- A short warm welcome
- Key travel highlights
- Flight summary
- Weather insights + packing advice
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7,
        )
        return resp.choices[0].message.content


# ---------------------------
# 🚀 Orchestrator (Simple Agentic Flow)
# ---------------------------
def run_agents():
    intro_agent = IntroAgent()
    flight_agent = FlightAgent()
    summary_agent = SummaryAgent()

    intro = intro_agent.run(origin, destination)
    flights = flight_agent.run(origin, destination)
    summary = summary_agent.run(origin, destination, weather_question, intro, flights)

    return intro, flights, summary


# ---------------------------
# Tabs
# ---------------------------
intro_tab, flight_tab, summary_tab = st.tabs(["🌏 Introduction", "🛫 Flights", "🧳 Summary"])

# ---------------------------
# Main Action
# ---------------------------
if st.button("🎯 Generate Full Plan"):
    with st.spinner("Agents are working together..."):
        intro_text, flight_text, summary_text = run_agents()

    with intro_tab:
        st.markdown(intro_text)
    with flight_tab:
        st.markdown(flight_text)
    with summary_tab:
        st.markdown(summary_text)
