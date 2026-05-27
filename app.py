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
    .download-section { border: 1px solid rgba(148, 163, 184, 0.3); padding: 20px; border-radius: 8px; margin-top: 40px; background-color: rgba(30, 41, 59, 0.02); }
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
st.markdown('<div class="welcome-box"><h4>🌐 V3.4.4 剛性預算精算版</h4>已無損對接底層資料型態。全行程生成完畢後，系統將自動提取『住宿費』與『餐飲景點費』進行精算，並以百分比與圖表即時呈現在手機端！</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 旅遊核心設定")
    user_prompt = st.text_area("🔮 旅遊意向：", value="義大利 人文 美食 購物 古蹟")
    total_days = st.number_input("📅 總天數：", min_value=1, max_value=30, value=7, step=1)
    
    st.subheader("🛫 航班與時區參數")
    start_country = st.text_input("📍 出發地地標：", value="台灣台北 (TPE)")
    departure_time = st.text_input("⏰ 第 1 天起飛時間點：", value="晚上 23:30")
    flight_hours = st.number_input("⏱️ 飛行總時間 (小時)：", min_value=0.5, max_value=40.0, value=14.0, step=0.5)
    timezone_diff = st.number_input("🌐 目的地時差 (比台灣慢請填負數)：", min_value=-12.0, max_value=12.0, value=-6.0, step=1.0)
    
    col_gen, col_clear = st.columns(2)
    with col_gen: btn_generate = st.button("🚀 啟動大腦生成", type="primary", use_container_width=True, disabled=st.session_state.is_generating)
    with col_clear:
        if st.button("🧹 清空重置", type="secondary", use_container_width=True):
            st.session_state.itinerary_days = {}
            st.session_state.user_prompt_val = ""
            st.session_state.is_generating = False
            if "last_uploaded_file_name" in st.session_state: del st.session_state.last_uploaded_file_name
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
                            temp_days = {}
                            for k, v in backup_data.get("days_data", {}).items():
                                # 兼容舊版字串花費轉型為整數
                                if "spots" in v:
                                    for s in v["spots"]:
                                        if isinstance(s.get("estimated_spending"), str):
                                            s["estimated_spending"] = int(re.sub(r'\D', '', s["estimated_spending"])) if re.sub(r'\D', '', s["estimated_spending"]) else 0
                                if "hotel" in v and isinstance(v["hotel"].get("estimated_spending"), str):
                                    v["hotel"]["estimated_spending"] = int(re.sub(r'\D', '', v["hotel"]["estimated_spending"])) if re.sub(r'\D', '', v["hotel"]["estimated_spending"]) else 0
                                temp_days[int(k)] = DayItinerary.model_validate(v)
                            st.session_state.user_prompt_val = backup_data.get("user_prompt", "")
                            st.session_state.total_days_val = backup_data.get("total_days", 7)
                            st.session_state.itinerary_days = temp_days
                            st.session_state.is_generating = False
                            st.session_state.last_uploaded_file_name = uploaded_file.name
                            st.success("✨ 行程已 100% 精準還原！")
                            st.rerun()
            except Exception as e: st.error(f"還原失敗：{str(e)}")
    progress_sidebar = st.empty()

if btn_generate:
    st.session_state.itinerary_days = {}
    st.session_state.is_generating = True
    capture_sidebar_inputs(user_prompt, total_days, start_country, departure_time, flight_hours, timezone_diff)
    st.rerun()

if st.session_state.is_generating:
    target_total = st.session_state.total_days_val
    current_done = len(st.session_state.itinerary_days)
    if current_done < target_total:
        next_day = current_done + 1
        sidebar_progress_bar = progress_sidebar.progress(float(current_done) / float(target_total))
        context_str = "\n".join([f"Day {k}: {v.day_title}" for k, v in sorted(st.session_state.itinerary_days.items())])
        day_result = st.session_state.brain.generate_day_itinerary(
            st.session_state.user_prompt_val, target_total, next_day, context_str,
            st.session_state.get('start_country_val', '台灣台北 (TPE)'),
            st.session_state.get('departure_time_val', '晚上 23:30'),
            st.session_state.get('flight_hours_val', 14.0),
            st.session_state.get('timezone_diff_val', -6.0)
        )
        st.session_state.itinerary_days[next_day] = day_result
        st.rerun()
    else:
        st.session_state.is_generating = False
        progress_sidebar.success("🎉 全行程編排完成！")
        st.rerun()

# 渲染介面
if st.session_state.itinerary_days:
    st.header(f"🗺️ 行程：{st.session_state.user_prompt_val}")
    
    total_hotel_cost = 0
    total_spot_cost = 0
    
    for day_counter in sorted(st.session_state.itinerary_days.keys()):
        day_data: DayItinerary = st.session_state.itinerary_days[day_counter]
        
        # 累加計算費用
        total_hotel_cost += day_data.hotel.estimated_spending
        total_spot_cost += sum([spot.estimated_spending for spot in day_data.spots])
        
        with st.expander(f"📅 第 {day_counter} 天：{day_data.day_title}", expanded=True):
            st.markdown(f'<div class="day-header">📅 第 {day_counter} 天：{day_data.day_title}</div>', unsafe_allow_html=True)
            for spot in day_data.spots:
                st.markdown(f'<div class="spot-card"><span style="font-weight: bold; color: #1e293b;">⏱️ {spot.time} - {spot.name}</span><p style="color: #475569; font-size: 0.95rem; margin-top: 6px;">{spot.description}</p><div class="trans-capsule">{get_transport_icon(spot.transportation)} {spot.transportation}</div><div style="font-size: 0.88rem; color: #64748b;">🎫 <b>購票：</b>{spot.booking_info} | 💳 <b>費用：</b>NT$ {spot.estimated_spending:,}</div></div>', unsafe_allow_html=True)
                if spot.alternatives:
                    st.markdown('<div class="alt-box">💡 <b>老導遊備案：</b>', unsafe_allow_html=True)
                    for alt in spot.alternatives: st.markdown(f"• 🍴 **{alt.name}**：{alt.desc}")
                    st.markdown('</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1: st.link_button(f"🗺️ Google Maps: {spot.name}", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot.map_keyword)}", use_container_width=True)
                with col2:
                    if spot.ticket_link_query != "FREE": st.link_button(f"🎫 搜尋購票連結", f"https://www.google.com/search?q={urllib.parse.quote(spot.ticket_link_query)}", use_container_width=True)
            
            hotel = day_data.hotel
            has_hotel = "無（" not in hotel.name
            st.markdown(f'<div class="hotel-card" style="border-left-color: {"#3b82f6" if has_hotel else "#94a3b8"}; background-color: {"#f8fafc" if has_hotel else "#f1f5f9"};"><span style="font-weight: bold; color: {"#1e3a8a" if has_hotel else "#475569"};">🏨 下榻建議：{hotel.name}</span><p style="color: #334155; font-size: 0.95rem; margin-top: 6px;">{hotel.description}</p><div style="font-size: 0.88rem;">ℹ️ {hotel.booking_info} | 💳 每晚：NT$ {hotel.estimated_spending:,}</div></div>', unsafe_allow_html=True)
            if has_hotel and hotel.alternatives:
                st.markdown('<div class="alt-box" style="border-left: 3px solid #3b82f6;">🏨 <b>精選下榻備案分流：</b>', unsafe_allow_html=True)
                for alt_h in hotel.alternatives: st.markdown(f"• 🏨 **{alt_h.name}**：{alt_h.desc}")
                st.markdown('</div>', unsafe_allow_html=True)
            if has_hotel: st.link_button(f"🗺️ 地圖查看飯店：{hotel.name}", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(hotel.map_keyword)}", use_container_width=True)
            st.markdown("---")
            refine_input = st.text_input("微調此天行程：", placeholder="例如：我想換這間餐廳...", key=f"ref_{day_counter}")
            if st.button("🎯 立即微調", key=f"btn_{day_counter}"):
                if refine_input.strip() != "":
                    with st.spinner("調校中..."):
                        st.session_state.itinerary_days[day_counter] = st.session_state.brain.refine_day_itinerary(st.session_state.user_prompt_val, day_data, refine_input)
                        st.rerun()

    # 💰 剛性預算精算視覺化區塊
    total_rigid_cost = total_hotel_cost + total_spot_cost
    st.markdown('<div class="budget-box">', unsafe_allow_html=True)
    st.subheader("💰 本次旅遊剛性預算概估（排除購物變數）")
    
    if total_rigid_cost > 0:
        hotel_pct = (total_hotel_cost / total_rigid_cost) * 100
        spot_pct = (total_spot_cost / total_rigid_cost) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 預估剛性總花費", f"NT$ {total_rigid_cost:,}")
        c2.metric("🏨 總住宿預算", f"NT$ {total_hotel_cost:,}", f"{hotel_pct:.1f}%")
        c3.metric("🍱 總餐飲門票與交通", f"NT$ {total_spot_cost:,}", f"{spot_pct:.1f}%")
        
        st.markdown("**📉 預算分配比例結構：**")
        st.markdown(f"🏨 住宿花費占比 ({hotel_pct:.1f}%)")
        st.progress(hotel_pct / 100.0)
        st.markdown(f"🍱 餐飲景點交通占比 ({spot_pct:.1f}%)")
        st.progress(spot_pct / 100.0)
    else:
        st.info("暫無費用支出數據。")
    st.markdown('</div>', unsafe_allow_html=True)

    # 存檔導出
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    st.subheader("💾 行程導出與時光機存檔備份 (.ZIP)")
    clean_prompt = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', st.session_state.user_prompt_val).split()
    file_base_name = f"{clean_prompt[0] if clean_prompt else '我的專案行程'}_{st.session_state.total_days_val}天_精緻旅遊行程"
    export_dict = {"user_prompt": st.session_state.user_prompt_val, "total_days": st.session_state.total_days_val, "days_data": {str(k): v.model_dump() for k, v in st.session_state.itinerary_days.items()}}
    json_string = json.dumps(export_dict, ensure_ascii=False, indent=2)
    
    txt_buffer = io.StringIO()
    txt_buffer.write("=== 全球智慧旅遊助手 專屬行程 ===\n\n")
    for d_key in sorted(st.session_state.itinerary_days.keys()):
        d_obj: DayItinerary = st.session_state.itinerary_days[d_key]
        txt_buffer.write(f"-----------------------------------------\n📅 第 {d_key} 天：{d_obj.day_title}\n-----------------------------------------\n")
        for sp in d_obj.spots: txt_buffer.write(f"⏱️ 時間：{sp.time}\n📍 景點/餐廳：{sp.name}\n📝 介紹：{sp.description}\n🚇 交通：{sp.transportation}\n💳 費用：NT$ {sp.estimated_spending:,}\n\n")
        txt_buffer.write(f"🏨 當晚住宿：{d_obj.hotel.name} | 房價：NT$ {d_obj.hotel.estimated_spending:,}\n\n\n")
    txt_buffer.write(f"=== 💰 總預算剛性估算 ===\n總計花費：NT$ {total_rigid_cost:,}\n住宿總計：NT$ {total_hotel_cost:,}\n餐飲交通總計：NT$ {total_spot_cost:,}\n")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("itinerary_backup.json", json_string.encode("utf-8"))
        zip_file.writestr("itinerary_details.txt", txt_buffer.getvalue().encode("utf-8"))
    st.download_button(label="🎁 下載完整行程備份包 (.ZIP)", data=zip_buffer.getvalue(), file_name=f"{file_base_name}.zip", mime="application/zip", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)