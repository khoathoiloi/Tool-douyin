"""
GUI Module: Douyin Video Extractor & AI Filter Desktop Application (Phase 7).
Migrated to centralized Backend API architecture (Client-Server).
PC does not run AI directly or compute rankings locally; all operations flow through /api/v1.
"""

import os
import sys
import json
import time
import webbrowser
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

from gui.api_client import BackendApiClient

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


class DouyinExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Douyin Smart Search & AI Discovery - Desktop Client (by khoathoiloi)")
        self.geometry("1150x780")
        self.minsize(980, 680)

        # Application state
        self.raw_videos = []
        self.filtered_videos = []
        self.current_job_id = None
        self.current_preview_data = None
        self.is_searching = False

        # Load configuration
        self.config = self._load_config()

        # Initialize Backend API Client
        self.api_client = BackendApiClient(base_url=self.config.get("backend_url", "http://localhost:8000"))

        # Build UI layout
        self._build_ui()

    def _load_config(self) -> dict:
        default_config = {
            "backend_url": "http://localhost:8000",
            "download_folder": os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads"),
            "theme": "Dark"
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception:
                pass
        return default_config

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Left Navigation Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="🎵 Douyin Search",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))

        self.version_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Smart Multimodal Client v2.0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Navigation buttons
        self.nav_btn_smart = ctk.CTkButton(
            self.sidebar_frame, text="✨ Tìm Kiếm Tiếng Việt", command=lambda: self._select_tab("smart"),
            height=40, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.nav_btn_smart.grid(row=2, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_upload = ctk.CTkButton(
            self.sidebar_frame, text="📹 Tải Lên Video File", command=lambda: self._select_tab("upload"),
            height=40, font=ctk.CTkFont(size=13)
        )
        self.nav_btn_upload.grid(row=3, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_url = ctk.CTkButton(
            self.sidebar_frame, text="🔗 Dán Link Douyin", command=lambda: self._select_tab("url"),
            height=40, font=ctk.CTkFont(size=13)
        )
        self.nav_btn_url.grid(row=4, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_results = ctk.CTkButton(
            self.sidebar_frame, text="📊 Kết Quả & Bộ Lọc", command=lambda: self._select_tab("results"),
            height=40, font=ctk.CTkFont(size=13)
        )
        self.nav_btn_results.grid(row=5, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_history = ctk.CTkButton(
            self.sidebar_frame, text="🕒 Lịch Sử Tìm Kiếm", command=lambda: self._select_tab("history"),
            height=40, font=ctk.CTkFont(size=13)
        )
        self.nav_btn_history.grid(row=6, column=0, padx=15, pady=6, sticky="ew")

        self.nav_btn_settings = ctk.CTkButton(
            self.sidebar_frame, text="⚙️ Cài Đặt Backend", command=lambda: self._select_tab("settings"),
            height=40, font=ctk.CTkFont(size=13)
        )
        self.nav_btn_settings.grid(row=7, column=0, padx=15, pady=6, sticky="ew")

        # Bottom stats / Health indicator
        self.status_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.status_box.grid(row=8, column=0, padx=15, pady=15, sticky="s")

        self.lbl_server_status = ctk.CTkLabel(
            self.status_box,
            text="🟢 Backend: Sẵn sàng",
            font=ctk.CTkFont(size=11),
            text_color="#48BB78"
        )
        self.lbl_server_status.pack(anchor="w")

        self.lbl_stats = ctk.CTkLabel(
            self.status_box,
            text="Kết quả hiện tại: 0",
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        self.lbl_stats.pack(anchor="w", pady=(3, 0))

        # Right Main Container
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tab_frames = {
            "smart": self._create_smart_search_tab(),
            "upload": self._create_upload_tab(),
            "url": self._create_url_tab(),
            "results": self._create_results_tab(),
            "history": self._create_history_tab(),
            "settings": self._create_settings_tab()
        }

        self._select_tab("smart")

    def _select_tab(self, tab_name: str):
        for name, frame in self.tab_frames.items():
            if name == tab_name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        buttons = {
            "smart": self.nav_btn_smart,
            "upload": self.nav_btn_upload,
            "url": self.nav_btn_url,
            "results": self.nav_btn_results,
            "history": self.nav_btn_history,
            "settings": self.nav_btn_settings
        }
        for name, btn in buttons.items():
            if name == tab_name:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            else:
                btn.configure(fg_color="transparent")

    # ================= TAB 1: SMART VIETNAMESE SEARCH =================
    def _create_smart_search_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            frame,
            text="✨ Tìm Kiếm Tiếng Việt Thông Minh (Vietnamese → Chinese AI Engine)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        sub_lbl = ctk.CTkLabel(
            frame,
            text="Nhập từ khóa bằng Tiếng Việt. Backend AI sẽ tự động phân tích ý định, chuyển ngữ tự nhiên sang tiếng Trung và xếp hạng video Douyin.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=850,
            justify="left"
        )
        sub_lbl.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # Input Area
        input_box = ctk.CTkFrame(frame)
        input_box.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        input_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_box, text="Từ khóa tìm kiếm:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.smart_entry = ctk.CTkEntry(input_box, placeholder_text="Ví dụ: gái xinh mặc pijama che mặt, cô gái nấu ăn, mèo hài hước...", height=38)
        self.smart_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.smart_entry.insert(0, "gái xinh mặc pijama che mặt")

        self.chk_deep_search = ctk.CTkCheckBox(input_box, text="🔥 Deep Search (30 queries)")
        self.chk_deep_search.grid(row=0, column=2, padx=10, pady=10)

        # Action Buttons Row
        btn_row = ctk.CTkFrame(input_box, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        btn_row.grid_columnconfigure(0, weight=1)

        self.btn_preview_kw = ctk.CTkButton(
            btn_row,
            text="👁️ Xem Trước Từ Khóa Tiếng Trung",
            command=self._on_preview_keywords,
            height=35,
            fg_color="#4A5568",
            hover_color="#2D3748"
        )
        self.btn_preview_kw.pack(side="left", padx=(0, 10))

        self.btn_run_smart_search = ctk.CTkButton(
            btn_row,
            text="🚀 Bắt Đầu Tìm Kiếm Trên Douyin",
            command=self._on_execute_smart_search,
            font=ctk.CTkFont(weight="bold"),
            height=35,
            fg_color="#2FA572",
            hover_color="#1E7A52"
        )
        self.btn_run_smart_search.pack(side="right")

        # Results / Preview details
        preview_box = ctk.CTkFrame(frame)
        preview_box.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="nsew")
        preview_box.grid_rowconfigure(0, weight=1)
        preview_box.grid_columnconfigure(0, weight=1)

        self.smart_output_text = ctk.CTkTextbox(preview_box, font=ctk.CTkFont(family="Consolas", size=13))
        self.smart_output_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        return frame

    def _on_preview_keywords(self):
        q = self.smart_entry.get().strip()
        if not q:
            messagebox.showwarning("Thông báo", "Vui lòng nhập từ khóa tìm kiếm.")
            return

        self.btn_preview_kw.configure(state="disabled", text="⏳ Đang sinh từ khóa...")
        mode = "deep" if self.chk_deep_search.get() else "normal"

        def _worker():
            try:
                res = self.api_client.translate_query(query=q, mode=mode)
                self.after(0, lambda: self._display_preview_data(res))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi API", f"Không thể kết nối Backend:\n{e}"))
                self.after(0, lambda: self.btn_preview_kw.configure(state="normal", text="👁️ Xem Trước Từ Khóa Tiếng Trung"))

        threading.Thread(target=_worker, daemon=True).start()

    def _display_preview_data(self, res: dict):
        self.btn_preview_kw.configure(state="normal", text="👁️ Xem Trước Từ Khóa Tiếng Trung")
        self.smart_output_text.delete("0.0", "end")

        out = "=== KẾT QUẢ SINH TỪ KHÓA & TRUY VẤN DOUYIN (TỪ BACKEND API) ===\n\n"
        out += f"📌 Truy vấn gốc: {res.get('original_query')}\n"
        out += f"🌐 Ngôn ngữ nhận diện: {res.get('detected_language')}\n"
        out += f"🎯 Ý định tìm kiếm (Intent): {res.get('intent')}\n\n"

        out += "🇨🇳 CÁC NHÓM TỪ KHÓA TIẾNG TRUNG TÁCH ĐƯỢC:\n"
        cats = res.get("chinese_keywords", {})
        for cat_name, kw_list in cats.items():
            out += f"   • {cat_name.upper()}: {', '.join(kw_list)}\n"

        out += "\n🔥 DANH SÁCH SEARCH QUERIES TỐI ƯU DOUYIN:\n"
        for q_item in res.get("query_scores", []):
            out += f"   [{q_item.get('tier', '').upper():<5} - {q_item.get('score')}đ] {q_item.get('query')}\n"

        self.smart_output_text.insert("0.0", out)

    def _on_execute_smart_search(self):
        q = self.smart_entry.get().strip()
        if not q:
            messagebox.showwarning("Thông báo", "Vui lòng nhập từ khóa tìm kiếm.")
            return

        self.btn_run_smart_search.configure(state="disabled", text="⏳ Đang quét...")
        mode = "deep" if self.chk_deep_search.get() else "normal"

        def _worker():
            try:
                res = self.api_client.smart_search(
                    query=q,
                    mode=mode,
                    min_score=float(self.min_score_slider.get() if hasattr(self, 'min_score_slider') else 60.0),
                    sort_by="similarity"
                )
                self.raw_videos = res.get("results", [])
                self.after(0, self._on_search_completed)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi API", f"Lỗi tìm kiếm từ Backend:\n{e}"))
                self.after(0, lambda: self.btn_run_smart_search.configure(state="normal", text="🚀 Bắt Đầu Tìm Kiếm Trên Douyin"))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_search_completed(self):
        self.btn_run_smart_search.configure(state="normal", text="🚀 Bắt Đầu Tìm Kiếm Trên Douyin")
        self._select_tab("results")
        self._apply_results_filters()

    # ================= TAB 2: VIDEO UPLOAD & MULTIMODAL =================
    def _create_upload_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(frame, text="📹 Tải Lên Video & Phân Tích Đa Tầng (AI Multimodal)", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        sub_lbl = ctk.CTkLabel(
            frame,
            text="Tải lên file video (.mp4, .mov). Backend sẽ tự động chạy trích xuất bối cảnh, nhân vật, hành động, OCR, ASR rồi quét Douyin tìm video tương đồng.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=850,
            justify="left"
        )
        sub_lbl.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        box = ctk.CTkFrame(frame)
        box.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(box, text="File Video:").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        self.txt_video_path = ctk.CTkEntry(box, placeholder_text="Chọn đường dẫn file video .mp4...")
        self.txt_video_path.grid(row=0, column=1, padx=10, pady=12, sticky="ew")

        btn_browse = ctk.CTkButton(box, text="📁 Chọn File", width=90, command=self._on_browse_video_file)
        btn_browse.grid(row=0, column=2, padx=(0, 15), pady=12)

        ctk.CTkLabel(box, text="Gợi ý chủ đề:").grid(row=1, column=0, padx=15, pady=12, sticky="w")
        self.txt_video_hint = ctk.CTkEntry(box, placeholder_text="Tùy chọn: Nhập thêm gợi ý (ví dụ: Video nhảy hot trend, hướng dẫn làm bánh...)")
        self.txt_video_hint.grid(row=1, column=1, columnspan=2, padx=10, pady=12, sticky="ew")

        self.btn_upload_video = ctk.CTkButton(
            frame,
            text="🚀 Bắt Đầu Upload & Phân Tích Video",
            font=ctk.CTkFont(weight="bold"),
            height=40,
            command=self._on_start_video_upload
        )
        self.btn_upload_video.grid(row=3, column=0, padx=20, pady=15, sticky="ew")

        self.lbl_upload_progress = ctk.CTkLabel(frame, text="Trạng thái: Sẵn sàng", text_color="gray70")
        self.lbl_upload_progress.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="w")

        return frame

    def _on_browse_video_file(self):
        f = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.mov;*.mkv;*.avi")])
        if f:
            self.txt_video_path.delete(0, "end")
            self.txt_video_path.insert(0, f)

    def _on_start_video_upload(self):
        fpath = self.txt_video_path.get().strip()
        if not fpath or not os.path.exists(fpath):
            messagebox.showwarning("Thông báo", "Vui lòng chọn file video hợp lệ.")
            return

        hint = self.txt_video_hint.get().strip()
        self.btn_upload_video.configure(state="disabled", text="⏳ Đang tải lên và phân tích...")
        self.lbl_upload_progress.configure(text="Đang tải video lên Backend...")

        def _worker():
            try:
                res = self.api_client.analyze_video_file(file_path=fpath, user_hint=hint)
                job_id = res.get("job_id")
                self.current_job_id = job_id
                self._poll_job_progress(job_id)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi Upload", f"Không thể upload video:\n{e}"))
                self.after(0, lambda: self.btn_upload_video.configure(state="normal", text="🚀 Bắt Đầu Upload & Phân Tích Video"))

        threading.Thread(target=_worker, daemon=True).start()

    # ================= TAB 3: DOUYIN URL SEARCH =================
    def _create_url_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(frame, text="🔗 Dán Link Douyin / TikTok (URL Search)", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        sub_lbl = ctk.CTkLabel(
            frame,
            text="Dán link video Douyin hoặc TikTok bất kỳ. Backend sẽ bóc tách metadata, tải video phân tích và quét tìm video tương đồng.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=850,
            justify="left"
        )
        sub_lbl.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        box = ctk.CTkFrame(frame)
        box.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(box, text="Link Video:").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        self.txt_url_input = ctk.CTkEntry(box, placeholder_text="Dán link Douyin (https://v.douyin.com/... hoặc https://www.douyin.com/video/...)")
        self.txt_url_input.grid(row=0, column=1, padx=10, pady=12, sticky="ew")
        self.txt_url_input.insert(0, "https://www.douyin.com/video/7268899827364121901")

        self.btn_run_url_search = ctk.CTkButton(
            frame,
            text="🚀 Bắt Đầu Phân Tích Link & Quét Douyin",
            font=ctk.CTkFont(weight="bold"),
            height=40,
            command=self._on_start_url_search
        )
        self.btn_run_url_search.grid(row=3, column=0, padx=20, pady=15, sticky="ew")

        self.lbl_url_progress = ctk.CTkLabel(frame, text="Trạng thái: Sẵn sàng", text_color="gray70")
        self.lbl_url_progress.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="w")

        return frame

    def _on_start_url_search(self):
        url = self.txt_url_input.get().strip()
        if not url:
            messagebox.showwarning("Thông báo", "Vui lòng dán link Douyin hoặc TikTok.")
            return

        self.btn_run_url_search.configure(state="disabled", text="⏳ Đang phân tích link...")
        self.lbl_url_progress.configure(text="Đang kết nối Backend bóc tách URL...")

        def _worker():
            try:
                res = self.api_client.analyze_url(douyin_url=url)
                job_id = res.get("job_id")
                self.current_job_id = job_id
                self._poll_job_progress(job_id)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi URL", f"Không thể xử lý URL này:\n{e}"))
                self.after(0, lambda: self.btn_run_url_search.configure(state="normal", text="🚀 Bắt Đầu Phân Tích Link & Quét Douyin"))

        threading.Thread(target=_worker, daemon=True).start()

    def _poll_job_progress(self, job_id: str):
        def _poll_worker():
            while True:
                time.sleep(1.5)
                try:
                    job = self.api_client.get_job_status(job_id)
                    pct = job.get("progress_percent", 0)
                    stage = job.get("stage", "processing")
                    status = job.get("status", "in_progress")

                    status_str = f"Tiến độ: {pct}% ({stage})"
                    self.after(0, lambda: self.lbl_upload_progress.configure(text=status_str))
                    self.after(0, lambda: self.lbl_url_progress.configure(text=status_str))

                    if status == "completed":
                        # Fetch final ranked results
                        res_data = self.api_client.get_job_results(job_id)
                        self.raw_videos = res_data.get("results", [])
                        self.after(0, self._on_pipeline_completed)
                        break
                    elif status == "failed":
                        err_msg = job.get("error_message", "Lỗi không xác định")
                        self.after(0, lambda: messagebox.showerror("Pipeline Thất Bại", f"Quá trình xử lý bị lỗi:\n{err_msg}"))
                        self.after(0, self._reset_action_buttons)
                        break
                except Exception as e:
                    print(f"Polling error: {e}")
                    break

        threading.Thread(target=_poll_worker, daemon=True).start()

    def _on_pipeline_completed(self):
        self._reset_action_buttons()
        self._select_tab("results")
        self._apply_results_filters()

    def _reset_action_buttons(self):
        self.btn_upload_video.configure(state="normal", text="🚀 Bắt Đầu Upload & Phân Tích Video")
        self.btn_run_url_search.configure(state="normal", text="🚀 Bắt Đầu Phân Tích Link & Quét Douyin")

    # ================= TAB 4: RESULTS & FILTERS =================
    def _create_results_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Controls & Filters Bar
        filter_bar = ctk.CTkFrame(frame)
        filter_bar.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")

        ctk.CTkLabel(filter_bar, text="Độ tương đồng tối thiểu (%):").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.min_score_slider = ctk.CTkSlider(filter_bar, from_=50, to=95, number_of_steps=9, width=140)
        self.min_score_slider.set(60)
        self.min_score_slider.grid(row=0, column=1, padx=5, pady=8, sticky="w")

        ctk.CTkLabel(filter_bar, text="Min Likes:").grid(row=0, column=2, padx=(15, 5), pady=8, sticky="w")
        self.cb_min_likes = ctk.CTkComboBox(filter_bar, values=["0", "5000", "10000", "50000", "100000"], width=90)
        self.cb_min_likes.set("0")
        self.cb_min_likes.grid(row=0, column=3, padx=5, pady=8, sticky="w")

        ctk.CTkLabel(filter_bar, text="Sắp xếp:").grid(row=0, column=4, padx=(15, 5), pady=8, sticky="w")
        self.cb_sort_by = ctk.CTkComboBox(filter_bar, values=["Độ tương đồng (Score)", "Lượt thích (Likes)", "Bình luận (Comments)", "Mới nhất"], width=160)
        self.cb_sort_by.set("Độ tương đồng (Score)")
        self.cb_sort_by.grid(row=0, column=5, padx=5, pady=8, sticky="w")

        btn_filter = ctk.CTkButton(filter_bar, text="⚡ Lọc Lại", width=100, command=self._apply_results_filters)
        btn_filter.grid(row=0, column=6, padx=10, pady=8)

        # Table Results Area
        table_frame = ctk.CTkFrame(frame)
        table_frame.grid(row=2, column=0, padx=15, pady=(5, 15), sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("stt", "score", "tier", "title", "author", "likes", "comments", "kw_score", "sem_score", "vis_score")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")

        self.tree.heading("stt", text="#")
        self.tree.heading("score", text="Score")
        self.tree.heading("tier", text="Phân Loại")
        self.tree.heading("title", text="Tiêu đề Video Douyin")
        self.tree.heading("author", text="Tác giả")
        self.tree.heading("likes", text="Lượt Thích")
        self.tree.heading("comments", text="Bình Luận")
        self.tree.heading("kw_score", text="KW")
        self.tree.heading("sem_score", text="SEM")
        self.tree.heading("vis_score", text="VIS")

        self.tree.column("stt", width=35, anchor="center")
        self.tree.column("score", width=55, anchor="center")
        self.tree.column("tier", width=100, anchor="center")
        self.tree.column("title", width=380, anchor="w")
        self.tree.column("author", width=110, anchor="w")
        self.tree.column("likes", width=85, anchor="e")
        self.tree.column("comments", width=75, anchor="e")
        self.tree.column("kw_score", width=45, anchor="center")
        self.tree.column("sem_score", width=45, anchor="center")
        self.tree.column("vis_score", width=45, anchor="center")

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # Export Action Bar
        export_bar = ctk.CTkFrame(frame)
        export_bar.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")

        btn_copy = ctk.CTkButton(export_bar, text="📋 Sao Chép Tất Cả Link", command=self._on_copy_all_links, fg_color="#4A5568")
        btn_copy.pack(side="left", padx=10, pady=8)

        btn_excel = ctk.CTkButton(export_bar, text="📊 Xuất Excel (.xlsx)", command=self._on_export_excel, fg_color="#107C41", hover_color="#0B5C30")
        btn_excel.pack(side="right", padx=10, pady=8)

        return frame

    def _apply_results_filters(self):
        min_score = self.min_score_slider.get()
        min_likes = int(self.cb_min_likes.get().replace(",", "") or 0)
        sort_mode = self.cb_sort_by.get()

        res = []
        for r in self.raw_videos:
            score = r.get("final_score", r.get("score", 0))
            likes = r.get("likes", r.get("like_count", 0))

            if score < min_score:
                continue
            if likes < min_likes:
                continue
            res.append(r)

        if "Likes" in sort_mode:
            res.sort(key=lambda x: x.get("likes", x.get("like_count", 0)), reverse=True)
        elif "Bình luận" in sort_mode:
            res.sort(key=lambda x: x.get("comments", x.get("comment_count", 0)), reverse=True)
        else:
            res.sort(key=lambda x: x.get("final_score", x.get("score", 0)), reverse=True)

        self.filtered_videos = res

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, v in enumerate(self.filtered_videos, 1):
            score_val = v.get("final_score", v.get("score", 85))
            self.tree.insert("", "end", values=(
                i,
                f"{score_val}%",
                v.get("match_tier", "High"),
                v.get("title", ""),
                v.get("author", "Creator"),
                f"{v.get('likes', 0):,}",
                f"{v.get('comments', 0):,}",
                v.get("keyword_score", 80),
                v.get("semantic_score", 85),
                v.get("visual_score", 90)
            ))

        self.lbl_stats.configure(text=f"Kết quả hiện tại: {len(self.filtered_videos)}")

    def _on_tree_double_click(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        idx = int(self.tree.item(selected_item, "values")[0]) - 1
        if 0 <= idx < len(self.filtered_videos):
            vid = self.filtered_videos[idx]
            url = vid.get("url") or f"https://www.douyin.com/video/{vid.get('video_id')}"
            webbrowser.open(url)

    def _on_copy_all_links(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có danh sách video để sao chép.")
            return
        links = [v.get("url") or f"https://www.douyin.com/video/{v.get('video_id')}" for v in self.filtered_videos]
        self.clipboard_clear()
        self.clipboard_append("\n".join(links))
        messagebox.showinfo("Thành công", f"Đã sao chép {len(links)} link Douyin vào Clipboard!")

    def _on_export_excel(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có danh sách video để xuất.")
            return
        import pandas as pd
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], initialfile="douyin_ranked_results.xlsx")
        if filepath:
            df = pd.DataFrame(self.filtered_videos)
            df.to_excel(filepath, index=False)
            messagebox.showinfo("Thành công", f"Đã xuất file Excel:\n{filepath}")

    # ================= TAB 5: HISTORY =================
    def _create_history_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(frame, text="🕒 Lịch Sử Tìm Kiếm & Phân Tích (Từ Backend API)", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        btn_refresh = ctk.CTkButton(frame, text="🔄 Tải Lại Lịch Sử", command=self._load_history_from_backend, width=130)
        btn_refresh.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.history_tree = ttk.Treeview(frame, columns=("id", "name", "results", "time"), show="headings")
        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("name", text="Phiên Tìm Kiếm")
        self.history_tree.heading("results", text="Số Kết Quả")
        self.history_tree.heading("time", text="Thời Gian")

        self.history_tree.column("id", width=120, anchor="center")
        self.history_tree.column("name", width=380, anchor="w")
        self.history_tree.column("results", width=100, anchor="center")
        self.history_tree.column("time", width=150, anchor="center")

        self.history_tree.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="nsew")

        return frame

    def _load_history_from_backend(self):
        try:
            items = self.api_client.get_history()
            for row in self.history_tree.get_children():
                self.history_tree.delete(row)
            for it in items:
                self.history_tree.insert("", "end", values=(
                    it.get("id"),
                    it.get("filename"),
                    it.get("results_count", 0),
                    it.get("created_at", "")[:19]
                ))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lấy lịch sử từ Backend:\n{e}")

    # ================= TAB 6: SETTINGS =================
    def _create_settings_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(frame, text="⚙️ Cài Đặt Kết Nối Backend & Tùy Chọn", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        box = ctk.CTkFrame(frame)
        box.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(box, text="Backend API URL:").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        self.txt_backend_url = ctk.CTkEntry(box)
        self.txt_backend_url.insert(0, self.config.get("backend_url", "http://localhost:8000"))
        self.txt_backend_url.grid(row=0, column=1, padx=15, pady=12, sticky="ew")

        btn_test = ctk.CTkButton(box, text="Kiểm Tra Kết Nối", width=120, command=self._test_backend_connection)
        btn_test.grid(row=0, column=2, padx=15, pady=12)

        ctk.CTkLabel(box, text="Thư mục xuất file:").grid(row=1, column=0, padx=15, pady=12, sticky="w")
        self.txt_download_dir = ctk.CTkEntry(box)
        self.txt_download_dir.insert(0, self.config.get("download_folder", ""))
        self.txt_download_dir.grid(row=1, column=1, padx=15, pady=12, sticky="ew")

        btn_save = ctk.CTkButton(frame, text="💾 Lưu Cấu Hình PC Client", font=ctk.CTkFont(weight="bold"), height=40, command=self._on_save_pc_settings)
        btn_save.grid(row=2, column=0, padx=20, pady=20, sticky="e")

        return frame

    def _test_backend_connection(self):
        url = self.txt_backend_url.get().strip()
        self.api_client.set_base_url(url)
        if self.api_client.check_health():
            messagebox.showinfo("Thành công", f"Kết nối Backend API ({url}) thành công!")
            self.lbl_server_status.configure(text="🟢 Backend: Sẵn sàng", text_color="#48BB78")
        else:
            messagebox.showwarning("Cảnh báo", f"Không thể kết nối Backend tại {url}.\nVui lòng kiểm tra xem Backend server đã chạy chưa.")
            self.lbl_server_status.configure(text="🔴 Backend: Ngắt kết nối", text_color="#E53E3E")

    def _on_save_pc_settings(self):
        self.config["backend_url"] = self.txt_backend_url.get().strip()
        self.config["download_folder"] = self.txt_download_dir.get().strip()
        self._save_config()
        self.api_client.set_base_url(self.config["backend_url"])
        messagebox.showinfo("Thành công", "Đã lưu cấu hình PC client thành công!")


def main():
    app = DouyinExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()

