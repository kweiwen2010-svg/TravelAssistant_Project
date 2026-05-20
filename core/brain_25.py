import os
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

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
    name: str = Field(description="建議當晚入住的飯店名稱。若當天為最後一天且搭機回國，請直接寫'無（今日搭機返家）'")
    reason: str = Field(description="推薦入住這間飯店的原因。若不需住宿，請寫'今日已安排回國班機，夜宿機上或已抵達溫暖的家。'")
    price_level: str = Field(description="預估房價等級。若不需住宿，請填寫'NT$ 0 (不需住宿)'")
    search_keyword: str = Field(description="適合放入 Google 搜尋該飯店的關鍵字。若無住宿請寫 'FREE'")

class DayItinerary(BaseModel):
    day_number: int = Field(description="目前是第幾天的行程")
    day_title: str = Field(description="這一天的精簡主題摘要")
    spots: List[SpotDetail] = Field(description="這一天包含的所有行程、景點與餐廳清單")
    recommended_hotel: HotelDetail = Field(description="當晚主推的住宿/飯店明細")
    alternative_hotels: List[AltHotelDetail] = Field(default=[], description="固定提供1-2家同區域、不同價位風格的替代飯店備案物體")
    local_tips: str = Field(description="當天的交通銜接大方向建議或特別注意事項")

class TravelBrain:
    def __init__(self):
        self.model_name = "gemini-2.5-flash"

    def _get_client(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("找不到 GEMINI_API_KEY。請檢查 .env 檔案。")
        return genai.Client(api_key=api_key)

    def generate_day_itinerary(self, user_prompt: str, day_idx: int, total_days: int = 10, previous_context: str = "") -> DayItinerary:
        system_instruction = (
            "你是一位頂級的專業全球導遊與行程規劃師。\n"
            "【鐵律 1】你必須完全使用『繁體中文（台灣，zh-TW）』進行回覆。\n"
            "【鐵律 2】請務必為每一餐（餐廳）以及每晚住宿提供 1-2 個實用的備案選擇。\n"
            "【鐵律 3】貨幣單位一致性：全行程中所有涉及金額、消費狀況、現場預估費用（estimated_spending）的描述，\n"
            "         請統一使用『新台幣 (TWD)』或『當地貨幣並加註新台幣折算（例如：HKD 100，約折合台幣 410 元）』呈現。\n"
            "         絕對不允許第一天純寫港幣、第二天純寫台幣、第三天純寫美金。金額計價基準必須跨天數完全一致！\n"
            "【鐵律 4】回國邊界防禦律令（極度重要）：\n"
            "         當目前規劃的天數（day_idx）等於總天數（total_days）時，代表這是旅程的『最後一天』！\n"
            "         你必須在下午或傍晚強制安排『前往機場、辦理登機、免稅店購物、搭機返國』的返航行程。\n"
            "         最後一天的晚餐與住宿（recommended_hotel）不應再推薦當地飯店，請依據欄位說明強制填入『無（今日搭機返家）』，\n"
            "         且 alternative_hotels 備案陣列必須留空（[]）。不可讓旅客無止境地留在當地！\n"
            "【鐵律 5】交通數據標準化規範（極度重要）：\n"
            "         每個景點與餐廳的 transportation 欄位絕對不允許含糊其詞（例如只寫「搭地鐵」或「步行」）。\n"
            "         你必須嚴格遵守以下格式標準填寫細節，確保旅客能看到具體時間與路線：\n"
            "         1. 若是步行：必須包含預估時間（例如：『🚶 步行約 8 分鐘』）。\n"
            "         2. 若是地鐵/捷運：必須包含具體線路與預估時間（例如：『🚇 搭乘大眾地鐵 [大江戶線] 至新宿站，步行約 5 分鐘』）。\n"
            "         3. 若是公車/巴士：必須包含具體班次/路線與預估時間（例如：『🚌 搭乘京都市營巴士 [206路] 至清水寺道站，步行約 10 分鐘』）。\n"
            "【鐵律 6】時效落差防禦宣告（重要）：\n"
            "         你必須承認旅遊資料庫存在時間滯後性。凡是涉及歷史古蹟、國家博物館、知名地標（如：羅浮宮、萬神殿、晴空塔等），\n"
            "         只要涉及門票費用與預約規則，你必須在 booking_info 欄位中強制加上此警語：\n"
            "         『⚠️ 溫馨提醒：此熱門景點之票價與預約政策近年變動極為頻繁，強烈建議出發前點擊下方按鈕至官網或 Google 再次核對最新狀況，以現場公告為準。』\n"
            "【鐵律 7】老導遊人性化時間演算法（重要）：\n"
            "         1. 嚴格禁止行程過度緊湊。每日第一個行程出發時間請固定從 09:00 或 09:30 開始，留給旅客充足早餐與摸索時間。\n"
            "         2. 景點停留時間（time 欄位）必須合理化，凡是需要安檢、排隊的大型熱門景點，必須主動在停留時間內預留 30~45 分鐘的緩衝排隊與上洗手間時間。\n"
            "         3. 每日下午 15:00 ~ 17:00 之間，必須主動穿插一個『特色咖啡廳歇腳』或『自由漫步』的鬆弛時段，嚴防旅客體力崩潰。"
        )
        full_prompt = (
            f"使用者原始旅遊偏好：{user_prompt}\n"
            f"整個旅程總天數：{total_days} 天。\n"
            f"目前正在規劃【第 {day_idx} 天 / 共 {total_days} 天】。\n"
            f"【前情提要】：{previous_context if previous_context else '這是旅程的第一天。'}"
        )
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=DayItinerary,
        )
        
        max_retries = 3
        last_error_msg = ""
        
        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.models.generate_content(model=self.model_name, contents=full_prompt, config=config)
                return DayItinerary.model_validate_json(response.text)
            except Exception as e:
                last_error_msg = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                
        fallback_itinerary = DayItinerary(
            day_number=day_idx,
            day_title="【系統提示】今日行程數據讀取稍有延遲",
            spots=[
                SpotDetail(
                    time="說明",
                    name="連線或解析暫時受阻",
                    description=f"很抱歉，本地在向雲端大腦規劃第 {day_idx} 天行程時遭遇異常波動（錯誤代碼: {last_error_msg[:60]}）。這不影響整體系統！請不要緊張，直接拉到本天行程的最下方，點擊『🎯 立即微調此天行程與住宿』按鈕，即可單獨為這一天的行程進行手動無縫修復與重新生成。",
                    transportation="無",
                    booking_info="無",
                    estimated_spending="NT$ 0 (請點擊下方微調重新取得)",
                    map_keyword="",
                    ticket_link_query="FREE",
                    alternatives=[]
                )
            ],
            recommended_hotel=HotelDetail(
                name="請點擊下方微調按鈕重新取得飯店",
                reason="由於大腦遭遇短暫波動，請點擊下方微調按鈕單獨重新抓取此天資料。",
                price_level="NT$ 0",
                search_keyword="FREE"
            ),
            alternative_hotels=[],
            local_tips="提示：您可以直接點擊下方微調按鈕，輸入『重新產生這天行程』來修正本頁面。"
        )
        return fallback_itinerary

    def refine_day_itinerary(self, current_day_data: DayItinerary, refine_instruction: str) -> DayItinerary:
        system_instruction = (
            "你是一位行動力極強、善解人意的旅遊行程修正專家。\n"
            "【鐵律 1】你必須完全使用『繁體中文（台灣，zh-TW）』進行回覆。\n"
            "【鐵律 2】修改費用時，請同樣遵守統一使用『新台幣 (TWD)』或加註台幣說明的原則。\n"
            "【鐵律 3】鋼鐵覆寫特令（極度重要）：\n"
            "         你必須嚴格、無條件地服從使用者的『微調指令 (refine_instruction)』！\n"
            "         如果使用者要求更換晚餐、更換某個景點、或指定入住某家備案飯店，你『必須』直接修改並替換掉\n"
            "         原本 spots 清單或 recommended_hotel 中的內容。絕對不允許原封不動地傳回舊行程！\n"
            "         如果原本的行程是保底提示或受阻數據，請直接忽略原本的提示，重新根據微調指令為使用者生出一份完美的當日行程。\n"
            "         請展現你的修正誠意，將使用者想要的變更完美落實到輸出的 JSON 結構中。"
        )
        full_prompt = (
            f"原行程內容（JSON）：\n{current_day_data.model_dump_json(indent=2)}\n"
            f"使用者微調指令：\n{refine_instruction}\n"
        )
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
            response_mime_type="application/json",
            response_schema=DayItinerary,
        )
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client = self._get_client()
                response = client.models.generate_content(model=self.model_name, contents=full_prompt, config=config)
                return DayItinerary.model_validate_json(response.text)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise e