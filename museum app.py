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
    search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
    params = {
        "q": keyword.strip(),
        "hasImages": "true",
        "isHighlight": "false"
    }

    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        object_ids = data.get("objectIDs", [])
        if not isinstance(object_ids, list):
            return []

        artworks = []
        for obj_id in object_ids[:12]:
            detail_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
            try:
                detail_res = requests.get(detail_url, timeout=8)
                detail_res.raise_for_status()
                detail = detail_res.json()

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
                continue

        return artworks

    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

# ------------------------------
# 页面UI（兼容所有Streamlit版本）
# ------------------------------
st.title("🎨 Explore MET Artworks")
st.subheader("Search for artworks from the Metropolitan Museum of Art")

keyword = st.text_input("Enter keyword (e.g., flower, cat, Chinese figure with bird)", "")

if st.button("Search", type="primary"):
    if not keyword:
        st.warning("Please enter a valid keyword!")
    else:
        with st.spinner("Searching artworks..."):
            artworks = search_met_artworks(keyword)

            if artworks:
                cols = st.columns(2)
                for i, art in enumerate(artworks):
                    with cols[i % 2]:
                        # 兼容版卡片：用 container + border 模拟
                        card = st.container(border=True)
                        with card:
                            title = art['title'][:25] + "..." if len(art['title']) > 25 else art['title']
                            st.markdown(f"### {title}")
                            st.markdown(f"**Artist**: {art['artist']}")
                            st.markdown(f"**Date**: {art['date']}")
                            st.image(art["image_url"], use_container_width=True)
            else:
                st.info(f"No artworks found for '{keyword}'. Try other keywords like 'flower' or 'Chinese figure with bird'!")

st.markdown("---")
st.caption("Data source: Metropolitan Museum of Art Open API | No API key required")
