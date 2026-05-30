# =========================================
# 檔名：core/brain_25.py (基準版 3.0 Pydantic 大腦邏輯)
# =========================================
import os
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class AltSpotDetail(BaseModel):
    name: str = Field(description="替代餐廳或活動的繁體中文名稱，禁止包含 HTML 標籤")
    desc: str = Field(description="一句話特色與推薦簡述，禁止包含 HTML 標籤")

class AltHotelDetail(BaseModel):
    name: str = Field(description="替代飯店或住宿的繁體中文名稱，禁止包含 HTML 標籤")
    desc: str = Field(description="一句話推薦理由與預估價位，禁止包含 HTML 標籤")

class SpotDetail(BaseModel):
    time: str = Field(description="建議停留時間或時段，例如 '09:00 - 11:00'")
    name: str = Field(description="景點或餐廳的繁體中文名稱")
    description: str = Field(description="該點的特色介紹（嚴格繁體中文，生動人性化，嚴格禁止任何 HTML 標籤）")
    transportation: str = Field(description="前往該地點的交通方式，必須包含預估時間與具體線路/班次")
    booking_info: str = Field(description="該景點的門票、費用、訂位 or 購票攻略")
    estimated_spending: int = Field(description="預估現場現場門票或個人純餐費，必須是純整數，單位為新台幣(TWD)，免門票或不花錢請填 0")
    estimated_transport_cost: int = Field(description="前往該地點預估需要花費的交通車資（如地鐵票、火車票、計程車費），必須是純整數，單位為新台幣(TWD)，步行或不花錢請填 0")
    map_keyword: str = Field(description="Google Maps 搜尋關鍵字")
    ticket_link_query: str = Field(description="官網購票連結英文關鍵字（若不需門票則填寫 FREE）")
    alternatives: List[AltSpotDetail] = Field(default=[], description="備案選擇")

class HotelDetail(BaseModel):
    name: str = Field(description="建議入住飯店名稱，若該晚不需住宿，請填寫 '無（此夜在機上過夜）'")
    description: str = Field(description="推薦該飯店的理由、周邊機能與特色描述")
    booking_info: str = Field(description="訂房管道建議與房型提醒")
    estimated_spending: int = Field(description="預估該晚每房住宿花費，必須是純整數，單位為新台幣(TWD)，若不需住宿請填 0")
    map_keyword: str = Field(description="Google Maps 搜尋關鍵字")
    alternatives: List[AltHotelDetail] = Field(default=[], description="備案住宿")

class DayItinerary(BaseModel):
    day_number: int = Field(description="旅遊天數索引")
    day_title: str = Field(description="行程主題標題")
    estimated_flight_cost: int = Field(description="預估從出發地到目的地的來回國際機票總花費（僅限個人來回經濟艙刚性基礎估計）。請大腦根據起飛地、飛行時間合理盲猜。如果不是第 1 天，請一律填 0")
    spots: List[SpotDetail] = Field(description="當日景點清單")
    hotel: HotelDetail = Field(description="當晚入住飯店")

class TravelBrain:
    def __init__(self):
        self.client = genai.Client()
        self.model_name = "gemini-2.5-pro"

    def generate_day_itinerary(self, user_prompt: str, total_days: int, current_day: int, previous_days_context: str, start_country: str, departure_time: str, flight_hours: float, timezone_diff: float) -> DayItinerary:
        system_instruction = (
            "別名：老導遊物理時區引擎\n"
            "你是一位擁有30年帶團經驗的頂級全球資深星級老導遊。你現在要為使用者打造極致貼心、充滿鬆弛感且具備穿透成本視野的旅遊行程。\n"
            "你必須嚴格遵守以下物理與邏輯鐵律，絕對禁止違反：\n\n"
            "【鐵律 1】語言與貨幣：完全使用『繁體中文（台灣）』。費用統一以『新台幣 (TWD)』計價，且必須為純整數數字。\n"
            "【鐵律 2】機票估算防禦：你必須在 Day 1 根據出發地與目的地距離，估算一個合理的來回國際機票新台幣整數價格，填入 estimated_flight_cost。第 2 天之後的行程該欄位一律嚴格填寫 0。\n"
            "【鐵律 3】時區物理引擎核心公式：\n"
            "  落地時間 = 起飛時間 + 飛行總時間 + 時差變更（目的地時差）。\n"
            "  * 狀況 A：若經公式推算，第 1 天出發後，落地時間已是「隔天清晨或上午」。\n"
            "    - 第 1 天整天均在飛機上。此時【第 1 天的 hotel 欄位中的 name 必須嚴格填寫：'無（此夜在機上過夜）'，且 estimated_spending 填 0】！\n"
            "  * 狀況 B：若經公式推算，落地時間為「當天下午或傍晚/夜間」。\n"
            "    - 旅客在第 1 天晚上就需要床位。此時【第 1 天的 hotel 欄位必須精準指名當晚入住飯店與估算房價】！\n"
            "【鐵律 4】費用精細拆分：餐飲與門票花費填入 estimated_spending；而該景點移動產生的交通車資（地鐵、火車票）請務必獨立計算並填入 estimated_transport_cost，嚴禁混為一談！"
        )

        full_prompt = (
            "🛫 出發地：{0}\n⏰ 第 1 天起飛時間點：{1}\n⏱️ 預估飛行總時間：{2} 小時\n🌐 目的地時差：{3} 小時\n🎯 目的地與偏好：{4}\n📅 規劃總天數：{5} 天\n📌 當前正在生成：第 {6} 天的行程\n🧱 前情提要資訊：\n{7}"
        ).format(start_country, departure_time, flight_hours, timezone_diff, user_prompt, total_days, current_day, previous_days_context)

        for attempt in range(3):
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                    response_mime_type="application/json",
                    response_schema=DayItinerary,
                )
                response = self.client.models.generate_content(model=self.model_name, contents=full_prompt, config=config)
                return DayItinerary.model_validate_json(response.text)
            except Exception as e:
                if attempt == 2: return self.get_fallback_itinerary(current_day, str(e))
                time.sleep(1)

    def refine_day_itinerary(self, user_prompt: str, current_day_data: DayItinerary, refine_instruction: str) -> DayItinerary:
        system_instruction = "你是一位資深老導遊，負責局部微調行程。請保持繁體中文與台幣計價（金額為純整數），並產出新的 JSON 結構。"
        full_prompt = "🎯 原始設定：{0}\n📋 原行程：{1}\n🛠️ 微調指令：{2}".format(user_prompt, current_day_data.model_dump_json(), refine_instruction)
        try:
            config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2, response_mime_type="application/json", response_schema=DayItinerary)
            response = self.client.models.generate_content(model=self.model_name, contents=full_prompt, config=config)
            return DayItinerary.model_validate_json(response.text)
        except Exception: return current_day_data

    def get_fallback_itinerary(self, day_num: int, reason: str) -> DayItinerary:
        return DayItinerary(
            day_number=day_num,
            day_title="第 {0} 天 行程數據待微調".format(day_num),
            estimated_flight_cost=0,
            spots=[SpotDetail(time="09:00", name="系統定錨提示", description="API波動：{0}。請微調重試。".format(reason), transportation="🚶 步行", booking_info="無", estimated_spending=0, estimated_transport_cost=0, map_keyword="Rome", ticket_link_query="FREE", alternatives=[])],
            hotel=HotelDetail(name="待選定飯店", description="等待微調指令", booking_info="無", estimated_spending=0, map_keyword="Hotel", alternatives=[])
        )