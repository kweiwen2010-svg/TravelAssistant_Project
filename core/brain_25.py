import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class SpotDetail(BaseModel):
    time: str = Field(description="建議造訪的時間點，例如 '09:00 - 11:30'")
    name: str = Field(description="景點或餐廳的繁體中文名稱")
    map_keyword: str = Field(description="最精準的 Google 地圖搜尋關鍵字，需包含城市名，如 'Louvre Museum, Paris'")
    description: str = Field(description="深度景點人文歷史背景、旅遊攻略、必吃特色菜（拒絕重複）、必買清單與防坑指南")
    transportation: str = Field(description="從上一個點移動到此點的推薦交通方式與預估轉乘時間，如 '搭乘地鐵M1線至Palais Royal站 (約15分鐘)'")
    estimated_transport_cost: int = Field(description="這趟移動的單人當地交通車資預估（台幣）。注意：凡是登山火車、高山纜車、少女峰/策馬特車票、景觀列車、遊船，其票價『禁止』寫入門票花費，必須強制獨立算在此欄位！若單純步行或已包含在全包遊覽車中則填 0")
    booking_info: str = Field(description="詳細訂位或購票攻略，如 '建議提前30天在官網預約門票，現場無售現票'")
    ticket_link_query: str = Field(description="搜尋該景點購票或訂位網站的精準關鍵字。若免費景點或無須購票則強制填寫 'FREE'")
    estimated_spending: int = Field(description="單人在該景點的預估純花費（門票、餐飲、體驗費。注意：不含任何交通車資、高山纜車費與購物，折合台幣價格）")

class HotelDetail(BaseModel):
    name: str = Field(description="建議下榻飯店或住宿名稱")
    map_keyword: str = Field(description="飯店的 Google 地圖精準搜尋關鍵字")
    description: str = Field(description="選擇這家住宿的理由、安全區域考量、周邊便利性（如鄰近哪座車站，拉行李是否方便）")
    booking_info: str = Field(description="訂房管道建議，如 '透過 Booking.com 或 Agoda 預訂'")
    estimated_spending: int = Field(description="單人每晚預估住宿花費（折合台幣價格，需貼近五星或四星實時行情，勿過度樂觀）")

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
        system_instruction = f"""你是一位擁有20年自由行規劃經驗的殿堂級老導遊，對旅遊細節與行程流暢度有極致的龜毛要求。
請嚴格根據使用者的出發參數、旅遊意向、以及前幾天已生成的行程上下文，來編排精準的第 {current_day} 天行程。

【出發與時區參數說明（Day 1 計算基準）】
- 出發地地標：{start_country}
- 第 1 天起飛時間點：{departure_time}
- 飛行總時間（小時）：{flight_hours}
- 目的地時差：{timezone_diff} 小時

【大局編排與反饋優化鐵律】
1. 【反重複餐廳機制】：審視前幾天已排定行程大綱。嚴禁在整個行程中重複安排相同的餐廳或景點（例如：前幾天吃過軍火庫餐廳 Zeughauskeller，今天就必須強制換成義式料理、河畔輕食或特色起司鍋）。每一天的美食與體驗都要有新鮮感與多樣性！
2. 【高海拔拉車減壓防線】：如果當天有跨城市長途拉車（移動時間大於 3 小時，例如日內瓦到策馬特）且目的地為高海拔山城，抵達當天的下午行程（spots）禁止超過 1 個，必須留白給旅客 check-in、吃飯、適應高海拔與無車小鎮漫步，維持鬆弛感。
3. 【四大維度剛性預算精算】：全程一律轉換為【新台幣 NT$】進行估算。
   - 國際機票已被前端接管。
   - 請嚴格在每個 Spot 的 `estimated_transport_cost` 算準該段移動的車資（特別是瑞士高昂的少女峰登山火車、Gornergrat 登山火車、纜車、景觀列車票價）。
   - 景點內部的 `estimated_spending` 僅限純餐飲與單純景點門票。
"""
        prompt = f"""使用者旅遊意向：{user_prompt}
總天數：{total_days} 天
當前要生成的目標天數：第 {current_day} 天

【前幾天已排定行程大綱參考（請仔細檢查，絕對不要推薦重複的餐廳！）】：
{context_str}

請為我生成符合期待的第 {current_day} 天深度結構化行程。"""

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