import streamlit as st
import os
from core.brain_25 import TravelBrain, DayItinerary

# ==========================================
# 1. 網頁頂級配置（優化手機版體驗）
# ==========================================
st.set_page_config(
    page_title="全球智慧旅遊助手 2.5",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"  # 強制手機版一進網頁就自動展開左側設定欄
)

# ==========================================
# 2. 處理雲端與本地金鑰環境變數
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

if "GOOGLE_MAPS_API_KEY" in st.secrets:
    os.environ["GOOGLE_MAPS_API_KEY"] = st.secrets["GOOGLE_MAPS_API_KEY"]

# ==========================================
# 3. 主畫面標題與親切的新手防呆引導
# ==========================================
st.title("✈️ 全球智慧旅遊助手 2.5")
st.caption("基於 Gemini 2.5 Flash 大腦 • 純原生無鏈結高穩定版")

st.info(
    "👋 歡迎使用！請看網頁【左側的設定面板】（手機版已自動為您展開），"
    "輸入您想去的目的地、天數與預算偏好，接著按下最底下的『開始規劃行程』按鈕，"
    "AI 就會立刻在這裡為您量身打造專屬旅程與地圖路線喔！"
)

# ==========================================
# 4. 左側側邊欄輸入介面 (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🗺️ 旅程設定")
    
    start_place = st.text_input("出發地", value="台北")
    destination = st.text_input("目的地", value="東京")
    days = st.number_input("旅遊天數 (天)", min_value=1, max_value=30, value=5)
    
    budget = st.selectbox(
        "預算級別",
        ["經濟實惠", "標準舒適", "奢華享受"]
    )
    
    travel_style = st.multiselect(
        "旅遊偏好 (可多選)",
        ["美食饗宴", "古蹟文化", "自然風景", "購物血拼", "親子打卡", "放鬆度假"],
        default=["美食饗宴", "自然風景"]
    )
    
    st.markdown("---")
    submit_btn = st.button("🚀 開始規劃行程", use_container_width=True)

# ==========================================
# 5. 核心執行與邏輯串接
# ==========================================
if submit_btn:
    if not destination.strip():
        st.warning("⚠️ 請先輸入你想去的目的地！")
    else:
        with st.spinner("🧙‍♂️ AI 正在逐天思考景點、串聯最佳路線，請稍候..."):
            try:
                # 初始化核心大腦
                brain = TravelBrain()
                
                # 建立使用者偏好提示詞
                preferences_str = "、".join(travel_style) if travel_style else "無特殊偏好"
                user_prompt = f"我要從{start_place}出發到{destination}旅遊，預計玩{int(days)}天，預算風格是{budget}，主要偏好是：{preferences_str}。"
                
                # 🎯 精準對齊大腦：建立多天行程儲存陣列，並運用 previous_context 串聯記憶
                itineraries = []
                previous_context = ""
                
                for day_idx in range(1, int(days) + 1):
                    # 呼叫大腦專屬單天生成函式
                    day_data = brain.generate_day_itinerary(
                        user_prompt=user_prompt,
                        day_idx=day_idx,
                        previous_context=previous_context
                    )
                    itineraries.append(day_data)
                    # 滾動累積前情提要，讓下一天更順路
                    previous_context += f"第 {day_idx} 天的主題是：{day_data.day_title}，今天住在：{day_data.recommended_hotel.name}。"
                
                st.success("✨ 您的專屬精緻結構化行程已全部生成完畢！")
                
                # 逐天渲染精美行程
                for idx, day_data in enumerate(itineraries):
                    st.header(f"📅 第 {day_data.day_number} 天：{day_data.day_title}")
                    
                    if day_data.local_tips:
                        st.info(f"💡 **交通銜接與注意事項：** {day_data.local_tips}")
                    
                    st.markdown("### 📍 今日踩點與美食行程：")
                    
                    # 顯示當天景點與活動 (精準對齊大腦 SpotDetail 欄位)
                    for spot_idx, spot in enumerate(day_data.spots):
                        with st.expander(f"📍 景點 {spot_idx + 1}：{spot.name} ({spot.time})"):
                            st.write(f"**📝 活動與景點介紹：** {spot.description}")
                            st.write(f"**🚗 交通方式：** {spot.transportation}")
                            st.write(f"**🎫 門票與購票攻略：** {spot.booking_info}")
                            st.write(f"**💰 現場預估消費：** {spot.estimated_spending}")
                            
                            # 如果有替代方案美食，貼心顯示
                            if spot.alternatives:
                                st.markdown("**🍔 周邊替代美食/備案：**")
                                for alt in spot.alternatives:
                                    st.markdown(f"- **{alt.name}**：{alt.desc}")
                    
                    # 顯示當晚主推住宿 (精準對齊大腦 HotelDetail 欄位)
                    st.markdown("### 🏨 今日推薦住宿住宿：")
                    with st.chat_message("assistant", avatar="🏨"):
                        st.markdown(f"**主推飯店：{day_data.recommended_hotel.name}**")
                        st.caption(f"💰 價位等級：{day_data.recommended_hotel.price_level}")
                        st.write(f"👍 **推薦入住理由：** {day_data.recommended_hotel.reason}")
                        
                        # 備用飯店顯示
                        if day_data.alternative_hotels:
                            st.markdown("**📌 其他同區域替代住宿備案：**")
                            for alt_hotel in day_data.alternative_hotels:
                                st.markdown(f"- **{alt_hotel.name}** ({alt_hotel.desc})")
                                
                    st.markdown("---")
                    
            except Exception as e:
                st.error(f"💥 糟糕，行程生成時發生了一點驚喜（錯誤）：\n`{str(e)}`")