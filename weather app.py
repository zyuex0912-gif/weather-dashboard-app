import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

# 页面配置（贴合参考链接简洁风格）
st.set_page_config(
    page_title="Open-Meteo Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# 隐藏默认样式，优化视觉
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
# 核心配置：城市列表（含经纬度，可自由扩展）
# ------------------------------
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

# ------------------------------
# 核心函数：调用 Open-Meteo 公开 API 获取天气数据
# ------------------------------
def get_openmeteo_weather(lat, lon):
    """
    调用 Open-Meteo 公开 API（无需 API Key）
    文档参考：https://open-meteo.com/en/docs
    """
    # Open-Meteo 官方 API 端点
    api_url = "https://api.open-meteo.com/v1/forecast"
    
    # API 参数（严格遵循 Open-Meteo 文档规范）
    params = {
        "latitude": lat,               # 城市纬度
        "longitude": lon,              # 城市经度
        "current": [                   # 实时天气字段
            "temperature_2m",          # 2米处温度
            "relative_humidity_2m",    # 2米处相对湿度
            "wind_speed_10m",          # 10米处风速
            "weather_code",            # 天气代码（用于转换图标）
            "is_day"                   # 是否白天
        ],
        "daily": [                     # 每日预报字段
            "weather_code",
            "temperature_2m_max",      # 日最高温
            "temperature_2m_min",      # 日最低温
            "rain_sum",                # 日降雨量
            "snowfall_sum",            # 日降雪量
            "sunshine_duration"        # 日照时长
        ],
        "hourly": [                    # 每小时预报字段
            "temperature_2m",
            "precipitation"            # 每小时降水量
        ],
        "timezone": "auto",            # 自动适配时区
        "forecast_days": 7,            # 预报7天
        "hourly_steps": 1,             # 每小时1条数据
        "models": "best_match"         # 使用最优模型数据
    }

    try:
        # 发送 GET 请求（符合 Open-Meteo API 要求）
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()  # 触发 HTTP 错误（如 400/500）
        
        # 解析 JSON 响应（Open-Meteo 标准返回格式）
        weather_data = response.json()
        return weather_data

    except requests.exceptions.Timeout:
        st.error("Error: Connection timed out. Please try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Request failed: {str(e)}")
        return None

# ------------------------------
# 辅助函数：Open-Meteo 天气代码转图标/描述
# ------------------------------
def weather_code_to_info(code):
    """根据 Open-Meteo 官方天气代码定义，转换为图标和描述"""
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
# 主页面逻辑
# ------------------------------
def main():
    st.title("🌤️ Open-Meteo Interactive Weather Dashboard")
    st.subheader("Real-time & 7-Day Forecast (Powered by Open-Meteo Open API)")

    # 1. 侧边栏：城市选择
    with st.sidebar:
        st.header("📍 Select Location")
        selected_city = st.selectbox("Choose a city", list(CITIES.keys()))
        city_info = CITIES[selected_city]
        lat, lon = city_info["lat"], city_info["lon"]

        # 显示城市经纬度（Open-Meteo API 依赖参数，透明化展示）
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

    # 2. 调用 Open-Meteo API 获取数据
    st.markdown("---")
    with st.spinner("Fetching data from Open-Meteo API..."):
        weather_data = get_openmeteo_weather(lat, lon)
    
    if not weather_data:
        st.stop()  # 数据获取失败则停止执行

    # 3. 解析 API 返回数据（严格对应 Open-Meteo 响应结构）
    current = weather_data["current"]
    daily = weather_data["daily"]
    hourly = weather_data["hourly"]
    timezone = weather_data["timezone"]

    # 4. 实时天气展示（顶部核心指标）
    st.header(f"Current Weather - {selected_city.split(' ')[0]}")
    current_time = datetime.fromisoformat(current["time"]).strftime("%Y-%m-%d %H:%M")
    weather_icon, weather_desc = weather_code_to_info(current["weather_code"])
    day_night = "🌞 Day" if current["is_day"] == 1 else "🌙 Night"

    # 4列布局展示核心指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temperature", f"{current['temperature_2m']:.1f} °C", icon=weather_icon)
        st.caption(f"Weather: {weather_desc}")
    with col2:
        st.metric("Humidity", f"{current['relative_humidity_2m']} %", icon="💧")
        st.caption(f"Timezone: {timezone}")
    with col3:
        st.metric("Wind Speed", f"{current['wind_speed_10m']:.1f} km/h", icon="💨")
        st.caption(f"Updated: {current_time}")
    with col4:
        st.metric("Day/Night", day_night, icon=day_night.split()[0])
        # 今日降水概率（基于每小时数据计算）
        hourly_precip = [p for p in hourly["precipitation"][:24] if p > 0.1]
        precip_prob = f"{len(hourly_precip)/24*100:.0f}%" if hourly_precip else "0%"
        st.caption(f"Precipitation Chance: {precip_prob}")

    # 5. 交互式地图（标记城市位置）
    st.markdown("---")
    st.subheader("Location Map")
    m = folium.Map(location=[lat, lon], zoom_start=10, tiles="OpenStreetMap")
    folium.Marker(
        location=[lat, lon],
        popup=f"{selected_city}\nLat: {lat:.4f}, Lon: {lon:.4f}",
        icon=folium.Icon(color="blue", icon="cloud", prefix="fa")
    ).add_to(m)
    st_folium(m, width=1200, height=300, returned_objects=[])

    # 6. 预报图表（标签页切换）
    st.markdown("---")
    tab1, tab2 = st.tabs(["7-Day Forecast", "24-Hour Forecast"])

    with tab1:
        # 7天预报表格
        st.subheader("7-Day Weather Overview")
        dates = [datetime.fromisoformat(date).strftime("%m-%d (%a)") for date in daily["time"]]
        daily_icons = [weather_code_to_info(code)[0] for code in daily["weather_code"]]

        df_daily = pd.DataFrame({
            "Date": dates,
            "Weather": daily_icons,
            "Max Temp (°C)": daily["temperature_2m_max"].round(1),
            "Min Temp (°C)": daily["temperature_2m_min"].round(1),
            "Rain (mm)": daily["rain_sum"].round(1),
            "Snow (mm)": daily["snowfall_sum"].round(1),
            "Sunshine (h)": daily["sunshine_duration"].round(1)
        })

        st.dataframe(df_daily, use_container_width=True, hide_index=True)

        # 温度趋势图
        st.subheader("Temperature Trend")
        st.line_chart(
            df_daily,
            x="Date",
            y=["Max Temp (°C)", "Min Temp (°C)"],
            use_container_width=True,
            color=["#ff6b6b", "#4ecdc4"]
        )

        # 降水/降雪柱状图
        st.subheader("Rain & Snow Forecast")
        st.bar_chart(
            df_daily,
            x="Date",
            y=["Rain (mm)", "Snow (mm)"],
            use_container_width=True,
            color=["#4a90e2", "#f5f5f5"]
        )

    with tab2:
        # 24小时温度和降水
        st.subheader("Next 24-Hour Temperature")
        hours = [datetime.fromisoformat(time).strftime("%H:%M") for time in hourly["time"][:24]]
        df_hourly = pd.DataFrame({
            "Time": hours,
            "Temperature (°C)": hourly["temperature_2m"][:24].round(1),
            "Precipitation (mm)": hourly["precipitation"][:24].round(2)
        })

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

if __name__ == "__main__":
    main()
