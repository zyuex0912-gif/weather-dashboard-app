import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="MET博物馆藏品探索器",
    page_icon="🏛️",
    layout="wide"
)

# 隐藏默认样式（可选）
hide_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ------------------------------
# 核心函数：调用MET API获取数据
# ------------------------------
def get_met_departments():
    """获取博物馆所有部门列表"""
    url = "https://collectionapi.metmuseum.org/public/collection/v1/departments"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("departments", [])
    return []

def search_artworks(keyword, department_id=None, has_images=True, limit=50):
    """搜索艺术品（返回ID列表）"""
    url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
    params = {
        "q": keyword,
        "hasImages": "true" if has_images else "false",
        "departmentId": department_id if department_id else ""
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        # 关键修改：确保object_ids是列表（如果API返回None则设为空列表）
        object_ids = response.json().get("objectIDs", [])  # 这里将默认值设为[]
        # 只有当object_ids是列表时才切片
        if isinstance(object_ids, list):
            return object_ids[:limit]  # 限制返回数量
        else:
            return []  # 非列表类型时返回空列表
    return []  # API请求失败时返回空列表

def get_artwork_details(object_id):
    """获取单件艺术品的详细信息"""
    url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# ------------------------------
# 数据处理与可视化函数
# ------------------------------
def analyze_artwork_eras(artworks):
    """分析艺术品年代分布"""
    eras = []
    for art in artworks:
        date = art.get("objectDate", "未知")
        # 简单提取年份（处理格式如"1850-1860"或"19世纪"）
        if "-" in date and date[:4].isdigit():
            eras.append(date[:4])
        elif date.isdigit() and len(date) == 4:
            eras.append(date)
        else:
            eras.append("未知")
    
    # 统计年代分布
    era_counts = pd.Series(eras).value_counts().nlargest(10)
    return era_counts

def display_artwork_grid(artworks, cols=3):
    """网格展示艺术品"""
    columns = st.columns(cols)
    for i, art in enumerate(artworks):
        with columns[i % cols]:
            # 标题（过长截断）
            title = art.get("title", "无标题")
            st.subheader(title[:30] + "..." if len(title) > 30 else title)
            
            # 基本信息
            artist = art.get("artistDisplayName", "未知艺术家")
            st.write(f"**艺术家**：{artist}")
            
            date = art.get("objectDate", "未知年代")
            st.write(f"**年代**：{date}")
            
            # 图片
            image_url = art.get("primaryImage", "")
            if image_url:
                st.image(image_url, use_container_width=True, caption=f"ID: {art['objectID']}")
            else:
                st.warning("无图片可用")
            
            st.divider()

# ------------------------------
# 主应用逻辑
# ------------------------------
def main():
    st.title("🏛️ MET博物馆藏品探索器")
    st.write("基于大都会艺术博物馆公开API，探索全球艺术珍品")

    # 侧边栏：获取部门列表供筛选
    departments = get_met_departments()
    if departments:
        dept_options = {dept["displayName"]: dept["departmentId"] for dept in departments}
        dept_options["全部部门"] = None  # 增加"全部"选项
        selected_dept = st.sidebar.selectbox("选择部门", list(dept_options.keys()))
        selected_dept_id = dept_options[selected_dept]
    else:
        st.sidebar.warning("无法获取部门列表，将展示全部藏品")
        selected_dept_id = None

    # 主界面：搜索设置
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("搜索关键词（如画家、主题、流派）", "vangogh")
    with col2:
        max_results = st.slider("最大结果数", 5, 50, 15)

    # 搜索按钮
    if st.button("开始搜索", key="search_btn"):
        if not keyword.strip():
            st.warning("请输入搜索关键词")
            return

        with st.spinner("正在从MET博物馆获取数据..."):
            # 1. 搜索艺术品ID
            artwork_ids = search_artworks(
                keyword=keyword,
                department_id=selected_dept_id,
                has_images=True,
                limit=max_results
            )

            if not artwork_ids:
                st.info("未找到匹配的艺术品，请尝试其他关键词或部门")
                return

            st.success(f"找到 {len(artwork_ids)} 件符合条件的艺术品")

            # 2. 获取每件艺术品的详细信息
            artworks = []
            progress_bar = st.progress(0)
            for i, obj_id in enumerate(artwork_ids):
                details = get_artwork_details(obj_id)
                if details:
                    artworks.append(details)
                progress_bar.progress((i + 1) / len(artwork_ids))

            if not artworks:
                st.error("无法获取艺术品详细信息")
                return

            # 3. 展示艺术品网格
            st.subheader("🖼️ 艺术品展示")
            display_artwork_grid(artworks, cols=3)

            # 4. 简单数据分析
            st.subheader("📊 年代分布分析")
            era_counts = analyze_artwork_eras(artworks)
            if not era_counts.empty:
                fig, ax = plt.subplots(figsize=(10, 5))
                era_counts.plot(kind="bar", ax=ax, color="#8B4513")
                ax.set_title("艺术品年代分布（前10位）")
                ax.set_xlabel("年代")
                ax.set_ylabel("数量")
                st.pyplot(fig)
            else:
                st.info("无法分析年代分布（数据不足）")

            # 5. 导出数据（可选）
            if st.button("导出数据为CSV"):
                # 提取关键字段生成DataFrame
                export_data = []
                for art in artworks:
                    export_data.append({
                        "ID": art.get("objectID"),
                        "标题": art.get("title"),
                        "艺术家": art.get("artistDisplayName"),
                        "年代": art.get("objectDate"),
                        "分类": art.get("classification"),
                        "图片URL": art.get("primaryImage")
                    })
                df = pd.DataFrame(export_data)
                st.download_button(
                    label="下载CSV",
                    data=df.to_csv(index=False),
                    file_name=f"met_artworks_{keyword}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

    # 侧边栏说明
    st.sidebar.markdown("---")
    st.sidebar.info("""
    数据来源：纽约大都会艺术博物馆公开API  
    功能说明：  
    1. 可按关键词和部门筛选艺术品  
    2. 展示艺术品图片及基本信息  
    3. 分析年代分布并支持数据导出  
    """)

if __name__ == "__main__":
    main()
