import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ===========================================================================
# 1. 結構化資料定義 (回歸純文字穩定備案)
# ===========================================================================

class AltSpotDetail(BaseModel):
    name: str = Field(description="替代餐廳或活動的繁體中文名稱")
    desc: str = Field(description="一句話特色與推薦簡述（例如：'在地人狂推的平價鳥貴族串燒'）")

class AltHotelDetail(BaseModel):
    name: str = Field(description="替代飯店或住宿的繁體中文名稱")
    desc: str = Field(description="一句話推薦理由與預估價位（例如：'新宿平價連鎖首選，CP值極高'）")

class SpotDetail(BaseModel):
    time: str = Field(description="建議停留時間或時段，例如 '09:00 - 11:00' 或 '上午'")
    name: str = Field(description="景點或餐廳的繁體中文名稱")
    description: str = Field(description="該點的特色介紹、推薦玩法或必吃推薦（嚴格繁體中文）")
    transportation: str = Field(description="前往該地點的交通方式")
    booking_info: str = Field(description="該景點的門票、費用、訂位或購票攻略")
    estimated_spending: str = Field(description="該景點或餐廳的預估現場基本消費狀況")
    map_keyword: str = Field(description="最適合放入 Google Maps 搜尋的關鍵字")
    ticket_link_query: str = Field(description="適合放入 Google 搜尋門票的關鍵字。免門票或純餐廳請寫 'FREE'")
    alternatives: List[AltSpotDetail] = Field(default=[], description="如果是餐廳，請固定提供1-2個附近的替代餐廳/美食備案物體；如果是純景點可留空陣列")

class HotelDetail(BaseModel):
    name: str = Field(description="建議當晚入住的飯店名稱")
    reason: str = Field(description="推薦入住這間飯店的原因")
    price_level: str = Field(description="預估房價等級")
    search_keyword: str = Field(description="適合放入 Google 搜尋該飯店的關鍵字")

class DayItinerary(BaseModel):
    day_number: int = Field(description="目前是第幾天的行程")
    day_title: str = Field(description="這一天的精簡主題摘要")
    spots: List[SpotDetail] = Field(description="這一天包含的所有行程、景點與餐廳清單")
    recommended_hotel: HotelDetail = Field(description="當晚主推的住宿/飯店明細")
    alternative_hotels: List[AltHotelDetail] = Field(default=[], description="固定提供1-2家同區域、不同價位風格的替代飯店備案物體")
    local_tips: str = Field(description="當天的交通銜接大方向建議或特別注意事項")


# ===========================================================================
# 2. 大腦核心類別 (Gemini 2.5 Flash 驅動)
# ===========================================================================

class TravelBrain:
    def __init__(self):
        self.model_name = "gemini-2.5-flash"

    def _get_client(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("找不到 GEMINI_API_KEY。請檢查 .env 檔案。")
        return genai.Client(api_key=api_key)

    def generate_day_itinerary(self, user_prompt: str, day_idx: int, previous_context: str = "") -> DayItinerary:
        system_instruction = (
            "你是一位頂級的專業全球導遊與行程規劃師。\n"
            "【鐵律】你必須完全使用『繁體中文（台灣，zh-TW）』進行回覆。\n"
            "請務必為每一餐（餐廳）以及每晚住宿提供 1-2 個實用的備案選擇。"
        )
        full_prompt = (
            f"使用者原始旅遊偏好：{user_prompt}\n"
            f"目前正在規劃【第 {day_idx} 天】。\n"
            f"【前情提要】：{previous_context if previous_context else '這是旅程的第一天。'}"
        )
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=DayItinerary,
        )
        client = self._get_client()
        response = client.models.generate_content(model=self.model_name, contents=full_prompt, config=config)
        return DayItinerary.model_validate_json(response.text)

    def refine_day_itinerary(self, current_day_data: DayItinerary, refine_instruction: str) -> DayItinerary:
        system_instruction = "你是一位善解人意的旅遊行程修正專家。【鐵律】你必須完全使用『繁體中文（台灣，zh-TW）』進行回覆。"
        full_prompt = (
            f"原行程內容（JSON）：\n{current_day_data.model_dump_json(indent=2)}\n"
            f"使用者微調指令：\n{refine_instruction}\n"
        )
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.5,
            response_mime_type="application/json",
            response_schema=DayItinerary,
        )
        client = self._get_client()
        response = client.models.generate_content(model=self.model_name, contents=full_prompt, config=config)
        return DayItinerary.model_validate_json(response.text)