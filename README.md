# Douyin Smart Search — Central Backend API & AI Multimodal Engine

> **Hệ thống Central Backend API & AI Đa phương thức tập trung cho toàn bộ ứng dụng PC, Web SPA và Android APK.**
> Toàn bộ logic NLP, AI Analysis, Douyin Crawler, Re-ranking và Secret Keys (`GEMINI_API_KEY`, `DOUYIN_COOKIE`) được bảo mật tuyệt đối tại Backend. Các client (PC, Web, Android) giao tiếp với Backend thông qua REST API `/api/v1/*`.

---

## 🏛️ Kiến Trúc Hệ Thống (Central Backend Architecture)

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Desktop GUI   │       │   Web SPA UI    │       │   Android APK   │
│ (CustomTkinter) │       │   (HTML/CSS/JS) │       │ (Kotlin Native) │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   ▼ HTTP / HTTPS
                    ┌───────────────────────────────┐
                    │    FASTAPI CENTRAL BACKEND    │
                    │        Prefix: /api/v1/       │
                    └──────────────┬────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│  AI Engine (Gemini) │ │ Douyin Live Crawler │ │ Multi-Factor Ranker │
│ & Smart NLP (VN->ZH)│ │ & No-Watermark CDN  │ │ (6-Dimension Scorer)│
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

---

## 🚀 Khởi Động Backend Server

### 1. Cài đặt môi trường
```bash
# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Sao chép file `.env.example` thành `.env` và điền API Key:
```bash
copy .env.example .env
```

### 3. Chạy Server
- **Cách 1 (1-Click):** Nhấp đúp chuột vào file `run_web.bat`
- **Cách 2 (Dòng lệnh):**
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Sau khi chạy:
- **Giao diện Web SPA:** `http://127.0.0.1:8000`
- **Tài liệu Swagger UI:** `http://127.0.0.1:8000/docs`
- **Tài liệu ReDoc:** `http://127.0.0.1:8000/redoc`
- **OpenAPI JSON Spec:** `http://127.0.0.1:8000/api/openapi.json`

---

## 🔌 Danh Sách Chi Tiết Các REST API Endpoints (`/api/v1/`)

| Method | Endpoint | Mô tả |
| :--- | :--- | :--- |
| `POST` | `/api/v1/search` | Tìm kiếm Douyin thông minh (Nhận diện Tiếng Việt/Trung/Anh, lọc trùng lặp & Re-ranking). |
| `POST` | `/api/v1/analyze/video` | Tải lên video file và kích hoạt Background AI Pipeline (ASR + OCR + Bối cảnh). |
| `POST` | `/api/v1/analyze/url` | Phân tích video Douyin / TikTok từ đường dẫn URL. |
| `POST` | `/api/v1/files` | Upload file độc lập trả về metadata & đường dẫn lưu trữ. |
| `GET` | `/api/v1/jobs/{job_id}` | Polling trạng thái tiến độ thời gian thực của Job (0% - 100%). |
| `GET` | `/api/v1/search/{job_id}/results` | Lấy danh sách kết quả video Douyin đã xếp hạng và phân trang. |
| `GET` | `/api/v1/history` | Lấy danh sách lịch sử tìm kiếm & phân tích. |
| `POST` | `/api/v1/history` | Ghi nhận một phiên tìm kiếm vào lịch sử. |
| `DELETE` | `/api/v1/history/{id}` | Xóa một phiên lịch sử tìm kiếm. |
| `GET` | `/api/v1/settings` | Lấy cấu hình hệ thống hiện tại (đã ẩn các ký tự secret key). |
| `PUT` | `/api/v1/settings` | Cập nhật runtime cấu hình AI Provider, Cookie, Trọng số Re-ranking. |
| `POST` | `/api/v1/query/translate` | Dịch & xem trước bộ từ khóa tiếng Trung phân nhóm cho câu tiếng Việt. |
| `POST` | `/api/v1/query/generate` | Sinh các biến thể truy vấn tiếng Trung kèm điểm chất lượng. |

---

## 🧪 Kiểm Thử Tự Động (Unit & Integration Tests)

Chạy toàn bộ 31 test cases (Bao gồm Smart Search, Central API, Video Pipeline, Endpoints):
```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```
