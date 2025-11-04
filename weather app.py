import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium, folium_static
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="全球天气查询仪表盘",
    page_icon="🌍",
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

# ------------------------------
# 核心函数：调用 Open-Meteo API（支持全球任意经纬度）
# ------------------------------
def get_global_weather(lat, lon):
    api_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code", "is_day"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "rain_sum", "snowfall_sum", "sunshine_duration"],
        "hourly": ["temperature_2m", "precipitation"],
        "timezone": "auto",  # 自动适配当地时区
        "forecast_days": 7,
        "hourly_steps": 1
    }

    try:
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("连接超时，请稍后重试")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API请求失败：{str(e)}")
        return None

# 天气代码转图标/描述（中英文对照）
def weather_code_to_info(code):
    code = int(code) if code is not None else 0
    if code == 0:
        return "☀️", "晴空 (Clear sky)"
    elif 1 <= code <= 3:
        return "⛅", "多云 (Mainly clear)"
    elif 45 <= code <= 48:
        return "🌫️", "雾 (Fog)"
    elif 51 <= code <= 55:
        return "🌦️", "毛毛雨 (Drizzle)"
    elif 56 <= code <= 57:
        return "❄️🌧️", "冻雨 (Freezing drizzle)"
    elif 61 <= code <= 65:
        return "🌧️", "下雨 (Rain)"
    elif 66 <= code <= 67:
        return "❄️🌧️", "冻雨 (Freezing rain)"
    elif 71 <= code <= 77:
        return "❄️", "下雪 (Snow fall)"
    elif 80 <= code <= 82:
        return "🌩️🌧️", "阵雨 (Rain showers)"
    elif 85 <= code <= 86:
        return "🌩️❄️", "阵雪 (Snow showers)"
    elif 95 <= code <= 99:
        return "⛈️", "雷暴 (Thunderstorm)"
    else:
        return "❓", "未知天气 (Unknown)"

# ------------------------------
# 主页面逻辑（支持全球任意地点）
# ------------------------------
def main():
    st.title("🌍 全球天气查询仪表盘")
    st.subheader("支持任意地点的实时天气与7天预报（基于Open-Meteo API）")

    # 初始化坐标（默认北京，可修改为任意地点）
    if 'lat' not in st.session_state:
        st.session_state.lat = 39.9042  # 默认纬度
    if 'lon' not in st.session_state:
        st.session_state.lon = 116.4074  # 默认经度
    if 'location_name' not in st.session_state:
        st.session_state.location_name = "北京市 (Beijing)"  # 默认地点名称

    # 侧边栏：位置选择方式（地图点击/手动输入）
    with st.sidebar:
        st.header("📍 选择查询位置")
        select_method = st.radio("选择方式", ["地图点击选择", "手动输入经纬度"])

        if select_method == "手动输入经纬度":
            # 手动输入经纬度（支持全球范围）
            st.subheader("经纬度输入")
            lat_input = st.number_input("纬度 (Latitude)", 
                                      min_value=-90.0, max_value=90.0, 
                                      value=st.session_state.lat, step=0.0001)
            lon_input = st.number_input("经度 (Longitude)", 
                                      min_value=-180.0, max_value=180.0, 
                                      value=st.session_state.lon, step=0.0001)
            location_name = st.text_input("地点名称（可选）", st.session_state.location_name)
            
            if st.button("确认位置", type="primary"):
                st.session_state.lat = lat_input
                st.session_state.lon = lon_input
                st.session_state.location_name = location_name if location_name else f"坐标: {lat_input:.4f}, {lon_input:.4f}"
                st.success("位置已更新")

        st.markdown("---")
        st.info(f"""
        📡 数据来源：Open-Meteo 全球公开API  
        🌐 支持范围：全球任意经纬度（-90°至90°纬度，-180°至180°经度）  
        ✨ 功能：
        - 实时天气指标
        - 7天详细预报
        - 小时级温度与降水
        - 交互式全球地图
        """)

    # 主地图：支持点击选择全球任意地点
    st.markdown("---")
    st.subheader("🌍 全球地图（点击任意位置查询天气）")
    try:
        # 创建全球地图（初始显示世界地图）
        m = folium.Map(
            location=[st.session_state.lat, st.session_state.lon],
            zoom_start=3,  # 初始缩放级别（3级可显示大洲）
            tiles="CartoDB positron",  # 浅色地图更清晰
            width="100%",
            height="500px"
        )

        # 添加点击交互：获取点击位置的经纬度
        m.add_child(folium.LatLngPopup())

        # 添加当前选中位置的标记
        folium.Marker(
            location=[st.session_state.lat, st.session_state.lon],
            popup=f"<b>{st.session_state.location_name}</b><br>Lat: {st.session_state.lat:.4f}<br>Lon: {st.session_state.lon:.4f}",
            icon=folium.Icon(color="red", icon="map-marker", prefix="fa")
        ).add_to(m)

        # 显示地图并捕获点击事件
        map_data = st_folium(m, width=1200, height=500, returned_objects=["last_clicked"])

        # 如果用户点击了地图，更新坐标
        if map_data.get("last_clicked"):
            st.session_state.lat = map_data["last_clicked"]["lat"]
            st.session_state.lon = map_data["last_clicked"]["lng"]
            st.session_state.location_name = f"点击位置 (Clicked Location)"
            st.experimental_rerun()  # 刷新页面生效

    except Exception as e:
        st.warning(f"地图加载失败：{str(e)}")

    # 获取选中位置的天气数据
    st.markdown("---")
    with st.spinner(f"正在获取 {st.session_state.location_name} 的天气数据..."):
        weather_data = get_global_weather(st.session_state.lat, st.session_state.lon)
    
    if not weather_data:
        st.stop()

    # 解析天气数据
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    hourly = weather_data.get("hourly", {})
    timezone = weather_data.get("timezone", "UTC")

    # 显示当前位置信息
    st.header(f"当前位置：{st.session_state.location_name}")
    st.caption(f"坐标：纬度 {st.session_state.lat:.4f}，经度 {st.session_state.lon:.4f} | 时区：{timezone}")

    # 实时天气展示
    st.subheader("实时天气状况")
    current_time = datetime.fromisoformat(current.get("time", "2024-01-01T00:00")).strftime("%Y-%m-%d %H:%M")
    weather_icon, weather_desc = weather_code_to_info(current.get("weather_code"))
    day_night = "🌞 白天 (Day)" if current.get("is_day") == 1 else "🌙 夜间 (Night)"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("温度 (Temperature)", f"{current.get('temperature_2m', 0):.1f} °C")
        st.caption(f"{weather_icon} {weather_desc}")
    with col2:
        st.metric("湿度 (Humidity)", f"{current.get('relative_humidity_2m', 0)} %")
        st.caption(f"更新时间 (Updated): {current_time}")
    with col3:
        st.metric("风速 (Wind Speed)", f"{current.get('wind_speed_10m', 0):.1f} km/h")
    with col4:
        st.metric("昼夜 (Day/Night)", day_night.split()[0])
        hourly_precip = [p for p in hourly.get("precipitation", [])[:24] if p > 0.1]
        precip_prob = f"{len(hourly_precip)/24*100:.0f}%" if hourly_precip else "0%"
        st.caption(f"🌧️ 降水概率 (Chance): {precip_prob}")

    # 预报图表
    st.markdown("---")
    tab1, tab2 = st.tabs(["7天预报 (7-Day Forecast)", "24小时预报 (24-Hour Forecast)"])

    with tab1:
        st.subheader("7天天气概况")
        dates = daily.get("time", [])
        dates = [datetime.fromisoformat(date).strftime("%m-%d（%a）") for date in dates] if dates else []
        
        daily_codes = daily.get("weather_code", [])
        daily_icons = [weather_code_to_info(code)[0] for code in daily_codes] if daily_codes else []

        df_daily = pd.DataFrame({
            "日期 (Date)": dates,
            "天气 (Weather)": daily_icons,
            "最高温 (Max Temp)": pd.Series(daily.get("temperature_2m_max", [])).round(1),
            "最低温 (Min Temp)": pd.Series(daily.get("temperature_2m_min", [])).round(1),
            "降雨量 (Rain)": pd.Series(daily.get("rain_sum", [])).round(1),
            "降雪量 (Snow)": pd.Series(daily.get("snowfall_sum", [])).round(1),
            "日照时长 (Sunshine)": pd.Series(daily.get("sunshine_duration", [])).round(1)
        })

        st.dataframe(df_daily, use_container_width=True, hide_index=True)

        if not df_daily.empty:
            st.subheader("温度趋势 (Temperature Trend)")
            st.line_chart(
                df_daily,
                x="日期 (Date)",
                y=["最高温 (Max Temp)", "最低温 (Min Temp)"],
                use_container_width=True,
                color=["#ff6b6b", "#4ecdc4"]
            )

            st.subheader("降水预报 (Precipitation Forecast)")
            st.bar_chart(
                df_daily,
                x="日期 (Date)",
                y=["降雨量 (Rain)", "降雪量 (Snow)"],
                use_container_width=True,
                color=["#4a90e2", "#f5f5f5"]
            )
        else:
            st.info("暂无7天预报数据 (No 7-day forecast data available)")

    with tab2:
        st.subheader("未来24小时温度 (Next 24-Hour Temperature)")
        hours = hourly.get("time", [])[:24]
        hours = [datetime.fromisoformat(time).strftime("%H:%M") for time in hours] if hours else []
        
        df_hourly = pd.DataFrame({
            "时间 (Time)": hours,
            "温度 (Temperature)": pd.Series(hourly.get("temperature_2m", [])[:24]).round(1),
            "降水量 (Precipitation)": pd.Series(hourly.get("precipitation", [])[:24]).round(2)
        })

        if not df_hourly.empty:
            st.line_chart(
                df_hourly,
                x="时间 (Time)",
                y="温度 (Temperature)",
                use_container_width=True,
                color="#ff6b6b"
            )

            st.subheader("未来24小时降水量 (Next 24-Hour Precipitation)")
            st.bar_chart(
                df_hourly,
                x="时间 (Time)",
                y="降水量 (Precipitation)",
                use_container_width=True,
                color="#4a90e2"
            )
        else:
            st.info("暂无小时级预报数据 (No hourly forecast data available)")

if __name__ == "__main__":
    main()
