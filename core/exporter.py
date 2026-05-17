import datetime

class TravelExporter:
    @staticmethod
    def to_txt(itinerary_data):
        if not itinerary_data:
            return "尚無行程資料"
        
        sections = itinerary_data.split("---DAY_SEPARATOR---")
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        header = [
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
            "   🌍 您的專屬旅遊規劃書 (行動版)",
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
            f"產出時間: {now}",
            "━" * 25 + "\n"
        ]
        
        body = []
        for idx, content in enumerate(sections):
            if idx == 0:
                title = "【💰 費用預算與氣候建議】"
            elif idx == 1:
                title = "【🌟 在地深度探索推薦】"
            else:
                title = f"【📌 第 {idx-1} 天詳細行程】"
            
            body.append(f"{title}\n{TravelExporter._format_for_mobile(content)}\n")
            body.append("-" * 30 + "\n")
            
        return "\n".join(header + body)

    @staticmethod
    def _format_for_mobile(text):
        """處理 Markdown 表格，讓手機好讀"""
        lines = text.split('\n')
        mobile_text = []
        for line in lines:
            if '|' in line and '---' not in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    # 將表格行轉成點列式
                    mobile_text.append(f"• {parts[0].replace('**', '')}: {' / '.join(parts[1:])}")
                else:
                    mobile_text.append(line.replace('|', '').strip())
            elif '---' in line and '|' in line:
                continue # 跳過表格分隔線
            else:
                mobile_text.append(line)
        return "\n".join(mobile_text)