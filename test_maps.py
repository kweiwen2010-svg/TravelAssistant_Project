from core.mapper import DataMapper
from config import Config

def test_connection():
    try:
        # 1. 檢查金鑰配置
        Config.validate()
        
        # 2. 初始化地圖模組
        mapper = DataMapper()
        
        # 3. 測試搜尋：找看看東京的熱門景點
        print("\n🔍 正在測試 Google Maps API (搜尋東京景點)...")
        results = mapper.search_attractions("東京", "必去景點")
        
        if results:
            print(f"✅ 成功抓取到 {len(results)} 個景點：")
            for idx, p in enumerate(results, 1):
                print(f"{idx}. {p['名稱']} (評分: {p['評分']})")
                print(f"   地址: {p['地址']}")
        else:
            print("⚠️ 沒抓到資料，請確認 Places API 是否已啟用。")

    except Exception as e:
        print(f"❌ 測試失敗！錯誤訊息: {e}")

if __name__ == "__main__":
    test_connection()