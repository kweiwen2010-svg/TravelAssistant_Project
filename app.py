import streamlit as st
import urllib.parse
import os
import re
import io
import json
import zipfile
from dotenv import load_dotenv

load_dotenv()
from core.brain_25 import TravelBrain, DayItinerary

st.set_page_config(page_title="全球智慧旅遊助手 2.5", page_icon="✈️", layout="wide")

# 🎨 注入交通時間軸與膠囊 CSS 樣式
st.markdown("""
<style>
    .welcome-box { background-color: #f0fdf4; padding: 22px; border-radius: 10px; border: 1px solid #bbf7d0; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .day-header { background: linear-gradient(90deg, #1e293b 0%, #334155 100%); color: white; padding: 12px 20px; border-radius: 6px; font-size: 1.25rem; font-weight: bold; margin-top: 35px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
    
    .spot-card { background-color: #ffffff; padding: 18px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .hotel-card { background-color: #f0f7ff; padding: 18px; border-radius: 8px; border-left: 5px solid #0284c7; margin-bottom: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    
    .time-badge { color: #ff4b4b; font-weight: bold; font-size: 1.1rem; }
    .hotel-badge { color: #0284c7; font-weight: bold; font-size: 1.1rem; }
    .spot-name { font-weight: bold; font-size: 1.2rem; color: #1e293b; }
    .info-sub-block { font-size: 0.95rem; color: #475569; background-color: #f8fafc; padding: 8px 12px; border-radius: 6px; margin-top: 6px; border: 1px solid #e2e8f0; }
    .tip-box { background-color: #f8fafc; padding: 12px; border-radius: 8px; border: 1px dashed #cbd5e1; margin-top: 25px; }
    .download-section { background-color: #f1f5f9; padding: 20px; border-radius: 10px; margin-top: 30px; border: 1px solid #cbd5e1; }

    /* 🛡️ 垂直時間軸與交通微縮膠囊外觀樣式 */
    .timeline-bridge {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 12px 0;
        width: 100%;
    }
    .timeline-line {
        width: 2px;
        height: 25px;
        border-left: 2px dashed #94a3b8;
    }
    .timeline-capsule {
        background-color: #f1f5f9;
        color: #475569;
        font-size: 0.9rem;
        padding: 6px 16px;
        border-radius: 50px;
        border: 1px solid #cbd5e1;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        max-width: 90%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("✈️ 全球智慧旅遊助手 2.5 (時間軸優化精修版 V3.2.2)")
st.caption("基於 Gemini 2.5 Flash 大腦 • 已精確限縮關鍵字並修正飯店過渡圖示與引號語法")

if "brain" not in st.session_state: st.session_state.brain = TravelBrain()
if "itinerary_days" not in st.session_state: st.session_state.itinerary_days = {}
if "is_generating" not in st.session_state: st.session_state.is_generating = False
if "user_prompt_val" not in st.session_state: st.session_state.user_prompt_val = "我想去土耳其10天 老婆同遊 美食 人文 風景 行程不要太趕"
if "total_days_val" not in st.session_state: st.session_state.total_days_val = 10
if "uploader_version" not in st.session_state: st.session_state.uploader_version = 0

def prepare_download_text(prompt, sorted_days_keys):
    download_text = f"=== 全球智慧旅遊助手 專屬行程 ===\n\n[使用者旅遊意向]\n{prompt}\n\n"
    for cb in sorted_days_keys:
        d_obj: DayItinerary = st.session_state.itinerary_days[cb]
        download_text += f"-----------------------------------------\n📅 第 {cb} 天：{d_obj.day_title}\n-----------------------------------------\n"
        for sp in d_obj.spots:
            download_text += f"⏱️ 時間：{sp.time}\n📍 景點/餐廳：{sp.name}\n📝 介紹：{sp.description}\n"
            download_text += f"🚇 交通指引：{sp.transportation}\n"
            download_text += f"🎫 購票攻略：{sp.booking_info}\n"
            download_text += f"💳 預估費用：{sp.estimated_spending}\n\n"
        download_text += f"🏠 當晚住宿：{d_obj.recommended_hotel.name}\n"
        download_text += f"📝 推薦理由：{d_obj.recommended_hotel.reason}\n"
        download_text += f"💰 房價等級：{d_obj.recommended_hotel.price_level}\n"
        download_text += f"💡 當日導遊貼心叮嚀：{d_obj.local_tips}\n\n"
    return download_text

def create_zip_backup(prompt, sorted_days_keys):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        raw_text = prepare_download_text(prompt, sorted_days_keys)
        bom_utf8_text = "\ufeff" + raw_text
        zip_file.writestr("itinerary_details.txt", bom_utf8_text.encode("utf-8-sig"))
        
        json_data = {
            "user_prompt": prompt,
            "total_days": len(sorted_days_keys),
            "days_data": {str(k): v.model_dump() for k, v in st.session_state.itinerary_days.items()}
        }
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        zip_file.writestr("itinerary_backup.json", json_str.encode("utf-8-sig"))
    return zip_buffer.getvalue()

# 🛡️ 【關鍵字防線優化】：精確拆分比對條件，避免單一「機」字造成誤判
def get_transport_icon(text: str) -> str:
    if "飯店" in text or "Check-in" in text or "入住" in text: return "🧳"
    if "步" in text or "走" in text: return "🚶"
    if "地鐵" in text or "捷運" in text or "火車" in text or "電車" in text or "M" in text: return "🚇"
    if "公車" in text or "巴士" in text or "客運" in text: return "🚌"
    if "開車" in text or "自駕" in text or "計程車" in text or "小黃" in text or "Uber" in text: return "🚗"
    if "船" in text or "渡輪" in text: return "🚢"
    if "飛機" in text or "航班" in text or "空運" in text: return "✈️"
    return "🔄"

if not st.session_state.itinerary_days and not st.session_state.is_generating:
    st.markdown("""
    <div class="welcome-box">
        <h4 style="margin-top:0; color: #166534;">💡 歡迎使用全球智慧旅遊助手 V3.2.2！</h4>
        <p style="font-size: 0.98rem; color: #1e293b;">我們已完成機場到飯店的過渡缺陷精修，並全面綁定行李箱 <b>🧳</b> 視覺：</p>
        <ol style="font-size: 0.95rem; color: #374151; line-height: 1.7;">
            <li>請看向網頁的 <b>⬅️ 左側邊欄（📋 旅遊意向設定與備份還原）</b>。</li>
            <li>在輸入框中確認或修改旅遊想法，點擊 <b>「🚀 開始全自動分段生成」</b>。</li>
            <li>本模組完全獨立不混亂，請放心進行多平台行動端測試！</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.header("📋 旅遊意向設定")
    
    uploader_key = f"zip_uploader_v_{st.session_state.uploader_version}"
    uploaded_zip = st.file_uploader("📂 拖入先前導出的 .zip 備份檔進行還原", type=["zip"], key=uploader_key)
    
    if uploaded_zip is not None:
        try:
            with zipfile.ZipFile(uploaded_zip) as z:
                if "itinerary_backup.json" not in z.namelist():
                    st.error("❌ 錯誤：上傳的 ZIP 檔中找不到標準的行程備份數據。")
                else:
                    with z.open("itinerary_backup.json") as json_file:
                        loaded_bytes = json_file.read()
                        loaded_json = json.loads(loaded_bytes.decode("utf-8-sig"))
                        
                        restored_days = {}
                        for k, v in loaded_json["days_data"].items():
                            restored_days[int(k)] = DayItinerary.model_validate(v)
                        
                        st.session_state.itinerary_days = restored_days
                        st.session_state.user_prompt_val = loaded_json.get("user_prompt", "")
                        st.session_state.total_days_val = loaded_json.get("total_days", len(restored_days))
                        st.success("🎯 時光機同步成功！行程已完美還原。")
        except Exception as e:
            st.error(f"❌ 錯誤：存檔數據結構毀損，無法讀取。({str(e)})")

    st.divider()
    
    user_prompt = st.text_area("輸入您的旅遊靈感與偏好：", value=st.session_state.user