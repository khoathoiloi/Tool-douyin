# Douyin Content Finder — Android APK (Tối ưu Samsung Galaxy S9)

> **Ứng dụng Android Native (Kotlin) kết nối Backend Server để tìm kiếm và lọc video Douyin thông minh dành cho Samsung Galaxy S9 (Android 8.0 - 10.0).**

---

## 📱 Đặc Tính Tối Ưu Cho Samsung Galaxy S9

1. **Hiệu Năng Cực Nhẹ & Tiết Kiệm Pin:**
   - Dung lượng RAM sử dụng < 80MB.
   - Không chạy các model AI nặng cục bộ trên điện thoại; toàn bộ tác vụ phân tích đa phương thức (Vision, ASR, OCR, Keyword Engine) đều được offload về Backend Server.
2. **Hỗ Trợ 3 Chế Độ Input:**
   - 📁 **Chọn Video từ máy:** Hệ thống file picker chuẩn Android (`ACTION_GET_CONTENT`), không yêu cầu quyền lưu trữ nguy hiểm.
   - 🔗 **Dán Link Douyin / TikTok:** Tự động kiểm tra và nhận diện link rút gọn / link đầy đủ.
   - 🔎 **Nhập Keyword Trực Tiếp:** Quét nhanh theo từ khóa tiếng Trung mà không cần video.
3. **Tính Năng "Share To App" (Chia sẻ liên kết):**
   - Đang lướt video trên Douyin / TikTok $\rightarrow$ Bấm nút **Chia Sẻ (Share)** $\rightarrow$ Chọn **Douyin Search** $\rightarrow$ Ứng dụng tự động mở và tìm kiếm ngay lập tức!
4. **Bộ Nhớ Đệm Ảnh Thumbnail (Coil Cache):**
   - Tự động nén và lưu đệm ảnh thumbnail của video Douyin, cuộn danh sách kết quả 60fps mượt mà trên màn hình Super AMOLED của Galaxy S9.
5. **Lưu Lịch Sử Offline:**
   - Tích hợp **Room Database** lưu lại các phiên tìm kiếm để xem lại mọi lúc kể cả khi không có mạng.

---

## 🛠️ Hướng Dẫn Build File APK

### Cách 1: Mở Bằng Android Studio (Khuyên dùng)
1. Mở **Android Studio**.
2. Chọn **Open an existing project** $\rightarrow$ Chọn thư mục `android/` trong dự án này.
3. Nhấn menu: **Build** $\rightarrow$ **Build Bundle(s) / APK(s)** $\rightarrow$ **Build APK(s)**.
4. File APK sẽ được tạo tại:
   `android/app/build/outputs/apk/release/app-release.apk`

---

### Cách 2: Build Bằng Dòng Lệnh (Command Line)
```bash
cd android
./gradlew assembleRelease
```

---

## 📲 Hướng Dẫn Cài Đặt Lên Samsung Galaxy S9

1. Chép file `app-release.apk` vào bộ nhớ điện thoại Samsung Galaxy S9 (qua cáp USB, Zalo, Telegram hoặc Google Drive).
2. Trên điện thoại, mở ứng dụng **File của bạn (My Files)** $\rightarrow$ Chọn file `app-release.apk`.
3. Bật tùy chọn *"Cho phép cài đặt từ nguồn này"* nếu có thông báo.
4. Nhấn **Cài đặt (Install)** $\rightarrow$ Mở ứng dụng **Douyin Search** và bắt đầu sử dụng!
