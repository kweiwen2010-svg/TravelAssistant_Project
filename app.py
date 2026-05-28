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
    .welcome-box { background-color: rgba(30, 41, 59, 0.05); padding: 22px; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.3); margin-bottom: 25px; color: inherit; }
    .welcome-box h4 { color: inherit !important; margin-top: 0px; }
    .day-header { background: linear-gradient(90deg, #1e293b 0%, #334155 100%); color: white; padding: 12px 20px; border-radius: 6px; font-weight: bold; margin-top: 35px; }
    .spot-card { background-color: #ffffff; padding: 18px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); color: #1e293b !important; }
    .spot-card p, .spot-card span, .spot-card div { color: #1e293b !important; }
    .hotel-card { background-color: #f8fafc; padding: 18px; border-radius: 8px; border-left: 5px solid #3b82f6; margin-top: 20px; color: #1e293b !important; }
    .hotel-card p, .hotel-card span, .hotel-card div { color: #1e293b !important; }
    .trans-capsule { display: inline-block; background-color: #f1f5f9; color: #475569 !important; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; margin: 8px 0; border: 1px solid #e2e8f0; }
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

def safe_int(val) -> int:
    if val is None: return 0
    if isinstance(val, (int, float)): return int(val)
    try:
        clean_str = re.sub(r'[^\d]', '', str(val))
        return int(clean_str) if clean_str else 0
    except:
        return 0

# 狀態初始化
if "brain" not in st.session_state: st.session_state.brain = TravelBrain()
if "itinerary_days" not in st.session_state: st.session_state.itinerary_days = {}
if "user_prompt_val" not in st.session_state: st.session_state.user_prompt_val = ""
if "total_days_val" not in st.session_state: st.session_state.total_days_val = 7
if "is_generating" not in st.session_state: st.session_state.is_generating = False

with st.sidebar:
    st.header("⏳ 歷史行程時光機")
    uploaded_file = st.file_uploader("📦 載入歷史行程存檔 (.zip)", type=["zip"])
    if uploaded_file is not None:
        try:
            with zipfile.ZipFile(uploaded_file, 'r') as z:
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
        except Exception as e:
            st.error(f"解析 ZIP 失敗：{str(e)}")

    st.write("---")
    st.header("⚙️ 旅遊核心設定")
    user_prompt = st.text_area("🔮 旅遊意向或旅行社行程貼上：", value="瑞士 人文 美食 購物 古蹟")
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

    if st.session_state.itinerary_days:
        st.write("---")
        st.header("💾 行程備份導出")
        clean_prompt = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', st.session_state.user_prompt_val).split()
        file_base_name = f"{clean_prompt[0] if clean_prompt else '我的專案行程'}_{len(st.session_state.itinerary_days)}天_行程存檔"
        
        export_dict = {
            "user_prompt": st.session_state.user_prompt_val,
            "sidebar_flight_cost": sidebar_flight_cost,
            "days_data": {str(k): v.model_dump() for k, v in st.session_state.itinerary_days.items()}
        }
        json_string = json.dumps(export_dict, ensure_ascii=False, indent=2)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{file_base_name}.json", json_string.encode("utf-8"))
        
        st.download_button(label="📦 下載當前行程存檔 (.zip)", data=zip_buffer.getvalue(), file_name=f"{file_base_name}.zip", mime="application/zip", use_container_width=True)

# 狀態觸發與遞迴步進生成核心
if btn_generate:
    st.session_state.itinerary_days = {}
    st.session_state.is_generating = True
    st.session_state.user_prompt_val = user_prompt
    st.session_state.total_days_val = total_days
    st.session_state.start_country_val = start_country
    st.session_state.departure_time_val = departure_time
    st.session_state.flight_hours_val = flight_hours
    st.session_state.timezone_diff_val = timezone_diff
    st.rerun()

if st.session_state.is_generating:
    target_total = st.session_state.total_days_val
    current_done = len(st.session_state.itinerary_days)
    if current_done < target_total:
        next_day = current_done + 1
        sidebar_progress_bar = progress_sidebar.progress(float(current_done) / float(target_total))
        
        # 核心記憶線：將前幾天的天數與標題串接，強迫大腦保持時空連貫
        context_str = "\n".join([f"Day {k}: {v.day_title}" for k, v in sorted(st.session_state.itinerary_days.items())])
        
        day_result = st.session_state.brain.generate_day_itinerary(
            st.session_state.user_prompt_val, target_total, next_day, context_str,
            st.session_state.get('start_country_val', '台灣台北 (TPE)'), st.session_state.get('departure_time_val', '晚上 23:30'),
            st.session_state.get('flight_hours_val', 14.0), st.session_state.get('timezone_diff_val', -6.0)
        )
        st.session_state.itinerary_days[next_day] = day_result
        st.rerun()
    else:
        st.session_state.is_generating = False
        st.rerun()

# 渲染看板與折疊卡片
if st.session_state.itinerary_days:
    st.header(f"🗺️ 行程：{st.session_state.user_prompt_val[:20]}...")
    total_flight_cost = safe_int(sidebar_flight_cost)
    total_hotel_cost = 0
    total_local_transport_cost = 0
    total_food_ticket_cost = 0
    
    for day_counter in sorted(st.session_state.itinerary_days.keys()):
        day_data: DayItinerary = st.session_state.itinerary_days[day_counter]
        if getattr(day_data, 'hotel', None):
            h_cost = getattr(day_data.hotel, 'estimated_spending', 0) or getattr(day_data.hotel, 'estimated_cost', 0)
            total_hotel_cost += safe_int(h_cost)
        if getattr(day_data, 'spots', None):
            for spot in day_data.spots:
                total_food_ticket_cost += safe_int(getattr(spot, 'estimated_spending', 0))
                t_cost = getattr(spot, 'estimated_transport_cost', None) or getattr(spot, 'transport_cost', None) or getattr(spot, 'estimated_transportation_cost', 0)
                total_local_transport_cost += safe_int(t_cost)

    total_rigid_cost = total_flight_cost + total_hotel_cost + total_local_transport_cost + total_food_ticket_cost
    st.markdown('<div class="budget-box">', unsafe_allow_html=True)
    st.subheader("💰 本次旅遊剛性預算精算概估 (四大維度全面解耦)")
    if total_rigid_cost > 0:
        flight_pct = (total_flight_cost / total_rigid_cost) * 100
        hotel_pct = (total_hotel_cost / total_rigid_cost) * 100
        trans_pct = (total_local_transport_cost / total_rigid_cost) * 100
        food_pct = (total_food_ticket_cost / total_rigid_cost) * 100
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📊 預估剛性總花費", f"NT$ {total_rigid_cost:,}")
        c2.metric("✈️ 國際機票總計", f"NT$ {total_flight_cost:,}", f"{flight_pct:.1f}%")
        c3.metric("🏨 住宿總預算", f"NT$ {total_hotel_cost:,}", f"{hotel_pct:.1f}%")
        c4.metric("🚇 當地交通车資", f"NT$ {total_local_transport_cost:,}", f"{trans_pct:.1f}%")
        c5.metric("🍱 純餐飲與門票", f"NT$ {total_food_ticket_cost:,}", f"{food_pct:.1f}%")
    st.markdown('</div>', unsafe_allow_html=True)

    # 依序渲染每天的卡片，預設 expanded=False 優化手機單手操作
    for day_counter in sorted(st.session_state.itinerary_days.keys()):
        day_data: DayItinerary = st.session_state.itinerary_days[day_counter]
        with st.expander(f"📅 第 {day_counter} 天：{day_data.day_title}", expanded=False):
            st.markdown(f'<div class="day-header">📅 第 {day_counter} 天：{day_data.day_title}</div>', unsafe_allow_html=True)
            for spot in day_data.spots:
                spot_t_cost = safe_int(getattr(spot, 'estimated_transport_cost', None) or getattr(spot, 'transport_cost', None) or getattr(spot, 'estimated_transportation_cost', 0))
                st.markdown(f'<div class="spot-card"><span style="font-weight: bold; color: #1e293b;">⏱️ {spot.time} - {spot.name}</span><p style="color: #475569; font-size: 0.95rem; margin-top: 6px;">{spot.description}</p><div class="trans-capsule">{get_transport_icon(spot.transportation)} {spot.transportation}</div><div style="font-size: 0.88rem; color: #64748b;">🎫 <b>購票：</b>{spot.booking_info} | 🍱 <b>純餐飲門票：</b>NT$ {safe_int(spot.estimated_spending):,} | 🚇 <b>車資支出：</b>NT$ {spot_t_cost:,}</div></div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1: st.link_button(f"🗺️ Maps: {spot.name}", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot.map_keyword)}", use_container_width=True)
                with col2:
                    if spot.ticket_link_query != "FREE": st.link_button(f"🎫 搜尋購票", f"https://www.google.com/search?q={urllib.parse.quote(spot.ticket_link_query)}", use_container_width=True)
            hotel = day_data.hotel
            h_spending = safe_int(getattr(hotel, 'estimated_spending', 0) or getattr(hotel, 'estimated_cost', 0))
            st.markdown(f'<div class="hotel-card"><span style="font-weight: bold; color: #1e3a8a;">🏨 下榻建議：{hotel.name}</span><p style="color: #334155; font-size: 0.95rem; margin-top: 6px;">{hotel.description}</p><div style="font-size: 0.88rem;">ℹ️ {hotel.booking_info} | 💳 每晚：NT$ {h_spending:,}</div></div>', unsafe_allow_html=True)