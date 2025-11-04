import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Open-Meteo Interactive Weather Dashboard",
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
# Core function: Fetch data from Open-Meteo API (with coordinate validation)
# ------------------------------
def get_weather_data(lat, lon):
    """Retrieve weather data with strict coordinate validation"""
    # Step 1: Validate coordinate range (fix invalid values automatically)
    lat = max(-90.0, min(90.0, lat))  # Force latitude between -90 and 90
    lon = max(-180.0, min(180.0, lon))  # Force longitude between -180 and 180

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
# Helper function: Clean and validate map click coordinates
# ------------------------------
def clean_coordinates(lat, lon):
    """Clean and validate coordinates from map click"""
    # Fix latitude (must be -90 to 90)
    lat = float(lat)
    if lat < -90:
        lat = -90.0
    elif lat > 90:
        lat = 90.0

    # Fix longitude (must be -180 to 180)
    lon = float(lon)
    while lon < -180:
        lon += 360
    while lon > 180:
        lon -= 360

    return lat, lon

# ------------------------------
# Main application logic
# ------------------------------
def main():
    st.title("🌍 Open-Meteo Interactive Weather Dashboard")
    st.subheader("Real-time & 7-Day Forecast (Powered by Open-Meteo API)")

    # Initialize session state with valid default (New York)
    if 'lat' not in st.session_state:
        st.session_state.lat = 40.7128  # Valid latitude
    if 'lon' not in st.session_state:
        st.session_state.lon = -74.0060  # Valid longitude
    if 'location_name' not in st.session_state:
        st.session_state.location_name = "New York, USA"

    # Sidebar: Location selection
    with st.sidebar:
        st.header("📍 Select Location")
        selection_method = st.radio("Selection Method", 
                                   ["Click on Map", "Enter Coordinates"])

        if selection_method == "Enter Coordinates":
            st.subheader("Manual Coordinates")
            st.caption("Valid range: Latitude (-90 to 90), Longitude (-180 to 180)")
            # Force valid range in input (user can't enter invalid values)
            lat_input = st.number_input("Latitude", 
                                      min_value=-90.0, max_value=90.0,
                                      value=st.session_state.lat, step=0.0001,
                                      format="%.4f")
            lon_input = st.number_input("Longitude", 
                                      min_value=-180.0, max_value=180.0,
                                      value=st.session_state.lon, step=0.0001,
                                      format="%.4f")
            location_name = st.text_input("Location Name (optional)", 
                                         st.session_state.location_name)
            
            if st.button("Set Location", type="primary"):
                # Clean coordinates even if input is valid (double safety)
                clean_lat, clean_lon = clean_coordinates(lat_input, lon_input)
                st.session_state.lat = clean_lat
                st.session_state.lon = clean_lon
                st.session_state.location_name = location_name if location_name else \
                                               f"Coordinates: {clean_lat:.4f}, {clean_lon:.4f}"
                st.success("Location updated successfully")

        st.markdown("---")
        st.info("""
        📡 Data Source: Open-Meteo Public API  
        🌐 Coverage: Global (any valid latitude/longitude)  
        ✨ Features:
        - Real-time weather metrics
        - 7-day detailed forecast
        - Hourly temperature & precipitation
        - Interactive global map
        """)

    # ------------------------------
    # Optimized Interactive Map (fixed click issues)
    # ------------------------------
    st.markdown("---")
    st.subheader(" Interactive Map")
    st.caption("Drag to pan | Click to select location")
    try:
        # Create map with optimized settings (prevent invalid clicks)
        m = folium.Map(
            location=[st.session_state.lat, st.session_state.lon],
            zoom_start=2,  # Start with world view (harder to get invalid coordinates)
            min_zoom=1,    # Prevent over-zooming out (causes coordinate errors)
            max_zoom=16,   # Prevent over-zooming in (unnecessary for weather data)
            tiles="CartoDB positron",
            width="100%",
            height="500px",
            # Disable extreme panning (keep map within Earth bounds)
            max_bounds=True,
            max_bounds_extend=False
        )

        # Add click-to-select (only returns valid Earth coordinates)
        m.add_child(folium.LatLngPopup())

        # Add marker for current location (red dot, easy to see)
        folium.Marker(
            location=[st.session_state.lat, st.session_state.lon],
            popup=f"<b>{st.session_state.location_name}</b><br>Lat: {st.session_state.lat:.4f}<br>Lon: {st.session_state.lon:.4f}",
            icon=folium.Icon(color="red", icon="map-marker", prefix="fa", size=(10, 10))
        ).add_to(m)

        # Add world boundaries (optional: help user see valid areas)
        folium.GeoJson(
            data="https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json",
            style_function=lambda x: {"fillColor": "#f0f0f0", "color": "#cccccc", "weight": 1}
        ).add_to(m)

        # Display map and capture interactions
        map_response = st_folium(m, width=1200, height=500, returned_objects=["last_clicked"])

        # Update location only if click is valid (not None)
        if map_response.get("last_clicked"):
            # Clean and validate click coordinates (fixes invalid values)
            clicked_lat = map_response["last_clicked"]["lat"]
            clicked_lon = map_response["last_clicked"]["lng"]
            clean_lat, clean_lon = clean_coordinates(clicked_lat, clicked_lon)
            
            # Update session state with valid coordinates
            st.session_state.lat = clean_lat
            st.session_state.lon = clean_lon
            st.session_state.location_name = f"Selected Location ({clean_lat:.4f}, {clean_lon:.4f})"
            
            # Refresh page to show new location data
            st.rerun()

    except Exception as e:
        st.warning(f"Map could not be loaded: {str(e)}")
        st.info("Try refreshing the page or selecting location via coordinates.")

    # Fetch weather data for valid coordinates
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
