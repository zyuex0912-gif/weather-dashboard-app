import streamlit as st
import requests

# 页面配置（和参考链接风格一致）
st.set_page_config(
    page_title="MET Artwork Explorer",
    page_icon="🎨",
    layout="centered"  # 居中布局，贴合参考链接
)

# 隐藏默认样式，更简洁
hide_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ------------------------------
# 核心函数：确保API请求稳定且返回有效结果
# ------------------------------
def search_met_artworks(keyword):
    """调用MET API搜索艺术品，返回带图片的有效结果"""
    # 1. MET API搜索端点（官方推荐，确保参数正确）
    search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
    params = {
        "q": keyword.strip(),  # 去除关键词前后空格（避免空字符搜索）
        "hasImages": "true",   # 强制只返回有图片的结果（和参考链接一致）
        "isHighlight": "false" # 不限制高亮作品，扩大搜索范围
    }

    try:
        # 2. 发送请求（添加超时处理，避免卡顿时无响应）
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()  # 触发HTTP错误（如404、500）
        data = response.json()

        # 3. 提取有效艺术品ID（处理API返回None的情况）
        object_ids = data.get("objectIDs", [])
        if not isinstance(object_ids, list):
            return []

        # 4. 批量获取艺术品详情（只保留有图片和核心信息的结果）
        artworks = []
        for obj_id in object_ids[:12]:  # 限制12个结果，避免加载过慢
            detail_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
            try:
                detail_res = requests.get(detail_url, timeout=8)
                detail_res.raise_for_status()
                detail = detail_res.json()

                # 过滤无效数据：必须有图片、标题、艺术家
                if (detail.get("primaryImage") and 
                    detail.get("title") and 
                    detail.get("artistDisplayName")):
                    artworks.append({
                        "id": obj_id,
                        "title": detail["title"],
                        "artist": detail["artistDisplayName"],
                        "date": detail.get("objectDate", "Unknown"),
                        "image_url": detail["primaryImage"]
                    })
            except:
                continue  # 跳过单个作品获取失败的情况

        return artworks

    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

# ------------------------------
# 页面UI（完全贴合参考链接）
# ------------------------------
st.title("🎨 Explore MET Artworks")
st.subheader("Search for artworks from the Metropolitan Museum of Art")

# 搜索框（居中显示，和参考链接一致）
keyword = st.text_input("Enter keyword (e.g., flower, cat, Chinese figure with bird)", "")

# 搜索按钮
if st.button("Search", type="primary"):  # 主按钮，更醒目
    if not keyword:
        st.warning("Please enter a valid keyword!")
    else:
        with st.spinner("Searching artworks..."):
            artworks = search_met_artworks(keyword)

            if artworks:
                # 卡片式展示（2列布局，贴合参考链接）
                cols = st.columns(2)
                for i, art in enumerate(artworks):
                    with cols[i % 2]:
                        # 艺术品卡片
                        st.card(
                            f"""
                            ### {art['title'][:25]}... if len(art['title'])>25 else art['title']
                            **Artist**: {art['artist']}
                            **Date**: {art['date']}
                            """
                        )
                        # 显示图片（自适应宽度）
                        st.image(art["image_url"], use_container_width=True)
            else:
                # 无结果时友好提示（而非空白）
                st.info(f"No artworks found for '{keyword}'. Try other keywords like 'flower' or 'Chinese figure with bird'!")

# 底部说明（和参考链接一致，增加可信度）
st.markdown("---")
st.caption("Data source: Metropolitan Museum of Art Open API | No API key required")
