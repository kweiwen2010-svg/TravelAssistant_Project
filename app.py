import streamlit as st
import urllib.parse
import os
import re
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
from core.brain_25 import TravelBrain, DayItinerary

# 網頁初始化配置
st.set_page_config(page_title="全球智慧旅遊助手 2.5", page_icon="✈️", layout="wide")

# ===========================================================================
# 注入精緻且絕對穩定的安全 UI 樣式表 (CSS)
# ===========================================================================
st.markdown("""
<style>
    .spot-card { background-color: #f8f9fa; padding: 18px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; }
    .hotel-card { background-color: #f0f7ff; padding: 18px; border-radius: 8px; border-left: 5px solid #0284c7; margin-top: 20px; margin-bottom: 15px; }
    .time-badge { color: #ff4b4b; font-weight: bold; font-size: 1.1rem; }
    .hotel-badge { color: #0284c7; font-weight: bold; font-size: 1.1rem; }
    .spot-name { font-weight: bold; font-size: 1.2rem; color: #1e293b; }
    .info-sub-block { font-size: 0.95rem; color: #475569; background-color: #ffffff; padding: 8px 12px; border-radius: 6px; margin-top: 6px; border: 1px solid #e2e8f0; }
    .tip-box { background-color: #f8fafc; padding: 12px; border-radius: 8px; border: 1px dashed #cbd5e1; margin-top: 15px; }
    .download-section { background-color: #f1f5f9; padding: 20px; border-radius: 10px; margin-top: 30px; border: 1px solid #cbd5e1; }
</style>
""", unsafe_allow_html=True)

st.title("✈️ 全球智慧旅遊助手 2.5 (Structured UI Edition)")
st.caption("基於 Gemini 2.5 Flash 大腦 • 純原生無鏈結高穩定版")

# 初始化 Session State
if "brain" not in st.session_state: st.session_state.brain = TravelBrain()
if "itinerary_days" not in st.session_state: st.session_state.itinerary_days = {}
if "is_generating" not in st.session_state: st.session_state.is_generating = False

# 格式化文字檔案下載函數
def prepare_download_text(prompt, sorted_days_keys):
    download_text = f"=== 全球智慧旅遊助手 專屬行程 ===\n\n[使用者旅遊意向]\n{prompt}\n\n"
    for cb in sorted_days_keys:
        d_obj: DayItinerary = st.session_state.itinerary_days[cb]
        download_text += f"-----------------------------------------\n📅 第 {cb} 天：{d_obj.day_title}\n-----------------------------------------\n"
        for sp in d_obj.spots:
            download_text += f"⏱️ 時間：{sp.time}\n📍 景點/餐廳：{sp.name}\n📝 介紹：{sp.description}\n"
            if getattr(sp, 'alternatives', []):
                alt_strs = [f"{a.name}({a.desc})" for a in sp.alternatives]
                download_text += f"🔄 備案選擇：{', '.join(alt_strs)}\n"
            download_text += f"\n"
        download_text += f"🏠 當晚住宿：{d_obj.recommended_hotel.name}\n"
        if getattr(d_obj, 'alternative_hotels', []):
            alt_h_strs = [f"{h.name}({h.desc})" for h in d_obj.alternative_hotels]
            download_text += f"🔄 住宿備案：{', '.join(alt_h_strs)}\n"
        download_text += f"\n"
    return download_text

# ===========================================================================
# 側邊欄：設定區塊
# ===========================================================================
with st.sidebar:
    st.header("📋 旅遊意向設定")
    user_prompt = st.text_area("輸入您的旅遊靈感與偏好：", value="我想去土耳其10天 老婆同遊 美食 人文 風景 行程不要太趕", height=150, disabled=st.session_state.is_generating)
    total_days = st.number_input("規劃天數", min_value=1, max_value=15, value=10, disabled=st.session_state.is_generating)
    generate_btn = st.button("🚀 開始全自動分段生成", type="primary", use_container_width=True, disabled=st.session_state.is_generating)
    if st.button("🧹 清除目前行程方案", use_container_width=True, disabled=st.session_state.is_generating):
        st.session_state.itinerary_days = {}
        st.success("行程已成功重設！")
        st.rerun()

# 點擊生成行程
if generate_btn:
    st.session_state.is_generating = True
    st.session_state.itinerary_days = {}  
    st.rerun()

# ===========================================================================
# 核心調用邏輯：循序漸進生成行程
# ===========================================================================
if st.session_state.is_generating and not st.session_state.itinerary_days:
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    previous_summary_context = ""
    error_occurred = False
    
    for current_day in range(1, total_days + 1):
        status_text.markdown(f"⏳ **正在利用大腦深度規劃：第 {current_day} 天...** (正在同時建立高穩定備案清單)")
        try:
            day_data: DayItinerary = st.session_state.brain.generate_day_itinerary(user_prompt=user_prompt, day_idx=current_day, previous_context=previous_summary_context)
            st.session_state.itinerary_days[current_day] = day_data
            previous_summary_context += f"第 {current_day} 天主題: {day_data.day_title}，住宿: {day_data.recommended_hotel.name}。\n"
            progress_bar.progress(current_day / total_days)
        except Exception as e:
            error_occurred = True
            st.error(f"❌ **規劃中斷：** {str(e)}")
            break
            
    progress_bar.empty()
    status_text.empty()
    st.session_state.is_generating = False
    if not error_occurred: st.rerun()

# ===========================================================================
# 前端畫面渲染區：完全移除 HTML 拼接，改用原生元件與純 Markdown
# ===========================================================================
if st.session_state.itinerary_days:
    st.subheader("🗺️ 您專屬的客製化行程明細")
    sorted_days = sorted(st.session_state.itinerary_days.keys())
    
    for day_counter in sorted_days:
        day_data: DayItinerary = st.session_state.itinerary_days[day_counter]
        with st.expander(f"📅 第 {day_counter} 天：{day_data.day_title}", expanded=True):
            
            # --- 1. 渲染當日的所有景點/餐廳卡片 ---
            for spot in day_data.spots:
                spending_val = spot.estimated_spending if getattr(spot, 'estimated_spending', None) else "現場評估"
                
                # 標準、乾淨且獨立封閉的主卡片區塊
                st.markdown(f"""
                <div class="spot-card">
                    <span class="time-badge">⏱️ {spot.time}</span>   
                    <span class="spot-name">{spot.name}</span>
                    <p style="margin-top: 8px; color: #334155; line-height: 1.6;">{spot.description}</p>
                    <div class="info-sub-block">🚇 <strong>交通指引：</strong> {spot.transportation}</div>
                    <div class="info-sub-block">🎫 <strong>購票/預約攻略：</strong> {spot.booking_info}</div>
                    <div class="info-sub-block" style="border-left: 3px solid #10b981; background-color: #f0fdf4;">💳 <strong>預估現場消費：</strong> {spending_val}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 【高穩定修復】：完全放棄 HTML 串接，用原生帶底色的 st.info / st.markdown 渲染備案
                if getattr(spot, 'alternatives', []):
                    with st.container():
                        st.markdown("🍴 **此時段其他熱門餐廳/活動備案推薦：**")
                        for alt in spot.alternatives:
                            st.markdown(f" * **{alt.name}** —— {alt.desc}")
                        st.markdown("<p style='margin-bottom:15px;'></p>", unsafe_allow_html=True) # 留白
                
                # 主卡片的功能按鈕 (地圖與購票)
                has_ticket = getattr(spot, 'ticket_link_query', '').upper() != "FREE" and getattr(spot, 'ticket_link_query', '') != ""
                btn_cols = st.columns([6, 2, 2]) if has_ticket else st.columns([8, 2])
                
                if spot.map_keyword:
                    with btn_cols[-2 if has_ticket else -1]:
                        st.link_button(f"🔍 查「{spot.name}」位置", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot.map_keyword)}", use_container_width=True)
                if has_ticket:
                    with btn_cols[-1]:
                        st.link_button(f"🎫 線上購票 / 預約", f"https://www.google.com/search?q={urllib.parse.quote(spot.ticket_link_query)}", use_container_width=True)
            
            # --- 2. 渲染當晚的精選住宿推薦 ---
            hotel = day_data.recommended_hotel
            st.markdown(f"""
            <div class="hotel-card">
                <span class="hotel-badge">🏠 當晚精選住宿推薦</span>   
                <span class="spot-name" style="color: #0384c7; margin-left: 10px;">{hotel.name}</span>
                <p style="margin-top: 8px; color: #334155; line-height: 1.6;"><strong>推薦理由：</strong>{hotel.reason}</p>
                <div class="info-sub-block" style="border-left: 3px solid #0284c7;">💰 <strong>預估價位：</strong> {hotel.price_level}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 【高穩定修復】：住宿備案同樣改用原生安全 Markdown 渲染
            if getattr(day_data, 'alternative_hotels', []):
                with st.container():
                    st.markdown("🔄 **同區域其他精選住宿備案推薦：**")
                    for h_alt in day_data.alternative_hotels:
                        st.markdown(f" * **{h_alt.name}** —— {h_alt.desc}")
                    st.markdown("<p style='margin-bottom:15px;'></p>", unsafe_allow_html=True)
            
            # 查詢主推房價按鈕
            if hotel.search_keyword:
                with st.columns([8, 2])[1]:
                    st.link_button(f"🛎️ 查詢主推房價", f"https://www.google.com/search?q={urllib.parse.quote(hotel.search_keyword)}", use_container_width=True)

            # 當日貼心叮嚀與微調框
            st.markdown(f'<div class="tip-box">💡 <strong>當日導遊貼心叮嚀：</strong><br/>{day_data.local_tips}</div>', unsafe_allow_html=True)
            st.divider()
            
            # --- 3. 獨立天數的微調按鈕 ---
            st.markdown(f"🛠️ **覺得第 {day_counter} 天行程、餐廳或飯店需要更換？**")
            refine_input = st.text_input("請輸入修改想法：", placeholder="例如：『幫我把晚餐換成剛剛推薦的備案A』或『飯店改住低預算一點的備案B』...", key=f"refine_input_{day_counter}")
            if st.button("🎯 立即微調此天行程與住宿", key=f"refine_btn_{day_counter}"):
                if refine_input.strip() != "":
                    with st.spinner("正在為您重新調整行程..."):
                        st.session_state.itinerary_days[day_counter] = st.session_state.brain.refine_day_itinerary(current_day_data=day_data, refine_instruction=refine_input)
                        st.rerun()

    # ===========================================================================
    # 底部：完整行程下載區
    # ===========================================================================
    with st.container():
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.subheader("💾 行程導出與存檔備份")
        clean_prompt = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', user_prompt).split()
        st.download_button(
            label="📥 一鍵下載含有超連結備案的完整行程 (TXT)", 
            data=prepare_download_text(user_prompt, sorted_days), 
            file_name=f"{clean_prompt[0] if clean_prompt else '我的'}{len(sorted_days)}天_精緻旅遊行程.txt", 
            mime="text/plain", 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)