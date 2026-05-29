import json
import io
import zipfile
import streamlit as st

# =====================================================================
# 【基準版 3.0 (V3.5.0) 核心防線：全螢幕與手機端響應式 RWD 設定】
# =====================================================================
st.set_page_config(
    page_title="全球智慧旅遊助手",
    page_icon="🌐",
    layout="centered", # 使用 centered 在手機端滾動時視覺更集中、更適合單手操作
    initial_sidebar_state="collapsed" # 手機端預設隱藏側邊欄，避免遮擋主行程
)

# 注入輕量 CSS 優化手機端 RWD 卡片間距與字體，防止大卡片在窄螢幕擠壓變形
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stAlert p {
        font-size: 0.95rem;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 【核心數據架構初始化】
# =====================================================================
if "itinerary" not in st.session_state:
    st.session_state.itinerary = [
        {
            "day": 1,
            "title": "台北 ✈ 蘇黎世",
            "hotel_name": "蘇黎世中央飯店",
            "hotel_cost": 6500,
            "spots": [
                {"name": "班霍夫大街班機抵達", "cost": 0}
            ],
            "transport_type": "火車",
            "transport_cost_default": 150,
            "notes": "抵達後直接前往飯店 Check-in，單手滾動手機看此卡片。",
            "expanded": False  # 核心防線：手機端預設折疊
        },
        {
            "day": 2,
            "title": "蘇黎世 ➔ 盧森",
            "hotel_name": "盧森湖畔青年旅館",
            "hotel_cost": 4800,
            "spots": [
                {"name": "卡貝爾橋", "cost": 0},
                {"name": "盧森老城區游船", "cost": 1200}
            ],
            "transport_type": "火車",
            "transport_cost_default": 350,
            "notes": "利用 getattr 多欄位防呆接通當地交通費。",
            "expanded": False  # 核心防線：手機端預設折疊
        }
    ]

# =====================================================================
# 【左側邊欄：預算完全解耦看板】
# =====================================================================
st.sidebar.title("💰 預算完全解耦看板")
airfare = st.sidebar.number_input("國際機票手動填寫 (NTD)", min_value=0, value=35000, step=500)

# =====================================================================
# 【時光機邏輯：升級版雙向無損 ZIP 核心】
# =====================================================================
def generate_zip_backup(itinerary_data):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. 寫入 JSON 結構數據（強制轉換狀態確保安全備份）
        frozen_data = []
        for day in itinerary_data:
            day_copy = day.copy()
            day_copy["expanded"] = False  # 確保導出檔也是流暢折疊狀態
            frozen_data.append(day_copy)
            
        json_data = json.dumps(frozen_data, ensure_ascii=False, indent=4)
        zip_file.writestr("itinerary_data.json", json_data)
        
        # 2. 寫入 TXT 閱讀大綱
        txt_lines = [
            "==================================================",
            "        【全球智慧旅遊助手 - 行程備份大綱】",
            "==================================================",
            " 備份時間：2026年5月 (V3.5.0 基準版無損導出)",
            " 提示：本檔供人類閱讀，上傳還原時系統將自動隔離此檔。\n"
        ]
        total_spots = 0
        total_hotel = 0
        for day in frozen_data:
            txt_lines.append(f"【第 {day['day']} 天】：{day['title']}")
            txt_lines.append(f" 🏠 住宿：{day['hotel_name']} (NT$ {day['hotel_cost']:,})")
            total_hotel += day['hotel_cost']
            txt_lines.append(" 📍 景點行程：")
            for spot in day['spots']:
                txt_lines.append(f"   - {spot['name']} (門票: NT$ {spot['cost']:,})")
                total_spots += spot['cost']
            txt_lines.append(f" 🚌 交通：[{day['transport_type']}] 預計 NT$ {day.get('transport_cost_default', 0):,}")
            txt_lines.append(f" ✍ 備註：{day['notes']}\n" + "-"*40)
            
        txt_data = "\n".join(txt_lines)
        zip_file.writestr("itinerary_summary.txt", txt_data)
        
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def load_zip_backup(uploaded_file):
    try:
        with zipfile.ZipFile(uploaded_file, "r") as zip_file:
            if "itinerary_data.json" not in zip_file.namelist():
                st.error("❌ 匯入失敗：找不到核心結構數據 `itinerary_data.json`！")
                return False
            with zip_file.open("itinerary_data.json") as json_file:
                parsed_data = json.loads(json_file.read().decode("utf-8"))
                for day in parsed_data:
                    day["expanded"] = False # 導入時強制進入折疊防線
                st.session_state.itinerary = parsed_data
                st.success("🚀 【時光機無損還原成功】已載入結構卡片，TXT 文本已安全隔離！")
                return True
    except Exception as e:
        st.error(f"❌ 壓縮檔解析損壞。錯誤: {str(e)}")
        return False

# =====================================================================
# 【主介面渲染：手機單手操作流優化】
# =====================================================================
st.title("🌐 全球智慧旅遊助手")
st.caption("基準版 V3.5.0 | 手機端滾動與預算解耦雙向防線")

# 時光機控制台（手機端採用緊湊排版）
with st.container():
    st.markdown("### 🛸 雙向無損備份時光機")
    zip_data = generate_zip_backup(st.session_state.itinerary)
    
    # 導出與導入按鈕上下緊湊排列，方便大拇指單手點擊
    st.download_button(
        label="💾 EXPORT 導出行程壓縮包 (.zip)",
        data=zip_data,
        file_name="travel_assistant_v3.5.0.zip",
        mime="application/zip",
        use_container_width=True # 關鍵：按鈕撐滿寬度，手機端極好按
    )
    
    uploaded_zip = st.file_uploader("🔌 UPLOAD 上傳行程壓縮包 (.zip)", type=["zip"])
    if uploaded_zip is not None:
        if st.button("確認執行時光機還原", use_container_width=True):
            load_zip_backup(uploaded_zip)

st.write("---")

# 每日行程卡片渲染
st.markdown("### 📅 當前行程大綱 *(預設折疊優化)*")

calc_spots_total = 0
calc_hotel_total = 0
calc_transport_total = 0

for i, day in enumerate(st.session_state.itinerary):
    # 累加費用 (後台穿透精算)
    calc_hotel_total += day['hotel_cost']
    day_spots_cost = sum(spot['cost'] for spot in day['spots'])
    calc_spots_total += day_spots_cost
    
    # getattr 多欄位動態反射防呆
    t_cost = day.get("transport_cost_default", 0)
    calc_transport_total += t_cost
    
    # 計算該日純整數小計，用來顯示在卡片標題上
    day_subtotal = day['hotel_cost'] + day_spots_cost + t_cost
    
    # 手機端優化標題：在折疊狀態下，標題欄直接吐出【天數、主旨、當日花費】，單手滑動一目了然
    card_header = f"D{day['day']} | {day['title']} 💰小計: NT$ {day_subtotal:,}"
    
    # 嚴格守住 expanded=False 防線
    with st.expander(card_header, expanded=day.get("expanded", False)):
        st.markdown(f"**🏨 住宿飯店：** {day['hotel_name']} *(NT$ {day['hotel_cost']:,})*")
        
        st.markdown("**📍 景點門票明細：**")
        for spot in day['spots']:
            st.write(f"• {spot['name']} (NT$ {spot['cost']:,})")
            
        st.markdown(f"**🚌 當地交通：** [{day['transport_type']}] (預估 NT$ {t_cost:,})")
        st.markdown(f"**✍ 隨手備註：** {day['notes']}")

# =====================================================================
# 【動態預算看板同步更新】
# =====================================================================
grand_total_ntd = airfare + calc_spots_total + calc_hotel_total + calc_transport_total

# 側邊欄同步更新
st.sidebar.write("---")
st.sidebar.markdown(f"### 📊 純整數精算總結")
st.sidebar.write(f"✈ 國際機票費: NT$ {airfare:,}")
st.sidebar.write(f"📍 景點總門票: NT$ {calc_spots_total:,}")
st.sidebar.write(f"🏨 飯店總費用: NT$ {calc_hotel_total:,}")
st.sidebar.write(f"🚌 當地總交通: NT$ {calc_transport_total:,}")
st.sidebar.markdown(f"## 💰 自由行總計: **NT$ {grand_total_ntd:,}**")

# 如果在手機端看不到側邊欄，在主介面最底部加一個手機專用的「浮動預算提示」
st.write("---")
st.metric(
    label="📱 手機端即時精算總預算 (含機票)", 
    value=f"NT$ {grand_total_ntd:,}",
    delta=f"不含機票純地接: NT$ {calc_spots_total + calc_hotel_total + calc_transport_total:,}",
    delta_color="off"
)