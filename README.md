# Douyin Smart Search & AI Content Finder

> **Hệ thống Web Application & AI Đa phương thức (Multimodal AI) tìm kiếm video Douyin thông minh: Hỗ trợ người dùng nhập từ khóa bằng Tiếng Việt (hoặc Tiếng Anh / Tiếng Trung), AI tự động nhận diện ngôn ngữ, phân tích ý định (Intent & Semantic Entities), chuyển ngữ tự nhiên chuẩn văn phong tìm kiếm Douyin (không dịch từng chữ máy móc), quét đa tầng và Re-ranking video Douyin triệu view.**

---

## 🌟 Tính Năng Cốt Lõi (Core Features)

### 1. 🇻🇳 Vietnamese → Chinese Smart Douyin Search Engine (Mới)
- **Tự động nhận diện ngôn ngữ:** Phát hiện `vi` (Tiếng Việt), `zh` (Tiếng Trung), `en` (Tiếng Anh) hoặc chế độ `auto`.
- **Phân tích Ý định & Thực thể Ngữ nghĩa:** Tách bạch *Subject (chủ thể), Appearance (ngoại hình), Clothing (trang phục), Action (hành động), Scene (bối cảnh), Style (phong cách)*.
- **Dịch theo Ngữ nghĩa & Douyin Search Idioms:** Không dịch word-by-word máy móc mà ánh xạ sang từ khóa người bản xứ thực tế dùng để tìm trên Douyin.
- **Phân cấp Từ khóa & Đánh giá Điểm chất lượng (Quality Score 0–100):**
  - `EXACT` (Điểm 95–100): Ví dụ `美女穿睡衣遮脸`
  - `HIGH` (Điểm 88–94): Ví dụ `美女睡衣自拍`, `高颜值女生睡衣`
  - `MEDIUM` (Điểm 75–87): Ví dụ `美女睡衣日常`, `女生睡衣遮脸`
  - `BROAD` (Điểm 50–74): Ví dụ `美女睡衣`, `睡衣女孩`
- **Bộ lọc Negative Keywords:** Tự động phát hiện và lọc bỏ các video quảng cáo, shop bán hàng (`广告`, `商品`, `店铺`, `买`).
- **2 Chế độ Tìm kiếm:** `Auto Mode` (tìm kiếm tức thì) và `Manual Mode` (mở Translation Preview cho phép người dùng tick chọn / sửa / thêm từ khóa).

### 2. 📹 Video & Link Multi-Layer AI Pipeline
- Tải lên video kéo-thả hoặc dán link Douyin / TikTok.
- Bóc tách khung hình & âm thanh bằng **FFmpeg**, phân tích ASR lời thoại + OCR phụ đề.
- Sinh bộ 20 truy vấn phân nhóm và quét toàn diện Douyin.

### 3. 🎯 Multi-Criteria Re-Ranking Engine
- Công thức xếp hạng chuẩn:
  $$\text{Score} = 0.30 \times \text{Visual} + 0.25 \times \text{Semantic} + 0.15 \times \text{Action} + 0.10 \times \text{Scene} + 0.15 \times \text{Keyword} + 0.05 \times \text{Query Quality}$$
- Khử trùng lặp video (Deduplication) theo Video ID, URL và độ tương đồng tiêu đề.

---

## 🚀 Hướng Dẫn Khởi Động Nhanh

### Cách 1: Chạy Web Application bằng file 1-Click (Khuyên dùng)
Chỉ cần nhấp đúp chuột vào file:
```bash
run_web.bat
```
Sau đó mở trình duyệt (Chrome / Cốc Cốc / Edge) và truy cập:
👉 **`http://127.0.0.1:8000`**

---

### Cách 2: Chạy qua dòng lệnh (Command Line)
```bash
# 1. Cài đặt thư viện phụ thuộc
pip install -r requirements.txt

# 2. Khởi động Web Server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🔌 Danh Sách REST API Endpoints

### 🟢 Smart Search APIs (Mới)
- `POST /api/v1/query/translate`: Phân tích ý định câu tiếng Việt/Anh và sinh bộ từ khóa tiếng Trung preview.
- `POST /api/v1/query/generate`: Sinh các biến thể query Douyin.
- `POST /api/v1/search/smart`: Tìm kiếm thông minh toàn diện (chấp nhận tiếng Việt, tự động Re-ranking).

### 🔵 Video & Pipeline APIs
- `POST /api/v1/search/video`: Tải lên video và chạy pipeline AI.
- `POST /api/v1/search/url`: Dán link Douyin/TikTok để phân tích.
- `GET /api/v1/search/{job_id}`: Kiểm tra tiến độ xử lý realtime (0% - 100%).
- `GET /api/v1/search/{job_id}/results`: Lấy danh sách video Douyin đã xếp hạng & phân trang.
- `GET /api/v1/history`: Lấy lịch sử tìm kiếm.

---

## 🧪 Chạy Kiểm Thử Tự Động (Unit & Integration Tests)

```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```
