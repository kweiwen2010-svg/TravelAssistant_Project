import requests
from config import Config

class DataMapper:
    def __init__(self):
        self.api_key = Config.MAPS_KEY

    def search_attractions(self, destination, keyword="景點"):
        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        # 建立城市座標預設，強化鎖定義大利
        city_coords = {
            "羅馬": "41.9028,12.4964",
            "佛羅倫斯": "43.7696,11.2558",
            "威尼斯": "45.4408,12.3155",
            "義大利": "41.8719,12.5674"
        }
        
        bias_location = None
        for city, coord in city_coords.items():
            if city in destination:
                bias_location = coord
                break

        params = {
            "query": f"Italy {destination} {keyword}",
            "key": self.api_key,
            "language": "zh-TW",
            "region": "it" if "義大利" in destination else None
        }

        if bias_location:
            params["location"] = bias_location
            params["radius"] = 10000 

        response = requests.get(endpoint, params=params).json()
        results = response.get("results", [])

        extracted_data = []
        for place in results[:10]:
            loc = place["geometry"]["location"]
            # 物理過濾：捨棄包含「台灣」字樣的錯誤結果
            if "台灣" not in place.get("formatted_address", ""):
                extracted_data.append({
                    "名稱": place.get("name"),
                    "評分": place.get("rating", "無"),
                    "地址": place.get("formatted_address"),
                    "lat": loc["lat"],
                    "lng": loc["lng"],
                    "place_id": place.get("place_id")
                })
        
        return extracted_data