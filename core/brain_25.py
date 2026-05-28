import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class SpotDetail(BaseModel):
    time: str = Field(description="建議造訪的時間點，例如 '09:00 - 11:30'")
    name: str = Field(description="景點或餐廳的繁體中文名稱")
    map_keyword: str = Field(description="最精準的 Google 地圖搜尋關鍵字，需包含城市名，如 'Louvre Museum, Paris'")
    description: str = Field(description="深度景點人文歷史背景、旅遊攻略、必吃特色菜、必買清單與防坑指南")
    transportation: str = Field(description="從上一個點移動到此點的推薦交通方式與預估轉乘時間，如 '搭乘地鐵M1線至Palais Royal站 (約15分鐘)'")
    estimated_transport_cost: int = Field(description="這趟移動的單人當地交通車資預估（台幣），如地鐵票價。若步行則填 0")
    booking_info: str = Field(description="詳細訂位或購票攻略，如 '建議提前30天在官網預約門票，現場無售現票'")
    ticket_link_query: str = Field(description="搜尋該景點購票或訂位網站的精準關鍵字。若免費景點或無須購票則強制填寫 'FREE'")
    estimated_spending: int = Field(description="單人在該景點的預估純花費（門票、餐飲、體驗費，不含交通與購物，折合台幣價格）")

class HotelDetail(BaseModel):
    name: str = Field(description="建議下榻飯店或住宿名稱")
    map_keyword: str = Field(description="飯店的 Google 地圖精準搜尋關鍵字")
    description: str = Field(description="選擇這家住宿的理由、安全區域考量、周邊便利性（如鄰近哪座車站）")
    booking_info: str = Field(description="訂房管道建議，如 '透過 Booking.com 或 Agoda 預訂'")
    estimated_spending: int = Field(description="單人每晚預估住宿花費（折合台幣價格）")

class DayItinerary(BaseModel):
    day_number: int = Field(description="當前天數序號")
    day_title: str = Field(description="這一天行程的主題核心摘要，例如 '巴黎古典藝術啟航：盧浮宮與塞納河畔'")
    spots: List[SpotDetail] = Field(description="當天按時間順序排列的景點與餐飲明細列表")
    hotel: HotelDetail = Field(description="當晚建議下榻的住宿資訊")

class TravelBrain:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = "gemini-2.5-pro"
        
    def generate_day_itinerary(self, user_prompt: str, total_days: int, current_day: int, context_str: str, start_country: str, departure_time: str, flight_hours: float, timezone_diff: float) -> DayItinerary:
        system_instruction = f"""你是一位擁有20年自由行規劃經驗的殿堂級老導遊。
請嚴格根據使用者的出發參數、旅遊意向（可能包含旅行社團體行程文字範本）、以及前幾天已生成的行程上下文，來編排精準的第 {current_day} 天行程。

【出發與時區參數說明（Day 1 計算基準）】
- 出發地地標：{start_country}
- 第 1 天起飛時間點：{departure_time}
- 飛行總時間（小時）：{flight_hours}
- 目的地時差：{timezone_diff} 小時

【大局編排核心原則】
1. 請維持四大維度剛性預算精算架構：國際機票費用已被側邊欄手動接管，請你在 Spots 欄位中『集中算準』：
   - 景點內部的『estimated_spending』（純餐飲門票費）
   - 移動時的『estimated_transport_cost』（當地交通車資，如火車、地鐵票，若是步行或遊覽車填0）
   - 住宿的『estimated_spending』（單人每晚住宿費）
2. 全程一律轉換為【新台幣 NT$】進行估算。
3. 行程不可跳躍，交通銜接必須合乎邏輯。特別注意當輸入包含旅行社範本時，請幫忙進行去泡沫化的深度拆解，確保順序與地理銜接正確。
"""
        prompt = f"""使用者旅遊意向或旅行社參考範本：{user_prompt}
總天數：{total_days} 天
當前要生成的目標天數：第 {current_day} 天

【前幾天已排定行程大綱參考（請務必嚴格連貫銜接）】：
{context_str}

請為我生成符合期待並完美承接前一天動線的第 {current_day} 天深度結構化行程。"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=DayItinerary,
                temperature=0.3
            )
        )
        return DayItinerary.model_validate_json(response.text)