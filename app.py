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

st.markdown("""
<style>
    .welcome-box { 
        background-color: rgba(30, 41, 59, 0.05); 
        padding: 22px; 
        border-radius: 10px; 
        border: 1px solid rgba(148, 163, 184, 0.3); 
        margin-bottom: 25px;
        color: inherit; 
    }
    .welcome-box h4 { color: inherit !important; margin-top: 0px; }
    .day-header { background: linear-gradient(90deg, #1e293b 0%, #334155 100%); color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold; margin-top: 35px; }
    .spot-card { background-color: #ffffff; padding: 18px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); color: #1e293b !important; }
    .spot-card p, .spot-card span, .spot-card div { color: #1e293b !important; }
    .hotel-card { background-color: #f8fafc; padding: 18px; border-radius: 8px; border-left: 5px solid #3b82f6; margin-top: 20px; color: #1e293b !important; }
    .hotel-card p, .hotel-card span, .hotel-card div { color: #1e293b !important; }
    .trans-capsule { display: inline-block; background-color: #f1f5f9; color: #475569 !important; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; margin: 8px 0; border: 1px solid #e2e8f0; }
    .alt-box { background-color: #fffbeb; border: 1px dashed #fef3c7; padding: 12px 16px; border-radius: 6px; font-size: 0.9rem; margin-top: 10px; color: #78350f !important; }
    .alt-box b, .alt-box span { color: #78350f !important; }
    .budget-box { background-color: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.3); padding: 20px; border-radius: 8px; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

def get_transport_icon(trans_str: str) -> str:
    if "步行" in trans_str or "🚶" in trans_str: return "🚶"
    if "地鐵" in trans_str or "🚇" in trans_str: return "🚇"
    if "公車" in trans_str or "巴士" in trans_str or "🚌" in trans_str: return "🚌"
    if "飛機" in trans_str or "✈️" in trans_str: return "✈️"
    if "火車" in trans_str or "🚄" in trans_str: return "🚄"
    return "🔄"

# 數字安全轉換防呆防線
def safe_int(val) -> int:
    if val is None: return 0
    if isinstance(val, (int, float)): return int(val)
    try:
        clean_str = re.sub(r'[^\d]', '', str(val))
        return int(clean_str) if clean_str else 0
    except:
        return 0

if "brain" not in st.session_state: st.session_state.brain = TravelBrain()
if "itinerary_days" not in st.session_state: st.session_state.itinerary_days = {}
if "user_prompt_val" not in st.session_state: st.session_state.user_prompt_val = ""
if "total_days_val" not in st.session_state: st.session_state.total_days_val = 7
if "is_generating" not in st.session_state: st.session_state.is_generating = False

def capture_sidebar_inputs(prompt, days, country, d_time, f_hours, tz_diff):
    st.session_state.user_prompt_val = prompt
    st.session_state.total_days_val = days
    st.session_state.start_country_val = country
    st.session_state.departure_time_val = d_time
    st.session_state.flight_hours_val = f_hours
    st.session_state.timezone_diff_val = tz_diff

st.title("✈️ 全球智慧旅遊助手 2.5")
st.markdown('<div class="welcome-box"><h4>🌐 V3.5.0 剛性解耦完全體（ZIP雙向對齊版）</h4>當地交通與四大維度費用完全接通，導入/導出全面對齊 ZIP 壓縮包檔案！</div>', unsafe_allow_html=True)

with st.sidebar:
    # 🌟 方案 B：歷史行程時光機全面對齊 .zip 上傳
    st.header("⏳ 歷史行程時光機")
    uploaded_file = st.file_uploader("📦 載入歷史行程存檔 (.zip)", type=["zip"])
    if uploaded_file is not None:
        try:
            with zipfile.ZipFile(uploaded_file, 'r') as z:
                # 尋找 zip 壓縮包裡的第一個 json 檔案
                json_files = [f for f in z.namelist() if f.endswith('.json')]
                if json_files:
                    with z.open(json_files[0]) as f:
                        file_data = json.load(f)
                        if "days_data" in file_data:
                            restored_days = {}
                            for k, v in file_data["days_data"].items():
                                restored_days[int(k)] = DayItinerary.model_validate(v)
                            st.session_state.itinerary_days = restored_days
                            if "user_prompt" in file_data:
                                st.session_state.user_prompt_val = file_data["user_prompt"]
                            st.success("💾 ZIP 壓縮存檔已成功無損還原！")
                else:
                    st.error("壓縮包內找不到有效的行程 JSON 數據。")
        except Exception as e:
            st.error(f"解析 ZIP 失敗：{str(e)}")

    st.write("---")
    st.header("⚙️ 旅遊核心設定")
    user_prompt = st.text_area("🔮 旅遊意向：", value="瑞士 人文 美食 購物 古蹟")
    total_days = st.number_input("📅 總天數：", min_value=1, max_value=30, value=7, step=1)
    
    st.subheader("🛫 航班與時區參數")
    start_country = st.text_input("📍 出發地地標：", value="台灣台北 (TPE)")
    departure_time = st.text_input("⏰ 第 1 天起飛時間點：", value="晚上 23:30")
    flight_hours = st.number_input("⏱️ 飛行總時間 (小時)：", min_value=0.5, max_value=40.0, value=14.0, step=0.5)
    timezone_diff = st.number_input("🌐 目的地時差 (比台灣慢請填負數)：", min_value=-12.0, max_value=12.0, value=-6.0, step=1.0)
    
    st.write("---")
    st.subheader("💰 剛性預算手動補正")
    sidebar_flight_cost = st.number_input("✈️ 國際機票總費用 (NT$ / 人)：", min_value=0, value=35000, step=500)
    
    col_gen, col_clear = st.columns(2)
    with col_gen: btn_generate = st.button("🚀 啟動大腦生成", type="primary", use_container_width=True, disabled=st.session_state.is_generating)
    with col_clear:
        if st.button("🧹 清空重置", type="secondary", use_container_width=True):
            st.session_state.itinerary_days = {}
            st.session_state.user_prompt_val = ""
            st.session_state.is_generating = False
            st.rerun()
            
    progress_sidebar = st.empty()

    # 🌟 方案 B：打包下載同樣採用 ZIP 導出 (雙檔案版本：JSON 數據 + 人類可讀 TXT 摘要)
    if st