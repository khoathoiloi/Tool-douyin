import re
from typing import Literal

LanguageType = Literal["vi", "zh", "en", "auto", "other"]

class LanguageDetector:
    # Vietnamese diacritics pattern
    VIETNAMESE_DIACRITICS_REGEX = re.compile(
        r"[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ]",
        re.IGNORECASE
    )
    
    # Common Vietnamese unaccented words (useful if user types without accents)
    VIETNAMESE_UNACCENTED_WORDS = {
        "gai", "xinh", "mac", "che", "mat", "trong", "phong", "dep", "nhay", "mua",
        "nau", "an", "hai", "meo", "cho", "oto", "xe", "quan", "ao", "vay", "do",
        "ngu", "review", "co", "em", "hotgirl", "nguoi", "doi", "thuong", "hoc",
        "sinh", "ao", "dai", "nu", "nam", "tet", "xuan", "bien", "dao"
    }

    # Chinese CJK Unified Ideographs range
    CHINESE_CHAR_REGEX = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")

    # Common English words
    ENGLISH_WORDS = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "by",
        "girl", "girls", "beautiful", "cute", "wearing", "pajamas", "dress", "dance",
        "dancing", "cooking", "room", "funny", "cat", "dog", "car", "review", "food",
        "style", "face", "covered", "hiding", "mask", "hot", "pretty", "woman", "video"
    }

    @classmethod
    def detect(cls, text: str, preferred: str = "auto") -> LanguageType:
        """
        Detects whether the input text is Vietnamese ('vi'), Chinese ('zh'), English ('en'),
        or handles 'auto' detection with high accuracy.
        """
        if not text or not text.strip():
            return "auto" if preferred == "auto" else preferred  # type: ignore

        if preferred in ["vi", "zh", "en"] and preferred != "auto":
            return preferred  # type: ignore

        clean_text = text.strip()
        total_len = len(clean_text)

        # 1. Check for Chinese characters
        chinese_matches = cls.CHINESE_CHAR_REGEX.findall(clean_text)
        if len(chinese_matches) > 0 and (len(chinese_matches) / max(1, total_len) >= 0.25 or len(chinese_matches) >= 2):
            return "zh"

        # 2. Check for Vietnamese characters with diacritics
        if cls.VIETNAMESE_DIACRITICS_REGEX.search(clean_text):
            return "vi"

        # 3. Check for unaccented Vietnamese words
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", clean_text)]
        vi_word_count = sum(1 for w in words if w in cls.VIETNAMESE_UNACCENTED_WORDS)
        en_word_count = sum(1 for w in words if w in cls.ENGLISH_WORDS)

        if vi_word_count > 0 and vi_word_count >= en_word_count:
            return "vi"
        elif en_word_count > 0:
            return "en"

        # Default fallback
        # If Latin characters without specific matches, consider based on word structure
        return "vi" if any(w in clean_text.lower() for w in ["gai", "xinh", "mac", "pijama"]) else "en"
