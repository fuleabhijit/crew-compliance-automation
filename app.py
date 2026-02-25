import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_KEY = "9fd812ae14fd8f852227d0600e3228da"

MAX_DAILY_FLIGHT = 7
MAX_WEEKLY_FLIGHT = 30

if "pilot_hours" not in st.session_state:
    st.session_state.pilot_hours = {
        "Raj": 20,
        "Amit": 25,
        "Vikram": 10
    }

def get_flights(airport):
    url = f"http://api.aviationstack.com/v1/flights?access_key={API_KEY}&dep_iata={airport}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None, f"API returned {response.status_code}"
        data = response.json()
        if "error" in data:
            return None, data["error"]["message"]
        flights = data.get("data", [])
        if not flights:
            return None, "No flights found"
        cleaned = []
        for f in flights[:10]:
            cleaned.append({
                "Airline": f.get("airline", {}).get("name"),
                "Flight": f.get("flight", {}).get("number"),
                "From": f.get("departure", {}).get("airport"),
                "Scheduled": f.get("departure", {}).get("scheduled"),
                "Status": f.get("flight_status")
            })
        return cleaned, None
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.ConnectionError:
        return None, "Connection error"
    except Exception as e:
        return None, str(e)

def validate(pilot, hours):
    current = st.session_state.pilot_hours[pilot]
    projected = current + hours
    if hours > MAX_DAILY_FLIGHT:
        return "Violation", "Daily 7 hour limit exceeded"
    if projected > MAX_WEEKLY_FLIGHT:
        return "Violation", "Weekly 30 hour limit exceeded"
    if projected >= 0.8 * MAX_WEEKLY_FLIGHT:
        return "Warning", "Approaching weekly limit"
    return "Compliant", "Within allowed limits"

st.set_page_config(page_title="Live Crew Compliance", layout="wide")

st.title("✈ Live Aviation Crew Compliance")

airport = st.text_input("Departure Airport IATA Code", "DEL")

if st.button("Fetch Live Flights"):
    flights, error = get_flights(airport)
    if error:
        st.error(error)
    else:
        df = pd.DataFrame(flights)
        st.dataframe(df)

        st.subheader("Assign Flight")

        pilot = st.selectbox("Select Pilot", list(st.session_state.pilot_hours.keys()))
        duration = st.slider("Flight Duration (Hours)", 1, 8, 2)

        if st.button("Validate Assignment"):
            status, message = validate(pilot, duration)

            if status == "Violation":
                st.error(message)
            elif status == "Warning":
                st.warning(message)
            else:
                st.success(message)
                st.session_state.pilot_hours[pilot] += duration

            st.write("Current Weekly Hours:", st.session_state.pilot_hours[pilot])

st.subheader("Pilot Weekly Overview")

summary = pd.DataFrame(
    st.session_state.pilot_hours.items(),
    columns=["Pilot", "Weekly Hours"]
)

st.dataframe(summary)
st.bar_chart(summary.set_index("Pilot"))