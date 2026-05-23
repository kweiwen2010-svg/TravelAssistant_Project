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
    .welcome-box { background-color: #f8fafc; padding: 22px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 25px; }\
    .day-header { background: linear-gradient(90deg, #1e293b 0%, #334155 100%); color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold; margin-top: 35px; }\
    .spot-card { background-color: #ffffff; padding: 18px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }\
    .hotel-card { background-color: #f8fafc; padding: 18px; border-radius: 8px; border-left: 5px solid #3b82f6; margin-top: 20px; }\
    .trans-capsule { display: inline-block; background-color: #f1f5f9; color: #475569; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; margin: 8px 0; border: 1px solid #e2e8f0; }\
    .alt-box { background-color: #fffbeb; border: 1px dashed #fef3c7; padding: 12px 16px; border-radius: 6px; font-size: 0.9rem; margin-top: 10px; }\
    .download-section { background-color: #fafafa; border: 1px solid #eaeaea; padding: 20px; border-radius: 8px; margin-top: 40px; }\
</style>
""", unsafe_allow_html=True)

def get_transport_icon(trans_str: str) -> str:
    if "步行" in trans_str or "🚶" in trans_str: return "🚶"
    if "地鐵" in trans_str or "🚇" in trans_str: return "🚇"
    if "公車" in trans_str or "巴士" in trans_str or "🚌" in trans_str: return "🚌"
    if "飛機" in trans_str or "✈️" in trans_str: return "✈️"
    if "火車" in trans_str or "🚄" in trans_str: return "🚄"
    return "🔄"

if "brain" not in st.session_state:
    st.session_state.brain = TravelBrain()
if "itinerary_days" not in st.session_state:
    st.session_state.itinerary_days = {}
if "user_prompt_val" not in st.session_state:
    st.session_state.user_prompt_val = ""
if "total_days_val" not in st.session_state:
    st.session_state.total_days_val = 7

st.title("✈️ 全球智慧旅遊助手 2.5")
st.markdown('<div class="welcome-box"><h4>🌐 V3.4.2 物理時區引擎（防爆安全版）</h4>已完美串聯『飛行時間、起飛時段、目的地時差』。大腦將依物理公式自動判斷第 1 天是否過夜、需不需要住宿定錨，時光機回傳功能處於全鎖定穩定狀態。</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 旅遊核心設定")
    user_prompt = st.text_area("🔮 旅遊意向：", value="義大利 人文 美食 購物 古蹟", placeholder="例如：日本東京5天4夜...")
    total_days = st.number_input("📅 總天數：", min_value=1, max_value=30, value=7, step=1)
    
    st.subheader("🛫 航班與時區參數")
    start_country = st.text_input("📍 出發地地標：", value="台灣台北 (TPE)")
    departure_time = st.text_input("⏰ 第 1 天起飛時間點：", value="晚上 23:30", placeholder="例如：上午 09:00 或 晚上 23:30")
    
    # 精準物理數值設定
    flight_hours = st.number_input("⏱️ 飛行總時間 (小時)：", min_value=0.5, max_value=40.0, value=14.0, step=0.5)
    timezone_diff = st.number_input("🌐 目的地時差 (比台灣慢請填負數)：", min_value=-12.0, max_value=12.0, value=-6.0, step=1.0, help="例如：歐洲比台灣慢 6 小時填 -6；日本比台灣快 1 小時填 1")
    
    col_gen, col_clear = st.columns(2)
    with col_gen:
        btn_generate = st.button("🚀 啟動大腦生成", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🧹 清空重置", type="secondary", use_container_width=True):
            st.session_state.itinerary_days = {}
            st.session_state.user_prompt_val = ""
            if "last_uploaded_file_name" in st.session_state:
                del st.session_state.last_uploaded_file_name
            st.rerun()
            
    st.markdown("---")
    uploaded_file = st.file_uploader("⏳ 時光機還原：上傳行程 ZIP 檔", type=["zip"], key="time_machine_uploader")
    if uploaded_file:
        if "last_uploaded_file_name" not in st.session_state or st.session_state.last_uploaded_file_name != uploaded_file.name:
            try:
                with zipfile.ZipFile(uploaded_file) as z:
                    if "itinerary_backup.json" in z.namelist():
                        with z.open("itinerary_backup.json") as f:
                            backup_data = json.loads(f.read().decode("utf-8"))
                            
                            temp_prompt = backup_data.get("user_prompt", "")
                            temp_total = backup_data.get("total_days", 7)
                            raw_days = backup_data.get("days_data", {})
                            
                            temp_days = {}
                            for k, v in raw_days.items():
                                temp_days[int(k)] = DayItinerary.model_validate(v)
                            
                            st.session_state.user_prompt_val = temp_prompt
                            st.session_state.total_days_val = temp_total
                            st.session_state.itinerary_days = temp_days
                            st.session_state.last_uploaded_file_name = uploaded_file.name
                            
                            st.success("✨ 行程已 100% 精準還原！")
                            st.rerun()
                    else:
                        st.error("此壓縮包內未包含有效的 itinerary_backup.json 檔案。")
            except Exception as e:
                st.error(f"還原失敗：{str(e)}")

    progress_sidebar = st.empty()

if btn_generate:
    st.session_state.user_prompt_val = user_prompt
    st.session_state.total_days_val = total_days
    st.session_state.itinerary_days = {}
    
    sidebar_progress_bar = progress_sidebar.progress(0.0)
        
    for d in range(1, total_days + 1):
        context_str = "\n".join([f"Day {k}: {v.day_title}" for k, v in st.session_state.itinerary_days.items()])
        
        day_result = st.session_state.brain.generate_day_itinerary(
            user_prompt=user_prompt,
            total_days=total_days,
            current_day=d,
            previous_days_context=context_str,
            start_country=start_country,
            departure_time=departure_time,
            flight_hours=flight_hours,
            timezone_diff=timezone_diff
        )
        st.session_state.itinerary_days[d] = day_result
        sidebar_progress_bar.progress(float(d) / float(total_days))
    progress_sidebar.success("🎉 全行程編排完成！")

if st.session_state.itinerary_days:
    st.header(f"🗺️ 行程：{st.session_state.user_prompt_val}")
    
    for day_counter in sorted(st.session_state.itinerary_days.keys()):
        day_data: DayItinerary = st.session_state.itinerary_days[day_counter]
        
        with st.expander(f"📅 第 {day_counter} 天：{day_data.day_title}", expanded=True):
            st.markdown(f'<div class="day-header">📅 第 {day_counter} 天：{day_data.day_title}</div>', unsafe_allow_html=True)
            for spot in day_data.spots:
                st.markdown(f"""
                <div class="spot-card">
                    <span style="font-weight: bold; color: #1e293b;">⏱️ {spot.time} - {spot.name}</span>
                    <p style="color: #475569; font-size: 0.95rem; margin-top: 6px;">{spot.description}</p>
                    <div class="trans-capsule">{get_transport_icon(spot.transportation)} {spot.transportation}</div>
                    <div style="font-size: 0.88rem; color: #64748b;">🎫 <b>購票：</b>{spot.booking_info} | 💳 <b>費用：</b>{spot.estimated_spending}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if spot.alternatives:
                    st.markdown('<div class="alt-box">💡 <b>老導遊備案：</b>', unsafe_allow_html=True)
                    for alt in spot.alternatives:
                        st.markdown(f"• 🍴 **{alt.name.replace('<b>','').replace('</b>','')}**：{alt.desc}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button(f"🗺️ Google Maps: {spot.name}", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot.map_keyword)}", use_container_width=True)
                with col2:
                    if spot.ticket_link_query != "FREE":
                        st.link_button(f"🎫 搜尋購票連結", f"https://www.google.com/search?q={urllib.parse.quote(spot.ticket_link_query)}", use_container_width=True)
            
            # 飯店資訊渲染
            hotel = day_data.hotel
            has_hotel = "無（" not in hotel.name
            
            st.markdown(f"""
            <div class="hotel-card" style="border-left-color: {'#3b82f6' if has_hotel else '#94a3b8'}; background-color: {'#f8fafc' if has_hotel else '#f1f5f9'};">
                <span style="font-weight: bold; color: {'#1e3a8a' if has_hotel else '#475569'};">🏨 下榻建議：{hotel.name}</span>
                <p style="color: #334155; font-size: 0.95rem; margin-top: 6px;">{hotel.description}</p>
                <div style="font-size: 0.88rem;">ℹ️ {hotel.booking_info} | 💳 每晚：{hotel.estimated_spending}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if has_hotel and hotel.alternatives:
                st.markdown('<div class="alt-box" style="border-left: 3px solid #3b82f6;">🏨 <b>精選下榻備案分流：</b>', unsafe_allow_html=True)
                for alt_h in hotel.alternatives:
                    st.markdown(f"• 🏨 **{alt_h.name.replace('<b>','').replace('</b>','')}**：{alt_h.desc}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            if has_hotel:
                st.link_button(f"🗺️ 地圖查看飯店：{hotel.name}", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(hotel.map_keyword)}", use_container_width=True)

            st.markdown("---")
            refine_input = st.text_input("微調此天行程：", placeholder="例如：我想換這間餐廳...", key=f"ref_{day_counter}")
            if st.button("🎯 立即微調", key=f"btn_{day_counter}"):
                if refine_input.strip() != "":
                    with st.spinner("調校中..."):
                        st.session_state.itinerary_days[day_counter] = st.session_state.brain.refine_day_itinerary(st.session_state.user_prompt_val, day_data, refine_input)
                        st.rerun()

    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    st.subheader("💾 行程導出與時光機存檔備份 (.ZIP)")
    
    clean_prompt = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', st.session_state.user_prompt_val).split()
    file_base_name = f"{clean_prompt[0] if clean_prompt else '我的專案行程'}_{st.session_state.total_days_val}天_精緻旅遊行程"
    
    export_dict = {
        "user_prompt": st.session_state.user_prompt_val,
        "total_days": st.session_state.total_days_val,
        "days_data": {str(k): v.model_dump() for k, v in st.session_state.itinerary_days.items()}
    }
    json_string = json.dumps(export_dict, ensure_ascii=False, indent=2)
    
    txt_buffer = io.StringIO()
    txt_buffer.write("=== 全球智慧旅遊助手 專屬行程 ===\n\n")
    txt_buffer.write(f"[使用者旅遊意向]：{st.session_state.user_prompt_val}\n\n")
    
    for d_key in sorted(st.session_state.itinerary_days.keys()):
        d_obj: DayItinerary = st.session_state.itinerary_days[d_key]
        txt_buffer.write(f"-----------------------------------------\n")
        txt_buffer.write(f"📅 第 {d_key} 天：{d_obj.day_title}\n")
        txt_buffer.write(f"-----------------------------------------\n")
        for sp in d_obj.spots:
            txt_buffer.write(f"⏱️ 時間：{sp.time}\n")
            txt_buffer.write(f"📍 景點/餐廳：{sp.name}\n")
            txt_buffer.write(f"📝 介紹：{sp.description}\n")
            txt_buffer.write(f"🚇 交通指引：{sp.transportation}\n")
            txt_buffer.write(f"🎫 購票攻略：{sp.booking_info}\n")
            txt_buffer.write(f"💳 預估費用：{sp.estimated_spending}\n\n")
        txt_buffer.write(f"🏨 當晚住宿：{d_obj.hotel.name}\n")
        txt_buffer.write(f"📝 住宿描述：{d_obj.hotel.description}\n")
        txt_buffer.write(f"💳 住宿費用：{d_obj.hotel.estimated_spending}\n\n\n")
        
    txt_string = txt_buffer.getvalue()
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("itinerary_backup.json", json_string.encode("utf-8"))
        zip_file.writestr("itinerary_details.txt", txt_string.encode("utf-8"))
        
    st.download_button(
        label="🎁 下載完整行程備份包 (.ZIP)",
        data=zip_buffer.getvalue(),
        file_name=f"{file_base_name}.zip",
        mime="application/zip",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)