import os
import json
import zipfile
import io
import streamlit as st

# ==========================================
# 1. 核心時光機邏輯 (雙檔案無損備份)
# ==========================================

def export_itinerary_to_zip(itinerary_data):
    """將行程數據導出為 ZIP，內含 json 與 txt"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 寫入 JSON 供無損導入
        json_str = json.dumps(itinerary_data, ensure_ascii=False, indent=4)
        zf.writestr("trajectory_data.json", json_str)
        
        # 寫入 TXT 供人類閱讀
        txt_content = [
            "=== 全球智慧旅遊助手 行程摘要 ===",
            f"目的地: {itinerary_data.get('destination', '')}",
            f"總天數: {itinerary_data.get('days', 1)} 天",
            f"出發國家: {itinerary_data.get('departure_country', '')}",
            f"出發時間: {itinerary_data.get('departure_time', '')}",
            f"飛行時間: {itinerary_data.get('flight_time', '')}",
            f"時差: {itinerary_data.get('time_difference', '')}",
            f"機票價格: NT$ {itinerary_data.get('flight_price', 0):,}",
            "-" * 40
        ]
        for day in itinerary_data.get("daily_cards", []):
            txt_content.append(f"[{day.get('day_id', '')}] {day.get('title', '')}")
            txt_content.append(f"   景點預算: NT$ {day.get('spots_budget', 0):,}")
            txt_content.append(f"   住宿預算: NT$ {day.get('hotel_budget', 0):,}")
            txt_content.append(f"   本日小計: NT$ {day.get('day_total', 0):,}")
            txt_content.append("-" * 40)
            
        zf.writestr("trajectory_summary.txt", "\n".join(txt_content))
    return zip_buffer.getvalue()

def import_itinerary_from_zip(uploaded_file):
    """上傳 ZIP 檔案，只讀取其中的 json 進行還原"""
    try:
        zip_file_bytes = uploaded_file.read()
        with zipfile.ZipFile(io.BytesIO(zip_file_bytes)) as zf:
            if "trajectory_data.json" in zf.namelist():
                json_data = zf.read("trajectory_data.json").decode("utf-8")
                return json.loads(json_data)
            else:
                st.error("導入失敗：壓縮包內找不到 trajectory_data.json")
                return None
    except Exception as e:
        st.error(f"備份檔案解析出錯: {str(e)}")
        return None

# ==========================================
# 2. 初始化 Session State 狀態管理
# ==========================================
if 'destination' not in st.session_state:
    st.session_state.destination = "蘇黎世"
if 'days' not in st.session_state:
    st.session_state.days = 2
if 'departure_country' not in st.session_state:
    st.session_state.departure_country = "台灣"
if 'departure_time' not in st.session_state:
    st.session_state.departure_time = "10:00"
if 'flight_time' not in st.session_state:
    st.session_state.flight_time = "14小時"
if 'time_difference' not in st.session_state:
    st.session_state.time_difference = "-6"
if 'flight_price' not in st.session_state:
    st.session_state.flight_price = 35000
if 'daily_cards' not in st.session_state:
    st.session_state.daily_cards = [
        {"day_id": "D1", "title": "台北 ✈ 蘇黎世", "spots_budget": 2000, "hotel_budget": 4650, "day_total": 6650},
        {"day_id": "D2", "title": "蘇黎世 ➔ 盧森", "spots_budget": 1500, "hotel_budget": 4850, "day_total": 6350}
    ]

# ==========================================
# 3. Streamlit UI 介面呈現
# ==========================================
st.title("🌐 全球智慧旅遊助手")
st.caption("基準版 V3.5.0 | 手機端滾動與預算解耦雙向防線")

# --- 這裡幫你把 7 大全局輸入欄位通通蓋回來！ ---
st.subheader("📝 全局參數設定")
col1, col2 = st.columns(2)
with col1:
    st.session_state.destination = st.text_input("📍 地點", value=st.session_state.destination)
    st.session_state.days = st.number_input("📅 天數", min_value=1, value=st.session_state.days)
    st.session_state.departure_country = st.text_input("🛫 出發國", value=st.session_state.departure_country)
    st.session_state.departure_time = st.text_input("⏰ 出發時間", value=st.session_state.departure_time)
with col2:
    st.session_state.flight_time = st.text_input("⏳ 飛行時間", value=st.session_state.flight_time)
    st.session_state.time_difference = st.text_input("🌐 時差", value=st.session_state.time_difference)
    st.session_state.flight_price = st.number_input("💵 機票價格 (側邊欄解耦同步)", min_value=0, value=st.session_state.flight_price)

st.markdown("---")

# --- 時光機模組 ---
st.subheader("🛸 雙向無損備份時光機")

# 打包當前所有輸入狀態準備導出
current_data = {
    "destination": st.session_state.destination,
    "days": st.session_state.days,
    "departure_country": st.session_state.departure_country,
    "departure_time": st.session_state.departure_time,
    "flight_time": st.session_state.flight_time,
    "time_difference": st.session_state.time_difference,
    "flight_price": st.session_state.flight_price,
    "daily_cards": st.session_state.daily_cards
}

zip_data = export_itinerary_to_zip(current_data)
st.download_button(
    label="💾 EXPORT 導出行程壓縮包 (.zip)",
    data=zip_data,
    file_name="travel_itinerary_backup.zip",
    mime="application/zip",
    use_container_width=True
)

uploaded_zip = st.file_uploader("🔌 UPLOAD 上傳行程壓縮包 (.zip)", type=["zip"])
if uploaded_zip is not None:
    imported_data = import_itinerary_from_zip(uploaded_zip)
    if imported_data:
        # 將讀取到的 JSON 數據寫回各個輸入框的 state 觸發畫面更新
        st.session_state.destination = imported_data.get("destination", "")
        st.session_state.days = imported_data.get("days", 1)
        st.session_state.departure_country = imported_data.get("departure_country", "")
        st.session_state.departure_time = imported_data.get("departure_time", "")
        st.session_state.flight_time = imported_data.get("flight_time", "")
        st.session_state.time_difference = imported_data.get("time_difference", "")
        st.session_state.flight_price = imported_data.get("flight_price", 0)
        st.session_state.daily_cards = imported_data.get("daily_cards", [])
        st.success("時光機還原成功！欄位已同步更新。")

st.markdown("---")
st.subheader("📅 當前行程大綱 (預設折疊優化)")

# 渲染每日行程卡片 (死守手機端 expanded=False 預設折疊防線)
for day in st.session_state.daily_cards:
    with st.expander(f" {day['day_id']} | {day['title']} 💰 小計: NT$ {day['day_total']:,}", expanded=False):
        st.write(f"景點門票預算：NT$ {day['spots_budget']:,}")
        st.write(f"住宿酒店預算：NT$ {day['hotel_budget']:,}")