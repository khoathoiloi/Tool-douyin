import re
from typing import Dict, List, Any

class VietnameseQueryEngine:
    """
    NLP Entity & Intent Extraction Engine for Vietnamese search queries.
    Parses intent, subjects, actions, clothing, scenes, and styles.
    """

    # Comprehensive Vietnamese Synonyms & Concept Mapping
    SYNONYM_DICT = {
        # Subject & People
        "gai xinh": ["gái xinh", "hot girl", "cô gái đẹp", "người đẹp", "mỹ nữ", "tiểu tỷ tỷ", "nữ thần", "hotgirl", "gái đẹp"],
        "co gai": ["cô gái", "cô em", "thiếu nữ", "bạn nữ", "em gái"],
        "chang trai": ["chàng trai", "trai đẹp", "soái ca", "nam thần", "anh chàng"],
        "hoc sinh": ["học sinh", "sinh viên", "nữ sinh", "đồng phục"],
        "nguoi mau": ["người mẫu", "mẫu ảnh", "model", "chân dài"],
        "meo": ["mèo", "mèo con", "mèo dễ thương", "hoàng thượng", "boss mèo", "mèo béo"],
        "cho": ["chó", "chó con", "cún cưng", "cún con"],
        "em be": ["em bé", "trẻ con", "baby", "dễ thương", "đáng yêu"],

        # Appearance & Vibe
        "xinh": ["xinh", "đẹp", "dễ thương", "đáng yêu", "xinh xắn", "dễ thương", "gợi cảm", "quyến rũ", "ngọt ngào", "thần tiên"],
        "ngau": ["ngầu", "chất", "cool", "soái", "bá đạo"],
        "hai huoc": ["hài", "hài hước", "vui nhộn", "buồn cười", "lầy lội", "bựa", "troll"],

        # Clothing & Items
        "pijama": ["pijama", "đồ ngủ", "váy ngủ", "bộ ngủ", "quần áo ngủ", "pyjama"],
        "vay": ["váy", "váy ngắn", "váy trắng", "đầm", "váy body", "chân váy"],
        "ao dai": ["áo dài", "áo dài truyền thống", "cổ trang", "hán phục"],
        "ao tam": ["áo tắm", "bikini", "đồ bơi"],
        "kinh": ["kính", "mắt kính", "đeo kính"],
        "khau trang": ["khẩu trang", "bịt mặt"],

        # Actions
        "che mat": ["che mặt", "giấu mặt", "bịt mặt", "úp mặt", "lấy tay che mặt", "giấu mặt chụp hình"],
        "nhay": ["nhảy", "nhảy múa", "dance", "bắt trend", "đu trend", "uốn éo", "nhún nhảy", "nhảy cover"],
        "nau an": ["nấu ăn", "làm bếp", "nấu món", "hướng dẫn nấu", "chế biến", "ẩm thực"],
        "bien hinh": ["biến hình", "lột xác", "trước sau", "make up", "trang điểm"],
        "hat": ["hát", "cover", "ca hát", "lipsync", "nhép"],
        "review": ["review", "đánh giá", "trải nghiệm", "mở hộp", "unbox", "ăn thử"],
        "chup anh": ["chụp ảnh", "tự sướng", "selfie", "tạo dáng", "sống ảo"],

        # Scene & Location
        "trong phong": ["trong phòng", "phòng ngủ", "phòng khách", "trong nhà", "ở nhà", "phòng trọ", "giường", "trên giường"],
        "ngoai troi": ["ngoài trời", "ngoài phố", "đường phố", "công viên", "bờ biển", "biển", "quán cafe"],
        "bep": ["nhà bếp", "góc bếp", "bếp ăn"],
        "xe": ["xe", "ô tô", "siêu xe", "xe hơi", "trong xe"],

        # Style & Content Format
        "doi thuong": ["đời thường", "cuộc sống", "vlog", "hàng ngày", "chill"],
        "phong cach": ["phong cách", "thời trang", "outfit", "phối đồ", "lookbook"]
    }

    @classmethod
    def analyze(cls, query: str) -> Dict[str, Any]:
        """
        Extracts semantic entities and determines search intent.
        """
        q_lower = query.lower().strip()

        entities: Dict[str, List[str]] = {
            "subject": [],
            "appearance": [],
            "clothing": [],
            "action": [],
            "scene": [],
            "style": []
        }

        # Subject extraction
        if any(w in q_lower for w in ["gái xinh", "hot girl", "cô gái đẹp", "người đẹp", "mỹ nữ", "gái", "nữ sinh", "hotgirl", "gai xinh", "co gai"]):
            entities["subject"].append("gái xinh")
        elif any(w in q_lower for w in ["trai đẹp", "soái ca", "chàng trai", "nam thần", "con trai"]):
            entities["subject"].append("trai đẹp")
        elif any(w in q_lower for w in ["mèo", "mèo con", "hoàng thượng", "cún", "chó"]):
            entities["subject"].append("thú cưng")
        elif any(w in q_lower for w in ["xe", "ô tô", "siêu xe", "car"]):
            entities["subject"].append("ô tô")

        # Appearance extraction
        if any(w in q_lower for w in ["xinh", "đẹp", "dễ thương", "đáng yêu", "quyến rũ", "gợi cảm", "ngọt ngào", "xinh xắn"]):
            entities["appearance"].append("xinh đẹp")
        if any(w in q_lower for w in ["hài", "hài hước", "vui nhộn", "buồn cười", "lầy"]):
            entities["appearance"].append("hài hước")

        # Clothing extraction
        if any(w in q_lower for w in ["pijama", "đồ ngủ", "váy ngủ", "bộ ngủ", "pyjama"]):
            entities["clothing"].append("pijama")
        if any(w in q_lower for w in ["áo dài", "cổ trang", "hán phục"]):
            entities["clothing"].append("áo dài")
        if any(w in q_lower for w in ["váy", "đầm", "váy trắng", "chân váy"]):
            entities["clothing"].append("váy")
        if any(w in q_lower for w in ["bikini", "đồ bơi"]):
            entities["clothing"].append("bikini")

        # Action extraction
        if any(w in q_lower for w in ["che mặt", "giấu mặt", "bịt mặt", "úp mặt"]):
            entities["action"].append("che mặt")
        if any(w in q_lower for w in ["nhảy", "nhảy múa", "dance", "bắt trend", "đu trend"]):
            entities["action"].append("nhảy múa")
        if any(w in q_lower for w in ["nấu ăn", "làm bếp", "làm bánh", "nấu nướng"]):
            entities["action"].append("nấu ăn")
        if any(w in q_lower for w in ["biến hình", "lột xác", "make up"]):
            entities["action"].append("biến hình")
        if any(w in q_lower for w in ["tự sướng", "selfie", "chụp ảnh", "tạo dáng"]):
            entities["action"].append("selfie")
        if any(w in q_lower for w in ["review", "đánh giá", "ăn thử", "mở hộp"]):
            entities["action"].append("review")

        # Scene extraction
        if any(w in q_lower for w in ["trong phòng", "phòng ngủ", "phòng khách", "trong nhà", "ở nhà", "giường"]):
            entities["scene"].append("trong phòng")
        if any(w in q_lower for w in ["ngoài trời", "đường phố", "phố", "công viên", "biển"]):
            entities["scene"].append("ngoài trời")
        if any(w in q_lower for w in ["bếp", "nhà bếp"]):
            entities["scene"].append("nhà bếp")

        # Style extraction
        if any(w in q_lower for w in ["đời thường", "vlog", "hàng ngày", "cuộc sống"]):
            entities["style"].append("đời thường")
        if any(w in q_lower for w in ["selfie", "tự sướng", "sống ảo"]):
            entities["style"].append("selfie")
        if any(w in q_lower for w in ["thời trang", "outfit", "phối đồ"]):
            entities["style"].append("phối đồ")

        # Determine Intent
        intent = "VISUAL_CONTENT_SEARCH"
        if "nấu ăn" in entities["action"] or "hướng dẫn" in q_lower:
            intent = "ACTION_TUTORIAL"
        elif "nhảy múa" in entities["action"] or "trend" in q_lower:
            intent = "TREND_SEARCH"
        elif "review" in entities["action"] or "mua" in q_lower:
            intent = "PRODUCT_SEARCH"
        elif "hài hước" in entities["appearance"]:
            intent = "GENERAL_ENTERTAINMENT"

        return {
            "original_query": query,
            "intent": intent,
            "entities": {k: v for k, v in entities.items() if v}
        }
