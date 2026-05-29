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
st.markdown('<div class="welcome-box"><h4>🌐 V3.4.5 四大剛性預算精細版</h4>已成功將『交通費』與『餐飲門票』獨立解耦，並在全局完美引入『國際來回機票』預算估算！</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 旅遊核心設定")
    user_prompt = st.text_area("🔮 旅遊意向：", value="瑞士 人文 美食 購物 古蹟")
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
            st.rerun()

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
        st.rerun()

if st.session_state.itinerary_days:
    st.header(f"🗺️ 行程：{st.session_state.user_prompt_val}")
    
    total_flight_cost = 0
    total_hotel_cost = 0
    total_local_transport_cost = 0
    total_food_ticket_cost = 0
    
    for day_counter in sorted(st.session_state.itinerary_days.keys()):
        day_data: DayItinerary = st.session_state.itinerary_days[day_counter]
        
        # 🛡️ 提取四大核心費用並執行防呆轉型
        try: total_flight_cost += int(getattr(day_data, 'estimated_flight_cost', 0))
        except: pass
        try: total_hotel_cost += int(day_data.hotel.estimated_spending) if day_data.hotel.estimated_spending else 0
        except: pass
        
        for spot in day_data.spots:
            try: total_food_ticket_cost += int(spot.estimated_spending) if spot.estimated_spending else 0
            except: pass
            try: total_local_transport_cost += int(getattr(spot, 'estimated_transport_cost', 0))
            except: pass
        
        with st.expander(f"📅 第 {day_counter} 天：{day_data.day_title}", expanded=True):
            st.markdown(f'<div class="day-header">📅 第 {day_counter} 天：{day_data.day_title}</div>', unsafe_allow_html=True)
            for spot in day_data.spots:
                spot_t_cost = getattr(spot, 'estimated_transport_cost', 0)
                st.markdown(f'<div class="spot-card"><span style="font-weight: bold; color: #1e293b;">⏱️ {spot.time} - {spot.name}</span><p style="color: #475569; font-size: 0.95rem; margin-top: 6px;">{spot.description}</p><div class="trans-capsule">{get_transport_icon(spot.transportation)} {spot.transportation}</div><div style="font-size: 0.88rem; color: #64748b;">🎫 <b>購票：</b>{spot.booking_info} | 🍱 <b>純餐飲門票：</b>NT$ {spot.estimated_spending:,} | 🚇 <b>車資支出：</b>NT$ {spot_t_cost:,}</div></div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1: st.link_button(f"🗺️ Google Maps: {spot.name}", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot.map_keyword)}", use_container_width=True)
                with col2:
                    if spot.ticket_link_query != "FREE": st.link_button(f"🎫 搜尋購票連結", f"https://www.google.com/search?q={urllib.parse.quote(spot.ticket_link_query)}", use_container_width=True)
            
            hotel = day_data.hotel
            has_hotel = "無（" not in hotel.name
            st.markdown(f'<div class="hotel-card" style="border-left-color: {"#3b82f6" if has_hotel else "#94a3b8"}; background-color: {"#f8fafc" if has_hotel else "#f1f5f9"};"><span style="font-weight: bold; color: {"#1e3a8a" if has_hotel else "#475569"};">🏨 下榻建議：{hotel.name}</span><p style="color: #334155; font-size: 0.95rem; margin-top: 6px;">{hotel.description}</p><div style="font-size: 0.88rem;">ℹ️ {hotel.booking_info} | 💳 每晚：NT$ {hotel.estimated_spending:,}</div></div>', unsafe_allow_html=True)
            if has_hotel: st.link_button(f"🗺️ 地圖查看飯店：{hotel.name}", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(hotel.map_keyword)}", use_container_width=True)

    # 💰 四大剛性預算精算視覺化區塊
    total_rigid_cost = total_flight_cost + total_hotel_cost + total_local_transport_cost + total_food_ticket_cost
    st.markdown('<div class="budget-box">', unsafe_allow_html=True)
    st.subheader("💰 本次旅遊剛性預算精算概估（四大維度解耦）")
    
    if total_rigid_cost > 0:
        flight_pct = (total_flight_cost / total_rigid_cost) * 100
        hotel_pct = (total_hotel_cost / total_rigid_cost) * 100
        trans_pct = (total_local_transport_cost / total_rigid_cost) * 100
        food_pct = (total_food_ticket_cost / total_rigid_cost) * 100
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📊 預估剛性總花費", f"NT$ {total_rigid_cost:,}")
        c2.metric("✈️ 國際機票總計", f"NT$ {total_flight_cost:,}", f"{flight_pct:.1f}%")
        c3.metric("🏨 住宿總預算", f"NT$ {total_hotel_cost:,}", f"{hotel_pct:.1f}%")
        c4.metric("🚇 當地交通車資", f"NT$ {total_local_transport_cost:,}", f"{trans_pct:.1f}%")
        c5.metric("🍱 純餐飲與門票", f"NT$ {total_food_ticket_cost:,}", f"{food_pct:.1f}%")
        
        st.markdown("**📉 預算分配比例結構：**")
        st.markdown(f"✈️ 國際機票占比 ({flight_pct:.1f}%)")
        st.progress(flight_pct / 100.0)
        st.markdown(f"🏨 住宿花費占比 ({hotel_pct:.1f}%)")
        st.progress(hotel_pct / 100.0)
        st.markdown(f"🚇 當地交通占比 ({trans_pct:.1f}%)")
        st.progress(trans_pct / 100.0)
        st.markdown(f"🍱 純餐飲門票占比 ({food_pct:.1f}%)")
        st.progress(food_pct / 100.0)
    else:
        st.info("暫無費用支出數據。")
    st.markdown('</div>', unsafe_allow_html=True)