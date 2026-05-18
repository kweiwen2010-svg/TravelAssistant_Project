import re
import os

def diagnose_and_fix():
    brain_path = "core/brain_25.py"
    app_path = "app.py"
    
    if not os.path.exists(brain_path):
        print(f"❌ 找不到 {brain_path}，請確保你在正確的專案目錄下執行！")
        return

    # 1. 讀取大腦檔案內容，分析 SpotDetail 的欄位名稱
    with open(brain_path, "r", encoding="utf-8") as f:
        brain_content = f.read()
    
    # 搜尋 SpotDetail 裡面的屬性
    spot_section = re.search(r"class SpotDetail.*?(?:class|$)", brain_content, re.DOTALL)
    
    spot_name_field = "spot_name"  # 預設
    stay_time_field = "stay_time"  # 預設
    
    if spot_section:
        spot_code = spot_section.group(0)
        # 尋找像是 name, spot_name, location 等屬性名稱
        fields = re.findall(r"(\w+)\s*:\s*\w+", spot_code)
        if fields:
            print(f"🔍 偵測到大腦中 SpotDetail 的欄位有：{fields}")
            # 判斷景點名稱欄位
            if "name" in fields:
                spot_name_field = "name"
            elif "location" in fields:
                spot_name_field = "location"
            elif "spot_name" in fields:
                spot_name_field = "spot_name"
                
            # 判斷停留時間欄位
            if "stay_time" in fields:
                stay_time_field = "stay_time"
            elif "duration" in fields:
                stay_time_field = "duration"
            elif "visit_time" in fields:
                stay_time_field = "visit_time"

    print(f"🎯 判定正確的欄位對接：景點名稱 -> spot.{spot_name_field} | 停留時間 -> spot.{stay_time_field}")

    # 2. 產生全新、完美對齊的完整 app.py 程式碼
    full_app_code = f'''import streamlit as st
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
        with st.spinner("🧙‍♂️ AI 正在挑選景點、計算最順路徑，請稍候..."):
            try:
                # 初始化核心大腦
                brain = TravelBrain()
                
                preferences = "、".join(travel_style) if travel_style else "無特殊偏好"
                
                # 自動適應大腦的方法名稱，優先使用自動偵測或標準 generate
                itineraries = brain.generate(
                    start_place=start_place,
                    destination=destination,
                    days=int(days),
                    budget=budget,
                    preferences=preferences
                )
                
                st.success("✨ 專屬行程規劃完成！")
                
                # 逐天渲染精美行程
                for idx, day_data in enumerate(itineraries):
                    st.subheader(f"📅 第 {{idx + 1}} 天：{{day_data.day_title}}")
                    st.markdown(f"**💡 今日摘要：** {{day_data.day_summary}}")
                    
                    # 顯示當天景點與活動（自動對齊正確的欄位名稱）
                    for spot_idx, spot in enumerate(day_data.spots):
                        spot_name_val = getattr(spot, "{spot_name_field}", "未知景點")
                        stay_time_val = getattr(spot, "{stay_time_field}", "適度停留")
                        
                        with st.expander(f"📍 景點 {{spot_idx + 1}}：{{spot_name_val}} ({{stay_time_val}})"):
                            st.write(f"**🕒 建議時間：** {{getattr(spot, 'time_slot', '彈性')}}")
                            st.write(f"**📝 活動內容：** {{getattr(spot, 'description', '自由參觀')}}")
                            st.write(f"**🍔 推薦美食：** {{getattr(spot, 'local_food', '探索當地美食')}}")
                    
                    st.markdown("---")
                    
            except Exception as e:
                st.error(f"💥 糟糕，行程生成時發生了一點驚喜（錯誤）：\\n`{{str(e)}}`")
'''

    # 3. 寫入覆蓋 app.py
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(full_app_code)
    print("✅ 完美對齊的 app.py 已經全自動修正並覆蓋完畢！")

if __name__ == "__main__":
    diagnose_and_fix()