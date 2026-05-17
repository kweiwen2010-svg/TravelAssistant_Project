import streamlit as st
import pandas as pd
import folium
from datetime import datetime, timedelta
from streamlit_folium import st_folium
from core.mapper import DataMapper
# 確保這行對應到上面的檔案與類別名稱
from core.brain_25 import TravelBrain

st.set_page_config(page_title="全球智慧旅遊助手 2.5", layout="wide")

def main():
    st.title("🌏 全球自助旅行 AI 助理 (預算試算版)")

    if "itinerary" not in st.session_state:
        st.session_state.itinerary = None
    if "maps_data" not in st.session_state:
        st.session_state.maps_data = None

    with st.sidebar:
        st.header("📍 行程與費用設定")
        dest = st.text_input("輸入全球目的地", "日本大阪") 
        start_date = st.date_input("預計出發日期", datetime.now() + timedelta(days=30))
        days = st.slider("規劃天數", 1, 14, 5)
        currency = st.selectbox("幣別", ["TWD", "USD", "JPY", "EUR"])
        total_budget = st.number_input(f"每人預算上限 ({currency})", min_value=1000, value=50000, step=1000)
        prefs = st.text_input("興趣偏好", "美食、環球影城、購物")
        generate_btn = st.button("🚀 開始規劃行程")

    if generate_btn:
        mapper = DataMapper()
        brain = TravelBrain()
        with st.spinner(f"正在搜尋 {dest} 相關資訊..."):
            st.session_state.maps_data = mapper.search_attractions(dest, prefs)
            st.session_state.itinerary = brain.make_itinerary(
                {
                    "destination": dest, 
                    "days": days, 
                    "prefs": prefs,
                    "start_date": str(start_date),
                    "budget": f"{total_budget} {currency}"
                },
                st.session_state.maps_data
            )

    if st.session_state.itinerary:
        col_map, col_text = st.columns([1, 2])
        with col_map:
            st.subheader("📍 景點分佈")
            df = pd.DataFrame(st.session_state.maps_data)
            if not df.empty:
                m = folium.Map(location=[df['lat'].mean(), df['lng'].mean()], zoom_start=12)
                for _, row in df.iterrows():
                    folium.Marker([row['lat'], row['lng']], popup=row['名稱']).add_to(m)
                st_folium(m, width="100%", height=500, key="global_map")

        with col_text:
            st.subheader(f"📅 {dest} 行程與預算規劃")
            daily_sections = st.session_state.itinerary.split("---DAY_SEPARATOR---")
            for idx, content in enumerate(daily_sections):
                label = "💰 費用預算與氣候建議" if idx == 0 else f"📌 第 {idx} 天詳細行程"
                with st.expander(label, expanded=(idx <= 1)):
                    st.markdown(content.strip())

if __name__ == "__main__":
    main()