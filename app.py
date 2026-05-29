import os
import json
import zipfile
import io
import streamlit as st

# ==========================================
# 基準版 V3.5.0 核心時光機邏輯 (雙檔案無損備份)
# ==========================================

def export_itinerary_to_zip(itinerary_data):
    """
    將行程數據導出為 ZIP 壓縮包，內含：
    1. trajectory_data.json (供系統無損導入)
    2. trajectory_summary.txt (供人類閱讀的大綱)
    """
    # 1. 建立記憶體中的 ZIP 檔案
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 2. 寫入 JSON 數據檔案
        json_str = json.dumps(itinerary_data, ensure_ascii=False, indent=4)
        zf.writestr("trajectory_data.json", json_str)
        
        # 3. 建立並寫入人類可讀的 TXT 摘要大綱
        txt_content = []
        txt_content.append(f"=== 全球智慧旅遊助手 行程摘要大綱 ===")
        txt_content.append(f"目的地: {itinerary_data.get('destination', '未填寫')}")
        txt_content.append(f"總天數: {itinerary_data.get('days', 0)} 天")
        txt_content.append(f"出發國家: {itinerary_data.get('departure_country', '未填寫')}")
        txt_content.append(f"機票價格: NT$ {itinerary_data.get('flight_price', 0):,}")
        txt_content.append("-" * 40)
        
        # 遍歷每日卡片內容
        days_list = itinerary_data.get("daily_cards", [])
        for day in days_list:
            txt_content.append(f"[{day.get('day_id', '')}] {day.get('title', '無標題')}")
            txt_content.append(f"   景點預算 (Spots): NT$ {day.get('spots_budget', 0):,}")
            txt_content.append(f"   住宿預算 (Hotel): NT$ {day.get('hotel_budget', 0):,}")
            txt_content.append(f"   本日小計: NT$ {day.get('day_total', 0):,}")
            txt_content.append("-" * 40)
            
        full_txt_str = "\n".join(txt_content)
        zf.writestr("trajectory_summary.txt", full_txt_str)
        
    return zip_buffer.getvalue()


def import_itinerary_from_zip(uploaded_file):
    """
    從用戶上傳的 ZIP 壓縮包中還原行程：
    解壓後只抓取並讀取 trajectory_data.json，自動忽略 txt 檔案
    """
    try:
        # 將上傳的檔案讀入記憶體
        zip_file_bytes = uploaded_file.read()
        with zipfile.ZipFile(io.BytesIO(zip_file_bytes)) as zf:
            # 檢查壓縮包內是否有 json 檔案
            if "trajectory_data.json" in zf.namelist():
                json_data = zf.read("trajectory_data.json").decode("utf-8")
                itinerary_data = json.loads(json_data)
                return itinerary_data
            else:
                st.error("導入失敗：壓縮包內找不到有效的 trajectory_data.json 數據檔案！")
                return None
    except Exception as e:
        st.error(f"備份檔案解析出錯，請檢查檔案是否損壞。錯誤訊息: {str(e)}")
        return None

# ==========================================
# Streamlit UI 介面呈現 (死守四大防線)
# ==========================================

# 假定這些是我們死守的頂部全局參數（Vincent 本地端已有穩定的狀態管理機制）
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = {
        "destination": "蘇黎世",
        "days": 2,
        "departure_country": "台灣",
        "flight_price": 35000,
        "daily_cards": [
            {"day_id": "D1", "title": "台北 ✈ 蘇黎世", "spots_budget": 2000, "hotel_budget": 4650, "day_total": 6650},
            {"day_id": "D2", "title": "蘇黎世 ➔ 盧森", "spots_budget": 1500, "hotel_budget": 4850, "day_total": 6350}
        ]
    }

st.title("🌐 全球智慧旅遊助手")
st.caption("基準版 V3.5.0 | 手機端滾動與預算解耦雙向防線")

st.subheader("🛸 雙向無損備份時光機")

# 1. EXPORT 導出按鈕
zip_data = export_itinerary_to_zip(st.session_state.itinerary)
st.download_button(
    label="💾 EXPORT 導出行程壓縮包 (.zip)",
    data=zip_data,
    file_name="travel_itinerary_backup.zip",
    mime="application/zip",
    use_container_width=True
)

# 2. UPLOAD 上傳元件
uploaded_zip = st.file_uploader("🔌 UPLOAD 上傳行程壓縮包 (.zip)", type=["zip"])
if uploaded_zip is not None:
    imported_data = import_itinerary_from_zip(uploaded_zip)
    if imported_data:
        st.session_state.itinerary = imported_data
        st.success("時光機還原成功！已無損導入最新的 JSON 數據結構。")
        # st.rerun() # 根據你手機端的 Streamlit 版本決定是否啟用強制重新整理

st.markdown("---")
st.subheader("📅 當前行程大綱 (預設折疊優化)")

# 3. 渲染每日行程卡片 (死守手機端 expanded=False 預設折疊防線)
for day in st.session_state.itinerary["daily_cards"]:
    with st.expander(f" {day['day_id']} | {day['title']} 💰 小計: NT$ {day['day_total']:,}", expanded=False):
        st.write(f"景點門票預算：NT$ {day['spots_budget']:,}")
        st.write(f"住宿酒店預算：NT$ {day['hotel_budget']:,}")