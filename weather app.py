import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Global Weather Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Hide default styling
hide_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stTabs [data-baseweb="tab-list"] {gap: 1rem;}
.stTabs [data-baseweb="tab"] {height: 3rem; font-size: 1rem;}
</style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ------------------------------
# Core function: Fetch data from Open-Meteo API
# ------------------------------
def get_weather_data(lat, lon):
    """Retrieve weather data from Open-Meteo public API"""
    api_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", 
                   "weather_code", "is_day"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", 
                 "rain_sum", "snowfall_sum", "sunshine_duration"],
        "hourly": ["temperature_2m", "precipitation"],
        "timezone": "auto",
        "forecast_days": 7,
        "hourly_steps": 1
    }

    try:
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Connection timed out. Please try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

# ------------------------------
# Helper function: Convert weather code to icon and description
# ------------------------------
def weather_code_to_info(code):
    """Convert Open-Meteo weather code to icon and description"""
    code = int(code) if code is not None else 0
    if code == 0:
        return "☀️", "Clear sky"
    elif 1 <= code <= 3:
        return "⛅", "Mainly clear"
    elif 45 <= code <= 48:
        return "🌫️", "Fog"
    elif 51 <= code <= 55:
        return "🌦️", "Drizzle"
    elif 56 <= code <= 57:
        return "❄️🌧️", "Freezing drizzle"
    elif 61 <= code <= 65:
        return "🌧️", "Rain"
    elif 66 <= code <= 67:
        return "❄️🌧️", "Freezing rain"
    elif 71 <= code <= 77:
        return "❄️", "Snow fall"
    elif 80 <= code <= 82:
        return "🌩️🌧️", "Rain showers"
    elif 85 <= code <= 86:
        return "🌩️❄️", "Snow showers"
    elif 95 <= code <= 99:
        return "⛈️", "Thunderstorm"
    else:
        return "❓", "Unknown weather"

# ------------------------------
# Main application logic
# ------------------------------
def main():
    st.title("🌍 Global Weather Dashboard")
    st.subheader("Real-time & 7-Day Forecast (Powered by Open-Meteo API)")

    # Initialize session state for coordinates
    if 'lat' not in st.session_state:
        st.session_state.lat = 40.7128  # Default: New York latitude
    if 'lon' not in st.session_state:
        st.session_state.lon = -74.0060  # Default: New York longitude
    if 'location_name' not in st.session_state:
        st.session_state.location_name = "New York, USA"

    # Sidebar: Location selection
    with st.sidebar:
        st.header("📍 Select Location")
        selection_method = st.radio("Selection Method", 
                                   ["Click on Map", "Enter Coordinates"])

        if selection_method == "Enter Coordinates":
            st.subheader("Manual Coordinates")
            lat_input = st.number_input("Latitude", 
                                      min_value=-90.0, max_value=90.0, 
                                      value=st.session_state.lat, step=0.0001)
            lon_input = st.number_input("Longitude", 
                                      min_value=-180.0, max_value=180.0, 
                                      value=st.session_state.lon, step=0.0001)
            location_name = st.text_input("Location Name (optional)", 
                                         st.session_state.location_name)
            
            if st.button("Set Location", type="primary"):
                st.session_state.lat = lat_input
                st.session_state.lon = lon_input
                st.session_state.location_name = location_name if location_name else \
                                               f"Coordinates: {lat_input:.4f}, {lon_input:.4f}"
                st.success("Location updated successfully")

        st.markdown("---")
        st.info("""
        📡 Data Source: Open-Meteo Public API  
        🌐 Coverage: Global (any latitude/longitude)  
        ✨ Features:
        - Real-time weather metrics
        - 7-day detailed forecast
        - Hourly temperature & precipitation
        - Interactive global map
        """)

    # Interactive global map
    st.markdown("---")
    st.subheader("🌍 Interactive Map (Click to select location)")
    try:
        m = folium.Map(
            location=[st.session_state.lat, st.session_state.lon],
            zoom_start=3,
            tiles="CartoDB positron",
            width="100%",
            height="500px"
        )

        # Add click-to-select functionality
        m.add_child(folium.LatLngPopup())

        # Add marker for current location
        folium.Marker(
            location=[st.session_state.lat, st.session_state.lon],
            popup=f"<b>{st.session_state.location_name}</b><br>Lat: {st.session_state.lat:.4f}<br>Lon: {st.session_state.lon:.4f}",
            icon=folium.Icon(color="red", icon="map-marker", prefix="fa")
        ).add_to(m)

        # Display map and capture interactions
        map_response = st_folium(m, width=1200, height=500, returned_objects=["last_clicked"])

        # Update location if user clicks on map
        if map_response.get("last_clicked"):
            st.session_state.lat = map_response["last_clicked"]["lat"]
            st.session_state.lon = map_response["last_clicked"]["lng"]
            st.session_state.location_name = "Selected Location"
            st.experimental_rerun()

    except Exception as e:
        st.warning(f"Map could not be loaded: {str(e)}")

    # Fetch weather data for selected location
    st.markdown("---")
    with st.spinner(f"Fetching weather data for {st.session_state.location_name}..."):
        weather_data = get_weather_data(st.session_state.lat, st.session_state.lon)
    
    if not weather_data:
        st.stop()

    # Parse weather data
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    hourly = weather_data.get("hourly", {})
    timezone = weather_data.get("timezone", "UTC")

    # Display location info
    st.header(f"Current Location: {st.session_state.location_name}")
    st.caption(f"Coordinates: Lat {st.session_state.lat:.4f}, Lon {st.session_state.lon:.4f} | Timezone: {timezone}")

    # Current weather display
    st.subheader("Current Weather Conditions")
    current_time = datetime.fromisoformat(current.get("time", "2024-01-01T00:00")).strftime("%Y-%m-%d %H:%M")
    weather_icon, weather_desc = weather_code_to_info(current.get("weather_code"))
    day_night = "🌞 Day" if current.get("is_day") == 1 else "🌙 Night"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temperature", f"{current.get('temperature_2m', 0):.1f} °C")
        st.caption(f"{weather_icon} {weather_desc}")
    with col2:
        st.metric("Humidity", f"{current.get('relative_humidity_2m', 0)} %")
        st.caption(f"Last updated: {current_time}")
    with col3:
        st.metric("Wind Speed", f"{current.get('wind_speed_10m', 0):.1f} km/h")
    with col4:
        st.metric("Day/Night", day_night.split()[0])
        hourly_precip = [p for p in hourly.get("precipitation", [])[:24] if p > 0.1]
        precip_prob = f"{len(hourly_precip)/24*100:.0f}%" if hourly_precip else "0%"
        st.caption(f"🌧️ Precipitation chance: {precip_prob}")

    # Forecast tabs
    st.markdown("---")
    tab1, tab2 = st.tabs(["7-Day Forecast", "24-Hour Forecast"])

    with tab1:
        st.subheader("7-Day Weather Overview")
        dates = daily.get("time", [])
        dates = [datetime.fromisoformat(date).strftime("%m-%d (%a)") for date in dates] if dates else []
        
        daily_codes = daily.get("weather_code", [])
        daily_icons = [weather_code_to_info(code)[0] for code in daily_codes] if daily_codes else []

        df_daily = pd.DataFrame({
            "Date": dates,
            "Weather": daily_icons,
            "Max Temp (°C)": pd.Series(daily.get("temperature_2m_max", [])).round(1),
            "Min Temp (°C)": pd.Series(daily.get("temperature_2m_min", [])).round(1),
            "Rain (mm)": pd.Series(daily.get("rain_sum", [])).round(1),
            "Snow (mm)": pd.Series(daily.get("snowfall_sum", [])).round(1),
            "Sunshine (h)": pd.Series(daily.get("sunshine_duration", [])).round(1)
        })

        st.dataframe(df_daily, use_container_width=True, hide_index=True)

        if not df_daily.empty:
            st.subheader("Temperature Trend")
            st.line_chart(
                df_daily,
                x="Date",
                y=["Max Temp (°C)", "Min Temp (°C)"],
                use_container_width=True,
                color=["#ff6b6b", "#4ecdc4"]
            )

            st.subheader("Precipitation Forecast")
            st.bar_chart(
                df_daily,
                x="Date",
                y=["Rain (mm)", "Snow (mm)"],
                use_container_width=True,
                color=["#4a90e2", "#f5f5f5"]
            )
        else:
            st.info("No 7-day forecast data available")

    with tab2:
        st.subheader("Next 24-Hour Temperature")
        hours = hourly.get("time", [])[:24]
        hours = [datetime.fromisoformat(time).strftime("%H:%M") for time in hours] if hours else []
        
        df_hourly = pd.DataFrame({
            "Time": hours,
            "Temperature (°C)": pd.Series(hourly.get("temperature_2m", [])[:24]).round(1),
            "Precipitation (mm)": pd.Series(hourly.get("precipitation", [])[:24]).round(2)
        })

        if not df_hourly.empty:
            st.line_chart(
                df_hourly,
                x="Time",
                y="Temperature (°C)",
                use_container_width=True,
                color="#ff6b6b"
            )

            st.subheader("Next 24-Hour Precipitation")
            st.bar_chart(
                df_hourly,
                x="Time",
                y="Precipitation (mm)",
                use_container_width=True,
                color="#4a90e2"
            )
        else:
            st.info("No hourly forecast data available")

if __name__ == "__main__":
    main()
