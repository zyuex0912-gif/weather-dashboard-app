import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# 页面配置（简洁风格，保留地图功能）
st.set_page_config(
    page_title="Open-Meteo Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# 隐藏默认样式
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

# 核心配置：城市列表
CITIES = {
    "Beijing (China)": {"lat": 39.9042, "lon": 116.4074},
    "Shanghai (China)": {"lat": 31.2304, "lon": 121.4737},
    "Guangzhou (China)": {"lat": 23.1200, "lon": 113.2500},
    "New York (USA)": {"lat": 40.7128, "lon": -74.0060},
    "London (UK)": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo (Japan)": {"lat": 35.6762, "lon": 139.6503},
    "Seoul (Korea)": {"lat": 37.5665, "lon": 126.9780},
    "Paris (France)": {"lat": 48.8566, "lon": 2.3522},
    "Sydney (Australia)": {"lat": -33.8688, "lon": 151.2093},
    "Berlin (Germany)": {"lat": 52.5200, "lon": 13.4050}
}

# 核心函数：调用 Open-Meteo API
def get_openmeteo_weather(lat, lon):
    api_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code", "is_day"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "rain_sum", "snowfall_sum", "sunshine_duration"],
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
        st.error("Error: Connection timed out. Please try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Request failed: {str(e)}")
        return None

# 天气代码转图标/描述
def weather_code_to_info(code):
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

# 主页面逻辑
def main():
    st.title("🌤️ Open-Meteo Interactive Weather Dashboard")
    st.subheader("Real-time & 7-Day Forecast (Powered by Open-Meteo Open API)")

    # 侧边栏：城市选择
    with st.sidebar:
        st.header("📍 Select Location")
        selected_city = st.selectbox("Choose a city", list(CITIES.keys()))
        city_info = CITIES[selected_city]
        lat, lon = city_info["lat"], city_info["lon"]

        st.markdown(f"**Latitude**: {lat:.4f}")
        st.markdown(f"**Longitude**: {lon:.4f}")

        st.markdown("---")
        st.info(f"""
        📡 Data Source: Open-Meteo Open API  
        📋 API Endpoint: https://api.open-meteo.com/v1/forecast  
        ✨ Features:
        - Real-time weather metrics
        - 7-day detailed forecast
        - Hourly temperature/precipitation
        - Interactive location map
        """)

    # 获取天气数据
    st.markdown("---")
    with st.spinner("Fetching data from Open-Meteo API..."):
        weather_data = get_openmeteo_weather(lat, lon)
    
    if not weather_data:
        st.stop()

    # 解析数据（增加空值判断，避免键不存在报错）
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    hourly = weather_data.get("hourly", {})
    timezone = weather_data.get("timezone", "UTC")

    # 实时天气展示
    st.header(f"Current Weather - {selected_city.split(' ')[0]}")
    current_time = datetime.fromisoformat(current.get("time", "2024-01-01T00:00")).strftime("%Y-%m-%d %H:%M")
    weather_icon, weather_desc = weather_code_to_info(current.get("weather_code"))
    day_night = "🌞 Day" if current.get("is_day") == 1 else "🌙 Night"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temperature", f"{current.get('temperature_2m', 0):.1f} °C")
        st.caption(f"{weather_icon} Weather: {weather_desc}")
    with col2:
        st.metric("Humidity", f"{current.get('relative_humidity_2m', 0)} %")
        st.caption(f"Timezone: {timezone}")
    with col3:
        st.metric("Wind Speed", f"{current.get('wind_speed_10m', 0):.1f} km/h")
        st.caption(f"Updated: {current_time}")
    with col4:
        st.metric("Day/Night", day_night.split()[0])
        hourly_precip = [p for p in hourly.get("precipitation", [])[:24] if p > 0.1]
        precip_prob = f"{len(hourly_precip)/24*100:.0f}%" if hourly_precip else "0%"
        st.caption(f"🌧️ Precipitation Chance: {precip_prob}")

    # ------------------------------
    # 恢复地图功能（兼容所有版本）
    # ------------------------------
    st.markdown("---")
    st.subheader("📍 Location Map")
    try:
        # 创建地图（使用 OpenStreetMap 瓦片，加载稳定）
        m = folium.Map(
            location=[lat, lon],
            zoom_start=10,
            tiles="OpenStreetMap",
            width="100%",
            height="300px"
        )
        # 添加城市标记
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>{selected_city}</b><br>Lat: {lat:.4f}<br>Lon: {lon:.4f}",
            icon=folium.Icon(color="blue", icon="cloud", prefix="fa")
        ).add_to(m)
        # 在 Streamlit 中渲染地图
        st_folium(m, width=1200, height=300, returned_objects=[])
    except Exception as e:
        # 地图加载失败时友好提示，不影响整体功能
        st.warning(f"Map could not be loaded: {str(e)}")

    # 预报图表
    st.markdown("---")
    tab1, tab2 = st.tabs(["7-Day Forecast", "24-Hour Forecast"])

    with tab1:
        st.subheader("7-Day Weather Overview")
        dates = daily.get("time", [])
        dates = [datetime.fromisoformat(date).strftime("%m-%d (%a)") for date in dates] if dates else []
        
        daily_codes = daily.get("weather_code", [])
        daily_icons = [weather_code_to_info(code)[0] for code in daily_codes] if daily_codes else []

        # 数据类型修复：转 Series 后 round
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

            st.subheader("Rain & Snow Forecast")
            st.bar_chart(
                df_daily,
                x="Date",
                y=["Rain (mm)", "Snow (mm)"],
                use_container_width=True,
                color=["#4a90e2", "#f5f5f5"]
            )
        else:
            st.info("No 7-day forecast data available.")

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
            st.info("No hourly forecast data available.")

if __name__ == "__main__":
    main()
