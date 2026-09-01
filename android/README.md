# Douyin Content Finder — Android APK (Samsung Galaxy S9 Optimized)

> **Ứng dụng Android Native (Kotlin) kết nối Backend Server trung tâm để tìm kiếm và lọc video Douyin thông minh bằng Tiếng Việt dành cho Samsung Galaxy S9 (Android 8.0 - 10.0+).**

---

## 🏗️ Kiến Trúc Ứng Dụng (Android Native Clean Architecture)

```text
[UI (Activity / Fragments)]
         │
         ▼
[ViewModel (SearchViewModel / HistoryViewModel)]
         │
         ▼
[Repository (SearchRepository)]
    ├──► [Room Database (Offline History)]
    └──► [ApiService (Retrofit + OkHttp)]
             │
             ▼ (HTTPS/REST API)
    [BACKEND SERVER (/api/v1/*)]
```

### 🔒 Chính Sách Bảo Mật Tuyệt Đối (Thin Client)
- **APK KHÔNG chứa:**
  - ❌ AI API Keys (Google Gemini, OpenAI).
  - ❌ Database Password / Connection Strings.
  - ❌ Douyin / TikTok Cookies & Scraping Secrets.
  - ❌ AI Models nặng / TFLite / Onnx.
  - ❌ Ranking / Filter / Scoring Core.
- **Tất cả tác vụ phân tích, AI, dịch thuật, ranking và quét dữ liệu đều chạy 100% trên Backend Server.**

---

## 📱 8 Màn Hình & Tính Năng Chính (Tối Ưu Samsung Galaxy S9)

1. **Trang Chủ / Smart Vietnamese Search:**
   - Hỗ trợ nhập từ khóa tiếng Việt tự nhiên (ví dụ: *gái xinh mặc pijama che mặt*).
   - Nút `[SEARCH]` (🚀 Bắt đầu tìm kiếm).
   - Nút `[DEEP SEARCH]` (🔥 Quét sâu 30 queries).
   - Nút `[XEM TỪ KHÓA TIẾNG TRUNG]` (👁️ Preview 20 queries tối ưu Douyin).
2. **Video Search (`[UPLOAD VIDEO]`):**
   - Chọn video từ Gallery / Bộ nhớ máy $\rightarrow$ Upload lên Backend $\rightarrow$ Theo dõi thanh tiến độ realtime.
3. **Douyin URL Search (`[PASTE DOUYIN LINK]`):**
   - Dán link Douyin/TikTok từ Clipboard $\rightarrow$ Backend bóc tách metadata thật & xử lý.
4. **Tính Năng "Share To App":**
   - Lướt video trên Douyin / TikTok $\rightarrow$ Bấm nút **Chia Sẻ (Share)** $\rightarrow$ Chọn **Douyin Smart Finder** $\rightarrow$ Tự động phân tích và tìm video tương đồng.
5. **Search Results (Danh sách kết quả xếp hạng):**
   - Hiển thị Score Badge (`#1 ⭐️ 89% High Match`), Thumbnail mượt mà 60fps qua thư viện Coil.
   - Thống kê lượt thích (`❤️ Likes`), bình luận (`💬 Comments`), thời lượng video (`⏱️ Duration`).
   - Huy hiệu chi tiết **6 Sub-Scores**: `KW` (Từ khóa), `SEM` (Ngữ nghĩa), `VIS` (Hình ảnh), `SCN` (Bối cảnh), `ACT` (Hành động), `QRY` (Truy vấn).
   - Nút `MỞ XEM DOUYIN` (mở ứng dụng Douyin `snssdk1128://aweme/detail/...` hoặc trình duyệt) & `SAO CHÉP LINK`.
6. **Bộ Lọc Kết Quả (Filters):**
   - Thanh trượt độ tương đồng tối thiểu (`50% - 95%`).
   - Lọc theo lượt thích (`Min Likes`).
   - Sắp xếp theo: `Độ tương đồng`, `Lượt thích`, `Bình luận`, `Mới nhất`.
7. **Lịch Sử Tìm Kiếm (Search History):**
   - Lưu trữ offline qua **Room SQLite Database**.
   - Chạm vào bất kỳ mục lịch sử nào để tự động thực hiện lại tìm kiếm.
8. **Cài Đặt Hệ Thống (Settings):**
   - Nhập URL Backend Server (`http://10.0.2.2:8000` cho máy ảo hoặc `http://192.168.x.x:8000` cho Galaxy S9 thật).
   - Nút **"Kiểm Tra Kết Nối Backend"** với trạng thái trực quan: 🟢 Sẵn sàng / 🔴 Ngắt kết nối.
   - Nút dọn dẹp bộ nhớ đệm video cache.

---

## 🛠️ Hướng Dẫn Build APK

### Cách 1: Sử Dụng Android Studio (Khuyên Dùng)
1. Mở **Android Studio**.
2. Chọn **Open an existing project** $\rightarrow$ Trỏ tới thư mục `Tool-douyin/android/`.
3. Chờ Gradle sync hoàn tất.
4. Vào menu: **Build** $\rightarrow$ **Build Bundle(s) / APK(s)** $\rightarrow$ **Build APK(s)**.
5. File APK xuất ra tại:
   `android/app/build/outputs/apk/release/app-release.apk` (hoặc `app-debug.apk`).

### Cách 2: Sử Dụng Gradle Wrapper Command Line
```bash
cd android
./gradlew assembleDebug
# hoặc build bản Release:
./gradlew assembleRelease
```

---

## 📲 Hướng Dẫn Cài Đặt và Kết Nối Trên Samsung Galaxy S9

1. Đảm bảo máy tính và Samsung Galaxy S9 kết nối cùng mạng WiFi (hoặc cắm cáp USB).
2. Khởi động Backend trên PC:
   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
3. Chép file `app-debug.apk` vào Samsung Galaxy S9.
4. Mở ứng dụng **File của bạn (My Files)** $\rightarrow$ Chọn `app-debug.apk` $\rightarrow$ Nhấn **Cài Đặt (Install)**.
5. Mở ứng dụng **Douyin Smart Finder** $\rightarrow$ Vào tab **⚙️ Cài Đặt** $\rightarrow$ Nhập IP máy tính (ví dụ: `http://192.168.1.100:8000`) $\rightarrow$ Bấm **Kiểm Tra Kết Nối** $\rightarrow$ Hiện `🟢 Kết nối Thành Công` $\rightarrow$ Bắt đầu tìm kiếm video!
