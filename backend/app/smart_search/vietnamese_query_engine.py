import re
from typing import Dict, List, Any

class VietnameseQueryEngine:
    """
    Advanced NLP Entity & Intent Extraction Engine for Vietnamese search queries.
    Parses intent, subjects, appearance, actions, clothing, scenes, styles, and objects.
    """

    # Comprehensive Vietnamese Synonyms & Concept Mapping
    SYNONYM_DICT = {
        # Subject & People
        "gai_xinh": ["gái xinh", "hot girl", "cô gái đẹp", "người đẹp", "mỹ nữ", "tiểu tỷ tỷ", "nữ thần", "hotgirl", "gái đẹp", "cô nàng", "thiếu nữ", "bạn nữ", "em gái", "gái"],
        "trai_dep": ["chàng trai", "trai đẹp", "soái ca", "nam thần", "anh chàng", "con trai", "nam sinh", "bạn nam"],
        "hoc_sinh": ["học sinh", "sinh viên", "nữ sinh", "đồng phục", "kỷ yếu", "lớp học", "trường học"],
        "em_be": ["em bé", "trẻ con", "baby", "bé gái", "bé trai", "em bé dễ thương", "con nít"],
        "chu_tich": ["chủ tịch", "tổng tài", "sếp", "giám đốc", "đại gia"],
        "ban_than": ["bạn thân", "bạn bè", "đồng nghiệp", "hội bạn"],
        "meo": ["mèo", "mèo con", "mèo dễ thương", "hoàng thượng", "boss mèo", "mèo béo", "mèo ngủ", "mèo cưng"],
        "cho": ["chó", "chó con", "cún cưng", "cún con", "chó thông minh", "chó ngáo"],
        "xe": ["xe", "ô tô", "siêu xe", "xe hơi", "mô tô", "đua xe", "cao tốc", "tiếng pô", "tiếng máy", "tăng tốc"],

        # Appearance & Vibe
        "xinh": ["xinh", "đẹp", "dễ thương", "đáng yêu", "xinh xắn", "gợi cảm", "quyến rũ", "ngọt ngào", "thần tiên", "dáng chuẩn", "chân dài"],
        "ngau": ["ngầu", "chất", "cool", "soái", "bá đạo", "lạnh lùng"],
        "hai_huoc": ["hài", "hài hước", "vui nhộn", "buồn cười", "lầy lội", "bựa", "troll", "bể bụng", "cười bể bụng"],
        "buon": ["buồn", "tâm trạng", "cảm xúc", "cô đơn", "đêm khuya", "chữa lành", "triết lý"],

        # Clothing & Items
        "pijama": ["pijama", "đồ ngủ", "váy ngủ", "bộ ngủ", "quần áo ngủ", "pyjama", "đồ bộ"],
        "ao_dai": ["áo dài", "áo dài trắng", "áo dài truyền thống", "cổ trang", "hán phục", "sườn xám"],
        "vay": ["váy", "váy ngắn", "váy trắng", "đầm", "váy body", "chân váy", "váy hoa"],
        "bikini": ["áo tắm", "bikini", "đồ bơi", "hai mảnh", "tắm biển"],
        "mua_dong": ["mùa đông", "áo khoác", "áo len", "khăn len", "giữ ấm", "thời trang mùa đông"],
        "do_gym": ["đồ tập", "đồ gym", "quần legging", "áo bra tập gym"],

        # Actions
        "che_mat": ["che mặt", "giấu mặt", "bịt mặt", "úp mặt", "lấy tay che mặt", "giấu mặt chụp hình", "không lộ mặt", "không thấy mặt"],
        "nhay": ["nhảy", "nhảy múa", "dance", "bắt trend", "đu trend", "uốn éo", "nhún nhảy", "nhảy cover", "vũ đạo", "nhạc hot", "nhạc hot trend", "bắt nhịp"],
        "nau_an": ["nấu ăn", "làm bếp", "nấu món", "hướng dẫn nấu", "chế biến", "ẩm thực", "làm bánh", "bánh sinh nhật", "món ngon"],
        "bien_hinh": ["biến hình", "lột xác", "trước sau", "make up", "trang điểm", "trước và sau"],
        "hat": ["hát", "cover", "ca hát", "lipsync", "nhép", "nhạc buồn", "hát live"],
        "review": ["review", "đánh giá", "trải nghiệm", "mở hộp", "unbox", "ăn thử", "đập hộp", "trên tay"],
        "selfie": ["chụp ảnh", "tự sướng", "selfie", "tạo dáng", "sống ảo", "chụp kỷ yếu"],
        "tap_gym": ["tập gym", "giảm cân", "giảm mỡ", "mỡ bụng", "giảm mỡ bụng", "workout", "cardio", "tập luyện"],
        "giup_viec": ["giúp việc", "làm việc nhà", "quét nhà", "thông minh", "giúp chủ"],

        # Scene & Location
        "trong_phong": ["trong phòng", "phòng ngủ", "phòng khách", "trong nhà", "ở nhà", "phòng trọ", "giường", "trên giường"],
        "ngoai_troi": ["ngoài trời", "ngoài phố", "đường phố", "công viên", "đường cao tốc", "quán cafe", "đường sá"],
        "bep": ["nhà bếp", "góc bếp", "bếp ăn", "bếp"],
        "bien": ["biển", "bãi biển", "bờ biển", "mùa hè", "du lịch biển"],
        "nui": ["núi", "núi tuyết", "tuyết", "phong cảnh", "thiên nhiên", "rừng", "hùng vĩ", "phong cảnh thiên nhiên"]
    }

    @classmethod
    def analyze(cls, query: str) -> Dict[str, Any]:
        """
        Extracts semantic entities and determines search intent with high coverage.
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

        # 1. Subject extraction
        if any(w in q_lower for w in ["gái xinh", "hot girl", "cô gái đẹp", "người đẹp", "mỹ nữ", "gái", "cô gái", "cô nàng", "thiếu nữ", "hotgirl", "gai xinh", "co gai"]):
            entities["subject"].append("gái xinh")
        if any(w in q_lower for w in ["trai đẹp", "soái ca", "chàng trai", "nam thần", "con trai", "nam sinh"]):
            entities["subject"].append("trai đẹp")
        if any(w in q_lower for w in ["học sinh", "nữ sinh", "sinh viên", "kỷ yếu"]):
            entities["subject"].append("nữ sinh")
        if any(w in q_lower for w in ["em bé", "trẻ con", "bé gái", "bé trai", "baby"]):
            entities["subject"].append("em bé")
        if any(w in q_lower for w in ["chủ tịch", "tổng tài", "giám đốc", "sếp"]):
            entities["subject"].append("chủ tịch")
        if any(w in q_lower for w in ["mèo", "mèo con", "hoàng thượng", "boss mèo"]):
            entities["subject"].append("mèo")
        if any(w in q_lower for w in ["chó", "chó con", "cún cưng", "cún"]):
            entities["subject"].append("chó")
        if any(w in q_lower for w in ["xe", "ô tô", "siêu xe", "mô tô", "car"]):
            entities["subject"].append("siêu xe")

        # 2. Appearance & Vibe
        if any(w in q_lower for w in ["xinh", "đẹp", "dễ thương", "đáng yêu", "quyến rũ", "gợi cảm", "ngọt ngào", "xinh xắn", "dáng chuẩn"]):
            entities["appearance"].append("xinh đẹp")
        if any(w in q_lower for w in ["ngầu", "chất", "cool", "soái", "bá đạo"]):
            entities["appearance"].append("ngầu")
        if any(w in q_lower for w in ["hài", "hài hước", "vui nhộn", "buồn cười", "lầy", "troll", "bể bụng"]):
            entities["appearance"].append("hài hước")
        if any(w in q_lower for w in ["buồn", "tâm trạng", "cô đơn", "đêm khuya", "chữa lành"]):
            entities["appearance"].append("tâm trạng")

        # 3. Clothing
        if any(w in q_lower for w in ["pijama", "đồ ngủ", "váy ngủ", "bộ ngủ", "pyjama", "đồ bộ"]):
            entities["clothing"].append("pijama")
        if any(w in q_lower for w in ["áo dài", "áo dài trắng", "cổ trang", "hán phục"]):
            entities["clothing"].append("áo dài")
        if any(w in q_lower for w in ["bikini", "áo tắm", "đồ bơi"]):
            entities["clothing"].append("bikini")
        if any(w in q_lower for w in ["váy", "đầm", "váy trắng", "chân váy"]):
            entities["clothing"].append("váy")
        if any(w in q_lower for w in ["mùa đông", "áo khoác", "áo len", "đồ đông"]):
            entities["clothing"].append("đồ đông")
        if any(w in q_lower for w in ["đồ tập", "đồ gym", "quần legging"]):
            entities["clothing"].append("đồ gym")

        # 4. Actions
        if any(w in q_lower for w in ["che mặt", "giấu mặt", "bịt mặt", "úp mặt", "không lộ mặt"]):
            entities["action"].append("che mặt")
        if any(w in q_lower for w in ["nhảy", "nhảy múa", "dance", "bắt trend", "đu trend", "vũ đạo", "nhạc hot"]):
            entities["action"].append("nhảy múa")
        if any(w in q_lower for w in ["nấu ăn", "làm bếp", "nấu món", "hướng dẫn nấu", "làm bánh", "bánh sinh nhật", "ẩm thực"]):
            entities["action"].append("nấu ăn")
        if any(w in q_lower for w in ["biến hình", "lột xác", "make up", "trang điểm"]):
            entities["action"].append("biến hình")
        if any(w in q_lower for w in ["hát", "cover", "ca hát", "nhạc buồn"]):
            entities["action"].append("hát cover")
        if any(w in q_lower for w in ["review", "đánh giá", "ăn thử", "mở hộp", "đập hộp", "trên tay"]):
            entities["action"].append("review")
        if any(w in q_lower for w in ["selfie", "tự sướng", "chụp ảnh", "tạo dáng", "kỷ yếu"]):
            entities["action"].append("selfie")
        if any(w in q_lower for w in ["tập gym", "giảm cân", "giảm mỡ", "mỡ bụng", "workout"]):
            entities["action"].append("tập gym")
        if any(w in q_lower for w in ["giúp việc", "làm việc nhà", "thông minh"]):
            entities["action"].append("giúp việc nhà")
        if any(w in q_lower for w in ["mẹo vặt", "thủ thuật", "hữu ích"]):
            entities["action"].append("mẹo vặt")

        # 5. Scene & Location
        if any(w in q_lower for w in ["trong phòng", "phòng ngủ", "phòng khách", "trong nhà", "ở nhà", "giường", "ngủ"]):
            entities["scene"].append("trong phòng")
        if any(w in q_lower for w in ["ngoài trời", "đường phố", "phố", "công viên", "cao tốc", "đường cao tốc"]):
            entities["scene"].append("ngoài trời")
        if any(w in q_lower for w in ["bếp", "nhà bếp"]):
            entities["scene"].append("nhà bếp")
        if any(w in q_lower for w in ["biển", "bãi biển", "mùa hè"]):
            entities["scene"].append("bãi biển")
        if any(w in q_lower for w in ["núi", "núi tuyết", "tuyết", "phong cảnh", "thiên nhiên", "hùng vĩ"]):
            entities["scene"].append("núi tuyết")

        # 6. Style & Format
        if any(w in q_lower for w in ["đời thường", "vlog", "hàng ngày", "cuộc sống", "chill"]):
            entities["style"].append("đời thường")
        if any(w in q_lower for w in ["thời trang", "outfit", "phối đồ", "lookbook"]):
            entities["style"].append("thời trang")
        if any(w in q_lower for w in ["drama", "phim ngắn", "cái kết", "tiểu phẩm"]):
            entities["style"].append("drama")

        # 7. Determine Intent
        intent = "VISUAL_CONTENT_SEARCH"
        if "nấu ăn" in entities["action"] or "tập gym" in entities["action"] or "mẹo vặt" in entities["action"] or "hướng dẫn" in q_lower:
            intent = "ACTION_TUTORIAL"
        elif "nhảy múa" in entities["action"] or "biến hình" in entities["action"] or "trend" in q_lower or "nhạc hot" in q_lower:
            intent = "TREND_SEARCH"
        elif "review" in entities["action"] or "đập hộp" in q_lower or "điện thoại" in q_lower:
            intent = "PRODUCT_SEARCH"
        elif "hài hước" in entities["appearance"] or "drama" in entities["style"]:
            intent = "GENERAL_ENTERTAINMENT"

        return {
            "original_query": query,
            "intent": intent,
            "entities": {k: v for k, v in entities.items() if v}
        }
