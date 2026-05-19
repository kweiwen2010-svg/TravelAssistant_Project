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
    .welcome-box { background-color: #f0fdf4; padding: 22px; border-radius: 10px; border: 1px solid #bbf7d0; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .day-header { background: linear-gradient(90deg, #1e293b 0%, #334155 100%); color: white; padding: 12px 20px; border-radius: 6px; font-size: 1.25rem; font-weight: bold; margin-top: 35px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
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

st.title("✈️ 全球智慧旅遊助手 2.5 (安全氣囊防禦 V3.1)")
st.caption("基於 Gemini 2.5 Flash 大腦 • 已整合 API 自動降級保底防禦網")

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
            if getattr(sp, 'alternatives', []):
                alt_strs = [f"{a.name}({a.desc})" for a in sp.alternatives]
                download_text += f"🔄 備案選擇：{', '.join(alt_strs)}\n"
            download_text += f"🚇 交通指引：{sp.transportation}\n"
            download_text += f"🎫 購票攻略：{sp.booking_info}\n"
            download_text += f"💳 預估費用：{sp.estimated_spending}\n\n"
        download_text += f"🏠 當晚住宿：{d_obj.recommended_hotel.name}\n"
        download_text += f"📝 推薦理由：{d_obj.recommended_hotel.reason}\n"
        download_text += f"💰 房價等級：{d_obj.recommended_hotel.price_level}\n"
        if getattr(d_obj, 'alternative_hotels', []):
            alt_h_strs = [f"{h.name}({h.desc})" for h in d_obj.alternative_hotels]
            download_text += f"🔄 住宿備案：{', '.join(alt_h_strs)}\n"
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

if not st.session_state.itinerary_days and not st.session_state.is_generating:
    st.markdown("""
    <div class="welcome-box">
        <h4 style="margin-top:0; color: #166534;">💡 歡迎使用全球智慧旅遊助手！開始您的第一步：</h4>
        <p style="font-size: 0.98rem; color: #1e293b;">本系統已整合 V3.1 鋼鐵防禦網，即使發生 API 波動，天數生成也絕對不會中斷崩潰：</p>
        <ol style="font-size: 0.95rem; color: #374151; line-height: 1.7;">
            <li>請看向網頁的 <b>⬅️ 左側邊欄（📋 旅遊意向設定與備份還原）</b>。</li>
            <li>在輸入框中，自由修改或寫下您的旅遊想法，點擊 <b>「🚀 開始全自動分段生成」</b>。</li>
            <li><b>【防禦說明】</b>：若生成過程中某天因網路問題出現保底提示，直接點擊該天最下方的微調按鈕即可單獨修正！</li>
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
                    st.error("❌ 錯誤：上傳的 ZIP 檔中找不到標準的行程備份數據，請確認是否為本系統導出的檔案。")
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
    
    user_prompt = st.text_area("輸入您的旅遊靈感與偏好：", value=st.session_state.user_prompt_val, height=150, disabled=st.session_state.is_generating)
    total_days = st.number_input("規劃天數", min_value=1, max_value=15, value=st.session_state.total_days_val, disabled=st.session_state.is_generating)
    
    generate_btn = st.button("🚀 開始全自動分段生成", type="primary", use_container_width=True, disabled=st.session_state.is_generating)
    
    if st.button("🧹 清除目前行程方案 (一鍵重設安全網)", use_container_width=True, disabled=st.session_state.is_generating):
        st.session_state.itinerary_days = {}
        st.session_state.user_prompt_val = "我想去土耳其10天 老婆同遊 美食 人文 風景 行程不要太趕"
        st.session_state.total_days_val = 10
        st.session_state.uploader_version += 1
        st.success("系統與檔案上傳快取已成功全面清除重設！")
        st.rerun()

if generate_btn:
    st.session_state.is_generating = True
    st.session_state.itinerary_days = {}  
    st.session_state.user_prompt_val = user_prompt
    st.session_state.total_days_val = total_days
    st.rerun()

if st.session_state.is_generating and not st.session_state.itinerary_days:
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    previous_summary_context = ""
    
    for current_day in range(1, st.session_state.total_days_val + 1):
        status_text.markdown(f"⏳ **正在利用大腦深度規劃：第 {current_day} 天...** (安全氣囊防禦機制運作中)")
        # 🛡️ 內部即使遭遇異常，大腦也會回傳 Fallback 結構，此處不中斷、不 raise
        day_data: DayItinerary = st.session_state.brain.generate_day_itinerary(
            user_prompt=st.session_state.user_prompt_val, 
            day_idx=current_day, 
            total_days=st.session_state.total_days_val, 
            previous_context=previous_summary_context
        )
        st.session_state.itinerary_days[current_day] = day_data
        previous_summary_context += f"第 {current_day} 天主題: {day_data.day_title}，住宿: {day_data.recommended_hotel.name}。\n"
        progress_bar.progress(current_day / st.session_state.total_days_val)
            
    progress_bar.empty()
    status_text.empty()
    st.session_state.is_generating = False  
    st.rerun() 

if st.session_state.itinerary_days:
    st.subheader("🗺️ 您專屬的客製化行程明細")
    sorted_days = sorted(st.session_state.itinerary_days.keys())
    
    for day_counter in sorted_days:
        day_data: DayItinerary = st.session_state.itinerary_days[day_counter]
        
        # 🛡️ 動態判斷標題，若為保底資料則呈現警告橘色風格調性
        is_fallback = "【系統提示】" in day_data.day_title
        if is_fallback:
            st.markdown(f'<div class="day-header" style="background: linear-gradient(90deg, #c2410c 0%, #ea580c 100%);">⚠️ DETAILED PLAN · 第 {day_counter} 天 (點擊下方重新生成)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="day-header">📅 DETAILED PLAN · 第 {day_counter} 天</div>', unsafe_allow_html=True)
        
        with st.expander(f"📌 點擊展開/收合今日概覽：{day_data.day_title}", expanded=True):
            
            for spot in day_data.spots:
                spending_val = spot.estimated_spending if getattr(spot, 'estimated_spending', None) else "現場評估"
                card_border = "#f59e0b" if is_fallback else "#ff4b4b"
                
                st.markdown(f"""
                <div class="spot-card" style="border-left: 5px solid {card_border};">
                    <span class="time-badge" style="color: {card_border};">⏱️ {spot.time}</span>   
                    <span class="spot-name">{spot.name}</span>
                    <p style="margin-top: 8px; color: #334155; line-height: 1.6;">{spot.description}</p>
                    <div class="info-sub-block">🚇 <strong>交通指引：</strong> {spot.transportation}</div>
                    <div class="info-sub-block">🎫 <strong>購票/預約攻略：</strong> {spot.booking_info}</div>
                    <div class="info-sub-block" style="border-left: 3px solid #10b981; background-color: #f0fdf4;">💳 <strong>預估現場消費：</strong> {spending_val}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if getattr(spot, 'alternatives', []):
                    with st.container():
                        st.markdown("🍴 **此時段其他熱門餐廳/活動備案推薦：**")
                        for alt in spot.alternatives:
                            st.markdown(f" * **{alt.name}** —— {alt.desc}")
                        st.markdown("<p style='margin-bottom:15px;'></p>", unsafe_allow_html=True)
                
                has_ticket = getattr(spot, 'ticket_link_query', '').upper() != "FREE" and getattr(spot, 'ticket_link_query', '') != "" and spot.ticket_link_query != "無"
                btn_cols = st.columns([6, 2, 2]) if has_ticket else st.columns([8, 2])
                
                if spot.map_keyword:
                    with btn_cols[-2 if has_ticket else -1]:
                        st.link_button(f"🔍 查「{spot.name}」位置", f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(spot.map_keyword)}", use_container_width=True)
                if has_ticket:
                    with btn_cols[-1]:
                        st.link_button(f"🎫 線上購票 / 預約", f"https://www.google.com/search?q={urllib.parse.quote(spot.ticket_link_query)}", use_container_width=True)
            
            hotel = day_data.recommended_hotel
            st.markdown(f"""
            <div class="hotel-card">
                <span class="hotel-badge">🏠 當晚精選住宿推薦</span>   
                <span class="spot-name" style="color: #0384c7; margin-left: 10px;">{hotel.name}</span>
                <p style="margin-top: 8px; color: #334155; line-height: 1.6;"><strong>推薦理由：</strong>{hotel.reason}</p>
                <div class="info-sub-block" style="border-left: 3px solid #0284c7;">💰 <strong>預估價位：</strong> {hotel.price_level}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if getattr(day_data, 'alternative_hotels', []):
                with st.container():
                    st.markdown("🔄 **同區域其他精選住宿備案推薦：**")
                    for h_alt in day_data.alternative_hotels:
                        st.markdown(f" * **{h_alt.name}** —— {h_alt.desc}")
                    st.markdown("<p style='margin-bottom:15px;'></p>", unsafe_allow_html=True)
            
            if hotel.search_keyword and hotel.search_keyword.upper() != "FREE":
                with st.columns([8, 2])[1]:
                    st.link_button(f"🛎️ 查詢主推房價", f"https://www.google.com/search?q={urllib.parse.quote(hotel.search_keyword)}", use_container_width=True)

            st.markdown(f'<div class="tip-box">💡 <strong>當日導遊貼心叮嚀：</strong><br/>{day_data.local_tips}</div>', unsafe_allow_html=True)
            st.divider()
            
            st.markdown(f"🛠️ **覺得第 {day_counter} 天行程需要更換（或處於系統保底提示狀態需要重新產生）？**")
            placeholder_text = "例如：『請幫我重新完整產生這一天的行程』或『晚餐換成牛排』..." if is_fallback else "例如：『幫我把晚餐換成剛剛推薦的備案A』..."
            refine_input = st.text_input("請輸入修改或重新生成想法：", placeholder=placeholder_text, key=f"refine_input_{day_counter}")
            
            if st.button("🎯 立即微調此天行程與住宿", key=f"refine_btn_{day_counter}", type="primary" if is_fallback else "secondary"):
                if refine_input.strip() != "":
                    with st.spinner("正在為您調校大腦數據，請稍候..."):
                        st.session_state.itinerary_days[day_counter] = st.session_state.brain.refine_day_itinerary(current_day_data=day_data, refine_instruction=refine_input)
                        st.rerun()

    with st.container():
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.subheader("💾 行程導出與時光機存檔備份 (.ZIP)")
        st.markdown("<p style='font-size:0.92rem; color:#475569;'>下載的 .zip 壓縮包內含：(1) 手機開啟絕不亂碼的精美行程明細 .txt 檔 (2) 給系統專用的高穩定度還原 .json 檔。未來直接將此 .zip 檔拖入左側即可恢復現場。</p>", unsafe_allow_html=True)
        
        clean_prompt = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', st.session_state.user_prompt_val).split()
        file_base_name = f"{clean_prompt[0] if clean_prompt else '我的'}{len(sorted_days)}天_精緻旅遊行程"
        
        zip_data = create_zip_backup(st.session_state.user_prompt_val, sorted_days)
        
        st.download_button(
            label="📥 一鍵打包下載時光機備份包 (.ZIP)", 
            data=zip_data, 
            file_name=f"{file_base_name}.zip", 
            mime="application/zip", 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)