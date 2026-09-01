"""
GUI Module: Douyin Video Extractor & AI Filter Desktop Application
Built with CustomTkinter for a modern, responsive user experience.
"""

import os
import sys
import json
import webbrowser
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

from core.analyzer import DouyinAIAnalyzer, DOUYIN_TAXONOMY
from core.douyin_scanner import DouyinScanner
from core.filters import DouyinFilter
from core.exporter import DouyinExporter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


class DouyinExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Douyin Video Extractor & AI Filter - by khoathoiloi")
        self.geometry("1100x750")
        self.minsize(950, 650)

        # Application state
        self.raw_videos = []
        self.filtered_videos = []
        self.is_searching = False
        self.is_downloading = False

        # Load configuration
        self.config = self._load_config()

        # Initialize engines
        self.analyzer = DouyinAIAnalyzer(
            api_key=self.config.get("ai_api_key", ""),
            provider=self.config.get("ai_provider", "gemini")
        )
        self.scanner = DouyinScanner(cookie=self.config.get("douyin_cookie", ""))

        # Build UI layout
        self._build_ui()

    def _load_config(self) -> dict:
        default_config = {
            "ai_provider": "gemini",
            "ai_api_key": "",
            "douyin_cookie": "",
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
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="🎵 Douyin Extractor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.version_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="AI Link & Discovery Filter v1.2",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Navigation buttons
        self.nav_btn_ai = ctk.CTkButton(
            self.sidebar_frame, text="🧠 AI Link & Từ Khóa", command=lambda: self._select_tab("ai"),
            height=40, font=ctk.CTkFont(size=14)
        )
        self.nav_btn_ai.grid(row=2, column=0, padx=15, pady=8, sticky="ew")

        self.nav_btn_search = ctk.CTkButton(
            self.sidebar_frame, text="🔍 Tìm Kiếm & Lọc", command=lambda: self._select_tab("search"),
            height=40, font=ctk.CTkFont(size=14)
        )
        self.nav_btn_search.grid(row=3, column=0, padx=15, pady=8, sticky="ew")

        self.nav_btn_export = ctk.CTkButton(
            self.sidebar_frame, text="📥 Xuất & Tải Về", command=lambda: self._select_tab("export"),
            height=40, font=ctk.CTkFont(size=14)
        )
        self.nav_btn_export.grid(row=4, column=0, padx=15, pady=8, sticky="ew")

        self.nav_btn_settings = ctk.CTkButton(
            self.sidebar_frame, text="⚙️ Cài Đặt", command=lambda: self._select_tab("settings"),
            height=40, font=ctk.CTkFont(size=14)
        )
        self.nav_btn_settings.grid(row=5, column=0, padx=15, pady=8, sticky="ew")

        # Bottom stats
        self.status_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.status_box.grid(row=7, column=0, padx=15, pady=20, sticky="s")

        self.lbl_stats = ctk.CTkLabel(
            self.status_box,
            text="Video đã quét: 0",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.lbl_stats.pack(anchor="w")

        # Right Main Container
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.tab_frames = {
            "ai": self._create_ai_tab(),
            "search": self._create_search_tab(),
            "export": self._create_export_tab(),
            "settings": self._create_settings_tab()
        }

        self._select_tab("ai")

    def _select_tab(self, tab_name: str):
        for name, frame in self.tab_frames.items():
            if name == tab_name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        buttons = {
            "ai": self.nav_btn_ai,
            "search": self.nav_btn_search,
            "export": self.nav_btn_export,
            "settings": self.nav_btn_settings
        }
        for name, btn in buttons.items():
            if name == tab_name:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            else:
                btn.configure(fg_color="transparent")

    # ================= TAB 1: AI STUDIO =================
    def _create_ai_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(3, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            frame,
            text="🧠 Phân Tích Ý Tưởng & Sinh Từ Khóa Douyin (AI Studio)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        sub_lbl = ctk.CTkLabel(
            frame,
            text="Nhập mô tả ý tưởng, tóm tắt video mẫu hoặc chủ đề. AI sẽ tự động phân tích và sinh từ khóa tiếng Trung chuẩn SEO Douyin.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
            wraplength=800,
            justify="left"
        )
        sub_lbl.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # Input Area
        input_box = ctk.CTkFrame(frame)
        input_box.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        input_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_box, text="Dán Link Video / Mô tả:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.ai_input_text = ctk.CTkTextbox(input_box, height=75)
        self.ai_input_text.grid(row=0, column=1, columnspan=3, padx=10, pady=8, sticky="ew")
        self.ai_input_text.insert("0.0", "https://v.douyin.com/iR3qXYZ/ 7.89 复制打开抖音，看看【搞笑短剧】 (hoặc dán link video bất kỳ)")

        ctk.CTkLabel(input_box, text="Chủ đề gợi ý:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        niche_names = ["Tự động phát hiện"] + [v["name"] for v in DOUYIN_TAXONOMY.values()]
        self.niche_combo = ctk.CTkComboBox(input_box, values=niche_names, width=320)
        self.niche_combo.set("Tự động phát hiện")
        self.niche_combo.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.btn_run_ai = ctk.CTkButton(
            input_box,
            text="🚀 Bắt Đầu Phân Tích & Sinh Từ Khóa",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_run_ai_analysis,
            height=35
        )
        self.btn_run_ai.grid(row=1, column=2, padx=10, pady=10, sticky="e")

        # Result display
        result_box = ctk.CTkFrame(frame)
        result_box.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="nsew")
        result_box.grid_rowconfigure(1, weight=1)
        result_box.grid_columnconfigure(0, weight=1)

        result_header = ctk.CTkFrame(result_box, fg_color="transparent")
        result_header.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        result_header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(result_header, text="📋 Kết quả Từ Khóa Douyin:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        
        self.btn_use_keyword = ctk.CTkButton(
            result_header,
            text="➡️ Đưa Từ Khóa Sang Tìm Kiếm",
            command=self._on_transfer_keyword_to_search,
            fg_color="#2FA572",
            hover_color="#1E7A52",
            height=30
        )
        self.btn_use_keyword.grid(row=0, column=2, sticky="e")

        self.ai_output_text = ctk.CTkTextbox(result_box, font=ctk.CTkFont(family="Consolas", size=13))
        self.ai_output_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        return frame

    def _on_run_ai_analysis(self):
        user_text = self.ai_input_text.get("0.0", "end").strip()
        if not user_text:
            messagebox.showwarning("Thông báo", "Vui lòng nhập nội dung hoặc ý tưởng video.")
            return

        self.btn_run_ai.configure(state="disabled", text="⏳ Đang phân tích...")

        def _worker():
            selected_niche = self.niche_combo.get()
            niche_key = None
            for k, v in DOUYIN_TAXONOMY.items():
                if v["name"] == selected_niche:
                    niche_key = k
                    break

            res = self.analyzer.analyze_video_url(user_text, scanner_instance=self.scanner, niche_hint=niche_key)
            self.after(0, lambda: self._display_ai_result(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _display_ai_result(self, res: dict):
        self.btn_run_ai.configure(state="normal", text="🚀 Bắt Đầu Phân Tích & Sinh Từ Khóa")
        self.ai_output_text.delete("0.0", "end")

        if not res.get("success", False):
            self.ai_output_text.insert("0.0", f"❌ Lỗi: {res.get('error', 'Không xác định')}")
            return

        source = res.get("source", "Offline Engine")
        main_kw = res.get("main_query", "")
        keywords = res.get("keywords", [])
        hashtags = res.get("hashtags", [])
        meaning = res.get("vietnamese_meaning", {})

        parsed_vid = res.get("parsed_video", {})
        output_str = f"=== KẾT QUẢ PHÂN TÍCH TỪ KHÓA DOUYIN (Nguồn: {source}) ===\n\n"
        if parsed_vid and parsed_vid.get("success"):
            output_str += "🎬 THÔNG TIN VIDEO MẪU TỪ LINK:\n"
            output_str += f"   • Tiêu đề: {parsed_vid.get('title')}\n"
            output_str += f"   • Tác giả: {parsed_vid.get('author')}\n"
            output_str += f"   • Link gốc: {parsed_vid.get('original_link')}\n"
            if parsed_vid.get('video_url'):
                output_str += f"   • Link Video HD No-WM: {parsed_vid.get('video_url')}\n"
            output_str += "\n" 
        output_str += f"🔥 TỪ KHÓA CHÍNH (Main Query): {main_kw}\n"
        if meaning.get("main_query_vi"):
            output_str += f"   ➤ Ý nghĩa: {meaning.get('main_query_vi')}\n\n"

        output_str += f"📌 TỪ KHÓA PHỤ LIÊN QUAN:\n"
        for kw in keywords:
            output_str += f"   • {kw}\n"

        output_str += f"\n🏷️ HASHTAG XU HƯỚNG (#话题):\n"
        output_str += f"   {' '.join(hashtags)}\n\n"

        if meaning.get("strategy_vi"):
            output_str += f"💡 CHIẾN LƯỢC TÌM KIẾM:\n   {meaning.get('strategy_vi')}\n"

        self.ai_output_text.insert("0.0", output_str)
        self.last_generated_keyword = main_kw

    def _on_transfer_keyword_to_search(self):
        kw = getattr(self, "last_generated_keyword", "")
        if kw:
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, kw)
            self._select_tab("search")
        else:
            messagebox.showinfo("Thông báo", "Vui lòng phân tích từ khóa trước.")

    # ================= TAB 2: SEARCH & FILTER =================
    def _create_search_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Search Controls Bar
        ctrl_frame = ctk.CTkFrame(frame)
        ctrl_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        ctrl_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ctrl_frame, text="Từ khóa Douyin:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.search_entry = ctk.CTkEntry(ctrl_frame, placeholder_text="Nhập từ khóa tiếng Trung (ví dụ: 搞笑短剧, 治愈系, 美食教程)...", height=35)
        self.search_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.search_entry.insert(0, "搞笑短剧")

        self.btn_search = ctk.CTkButton(
            ctrl_frame,
            text="🔍 Bắt Đầu Quét",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_start_search,
            width=130,
            height=35
        )
        self.btn_search.grid(row=0, column=2, padx=10, pady=10)

        # Filter Options Accordion/Frame
        filter_frame = ctk.CTkFrame(frame)
        filter_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        # Row 1 of filters
        ctk.CTkLabel(filter_frame, text="Số lượng quét:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.count_combo = ctk.CTkComboBox(filter_frame, values=["10", "20", "50", "100"], width=80)
        self.count_combo.set("20")
        self.count_combo.grid(row=0, column=1, padx=5, pady=8, sticky="w")

        ctk.CTkLabel(filter_frame, text="Lượt Thích (Likes) tối thiểu:").grid(row=0, column=2, padx=(15, 5), pady=8, sticky="w")
        self.min_likes_combo = ctk.CTkComboBox(filter_frame, values=["0", "5,000", "10,000", "50,000", "100,000", "500,000"], width=110)
        self.min_likes_combo.set("10,000")
        self.min_likes_combo.grid(row=0, column=3, padx=5, pady=8, sticky="w")

        ctk.CTkLabel(filter_frame, text="Thời gian đăng:").grid(row=0, column=4, padx=(15, 5), pady=8, sticky="w")
        self.date_range_combo = ctk.CTkComboBox(filter_frame, values=["Tất cả thời gian", "24 giờ qua", "7 ngày qua", "30 ngày qua"], width=140)
        self.date_range_combo.set("Tất cả thời gian")
        self.date_range_combo.grid(row=0, column=5, padx=5, pady=8, sticky="w")

        # Row 2 of filters
        ctk.CTkLabel(filter_frame, text="Thời lượng:").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.duration_combo = ctk.CTkComboBox(filter_frame, values=["Tất cả", "Ngắn (< 1 phút)", "Vừa (1-3 phút)", "Dài (> 3 phút)"], width=130)
        self.duration_combo.set("Tất cả")
        self.duration_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=8, sticky="w")

        ctk.CTkLabel(filter_frame, text="Sắp xếp:").grid(row=1, column=3, padx=(15, 5), pady=8, sticky="w")
        self.sort_combo = ctk.CTkComboBox(filter_frame, values=["Nhiều Likes nhất", "Nhiều Bình luận nhất", "Mới nhất"], width=150)
        self.sort_combo.set("Nhiều Likes nhất")
        self.sort_combo.grid(row=1, column=4, padx=5, pady=8, sticky="w")

        self.btn_apply_filter = ctk.CTkButton(
            filter_frame,
            text="⚡ Lọc Lại Kết Quả",
            command=self._apply_current_filters,
            width=130,
            fg_color="#4A5568"
        )
        self.btn_apply_filter.grid(row=1, column=5, padx=10, pady=8)

        # Table Results Area
        table_frame = ctk.CTkFrame(frame)
        table_frame.grid(row=2, column=0, padx=15, pady=(10, 15), sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("stt", "id", "title", "author", "likes", "comments", "duration", "create_time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("stt", text="#")
        self.tree.heading("id", text="ID Video")
        self.tree.heading("title", text="Tiêu đề Video")
        self.tree.heading("author", text="Tác giả")
        self.tree.heading("likes", text="Lượt Thích")
        self.tree.heading("comments", text="Bình Luận")
        self.tree.heading("duration", text="Thời Lượng")
        self.tree.heading("create_time", text="Ngày Đăng")

        self.tree.column("stt", width=40, anchor="center")
        self.tree.column("id", width=140, anchor="center")
        self.tree.column("title", width=380, anchor="w")
        self.tree.column("author", width=120, anchor="w")
        self.tree.column("likes", width=100, anchor="e")
        self.tree.column("comments", width=90, anchor="e")
        self.tree.column("duration", width=80, anchor="center")
        self.tree.column("create_time", width=120, anchor="center")

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-1>", self._on_tree_double_click)

        return frame

    def _on_start_search(self):
        kw = self.search_entry.get().strip()
        if not kw:
            messagebox.showwarning("Thông báo", "Vui lòng nhập từ khóa tìm kiếm Douyin.")
            return

        count = int(self.count_combo.get())
        self.btn_search.configure(state="disabled", text="⏳ Đang quét...")

        def _worker():
            results = self.scanner.search_videos(keyword=kw, count=count)
            self.raw_videos = results
            self.after(0, self._apply_current_filters)

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_current_filters(self):
        self.btn_search.configure(state="normal", text="🔍 Bắt Đầu Quét")
        
        likes_str = self.min_likes_combo.get().replace(",", "").replace(".", "").strip()
        min_likes = int(likes_str) if likes_str.isdigit() else 0

        date_map = {
            "Tất cả thời gian": "all",
            "24 giờ qua": "24h",
            "7 ngày qua": "7d",
            "30 ngày qua": "30d"
        }
        date_range = date_map.get(self.date_range_combo.get(), "all")

        dur_map = {
            "Tất cả": "all",
            "Ngắn (< 1 phút)": "short",
            "Vừa (1-3 phút)": "medium",
            "Dài (> 3 phút)": "long"
        }
        dur_type = dur_map.get(self.duration_combo.get(), "all")

        sort_map = {
            "Nhiều Likes nhất": "likes_desc",
            "Nhiều Bình luận nhất": "comments_desc",
            "Mới nhất": "newest"
        }
        sort_by = sort_map.get(self.sort_combo.get(), "likes_desc")

        self.filtered_videos = DouyinFilter.apply_filters(
            videos=self.raw_videos,
            min_likes=min_likes,
            date_range=date_range,
            duration_type=dur_type,
            sort_by=sort_by
        )

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, v in enumerate(self.filtered_videos, 1):
            dur_formatted = f"{v.get('duration', 0)}s"
            self.tree.insert("", "end", values=(
                i,
                v.get("aweme_id", ""),
                v.get("title", ""),
                v.get("author_name", ""),
                f"{v.get('digg_count', 0):,}",
                f"{v.get('comment_count', 0):,}",
                dur_formatted,
                v.get("create_time", "")
            ))

        self.lbl_stats.configure(text=f"Video đã quét: {len(self.raw_videos)} | Thỏa bộ lọc: {len(self.filtered_videos)}")
        if hasattr(self, "lbl_export_count"):
            self.lbl_export_count.configure(text=f"Số lượng video sẵn sàng xuất: {len(self.filtered_videos)}")

    def _on_tree_double_click(self, event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        vals = self.tree.item(selected_item, "values")
        if vals:
            video_id = vals[1]
            webbrowser.open(f"https://www.douyin.com/video/{video_id}")

    # ================= TAB 3: EXPORT & DOWNLOAD =================
    def _create_export_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(frame, text="📥 Trích Xuất Dữ Liệu & Tải Video Hàng Loạt", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.lbl_export_count = ctk.CTkLabel(
            frame,
            text="Số lượng video sẵn sàng xuất: 0",
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        self.lbl_export_count.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        btn_box = ctk.CTkFrame(frame)
        btn_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        btn_box.grid_columnconfigure((0, 1), weight=1)

        # Left export box
        left_box = ctk.CTkFrame(btn_box)
        left_box.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(left_box, text="📊 Xuất Báo Cáo & Danh Sách", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=15, pady=(15, 10), anchor="w")

        btn_excel = ctk.CTkButton(
            left_box,
            text="📊 Xuất File Excel (.xlsx)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#107C41",
            hover_color="#0B5C30",
            height=40,
            command=self._on_export_excel
        )
        btn_excel.pack(padx=15, pady=8, fill="x")

        btn_csv = ctk.CTkButton(
            left_box,
            text="📄 Xuất File CSV (.csv)",
            font=ctk.CTkFont(size=13),
            fg_color="#2D3748",
            height=40,
            command=self._on_export_csv
        )
        btn_csv.pack(padx=15, pady=8, fill="x")

        btn_txt = ctk.CTkButton(
            left_box,
            text="📝 Xuất Danh Sách Link (.txt)",
            font=ctk.CTkFont(size=13),
            fg_color="#2D3748",
            height=40,
            command=self._on_export_txt
        )
        btn_txt.pack(padx=15, pady=8, fill="x")

        btn_copy = ctk.CTkButton(
            left_box,
            text="📋 Sao Chép Tất Cả Link Không Logo",
            font=ctk.CTkFont(size=13),
            fg_color="#4A5568",
            height=40,
            command=self._on_copy_all_links
        )
        btn_copy.pack(padx=15, pady=8, fill="x")

        # Right download box
        right_box = ctk.CTkFrame(btn_box)
        right_box.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(right_box, text="⬇️ Tải Video Trực Tiếp Về Máy", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=15, pady=(15, 10), anchor="w")

        self.btn_download_batch = ctk.CTkButton(
            right_box,
            text="⬇️ Bắt Đầu Tải Hàng Loạt Video (HD No-WM)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#E53E3E",
            hover_color="#C53030",
            height=45,
            command=self._on_start_batch_download
        )
        self.btn_download_batch.pack(padx=15, pady=(15, 10), fill="x")

        self.download_progress = ctk.CTkProgressBar(right_box)
        self.download_progress.pack(padx=15, pady=10, fill="x")
        self.download_progress.set(0)

        self.lbl_download_status = ctk.CTkLabel(right_box, text="Trạng thái: Sẵn sàng", text_color="gray70")
        self.lbl_download_status.pack(padx=15, pady=5, anchor="w")

        return frame

    def _on_export_excel(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để xuất.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], initialfile="douyin_videos.xlsx")
        if filepath:
            DouyinExporter.export_to_excel(self.filtered_videos, filepath)
            messagebox.showinfo("Thành công", f"Đã xuất {len(self.filtered_videos)} video ra file Excel:\n{filepath}")

    def _on_export_csv(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để xuất.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], initialfile="douyin_videos.csv")
        if filepath:
            DouyinExporter.export_to_csv(self.filtered_videos, filepath)
            messagebox.showinfo("Thành công", f"Đã xuất file CSV:\n{filepath}")

    def _on_export_txt(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để xuất.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")], initialfile="douyin_links.txt")
        if filepath:
            DouyinExporter.export_to_txt(self.filtered_videos, filepath, only_links=True)
            messagebox.showinfo("Thành công", f"Đã xuất danh sách link ra file:\n{filepath}")

    def _on_copy_all_links(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có dữ liệu video để sao chép.")
            return
        links = [v.get("web_url") or f"https://www.douyin.com/video/{v.get('aweme_id')}" for v in self.filtered_videos]
        self.clipboard_clear()
        self.clipboard_append("\n".join(links))
        messagebox.showinfo("Thành công", f"Đã sao chép {len(links)} link xem video Douyin (mở được ngay trên trình duyệt) vào Clipboard!")

    def _on_start_batch_download(self):
        if not self.filtered_videos:
            messagebox.showwarning("Thông báo", "Chưa có danh sách video để tải.")
            return

        download_dir = self.config.get("download_folder", "")
        if not download_dir or not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)

        self.btn_download_batch.configure(state="disabled", text="⏳ Đang tải video...")
        total = len(self.filtered_videos)
        self.download_progress.set(0)

        def _progress(completed, total_count, res):
            prog = completed / total_count
            self.download_progress.set(prog)
            self.lbl_download_status.configure(text=f"Đang tải: {completed}/{total_count} video ({int(prog*100)}%)")

        def _worker():
            cookie = self.config.get("douyin_cookie", "")
            results = DouyinExporter.batch_download(self.filtered_videos, download_dir, cookie=cookie, progress_callback=_progress)
            success_count = sum(1 for r in results if r.get("success"))
            self.after(0, lambda: self._on_download_complete(success_count, len(results)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_download_complete(self, success_count, total_count):
        self.btn_download_batch.configure(state="normal", text="⬇️ Bắt Đầu Tải Hàng Loạt Video (HD No-WM)")
        if success_count > 0:
            self.lbl_download_status.configure(text=f"✅ Đã tải thành công {success_count}/{total_count} video!")
            messagebox.showinfo("Hoàn tất", f"Đã tải thành công {success_count}/{total_count} video về thư mục:\n{self.config.get('download_folder')}")
        else:
            self.lbl_download_status.configure(text="⚠️ Cần Cookie Douyin để tải trực tiếp file về máy")
            messagebox.showinfo(
                "Thông báo tải video",
                "Máy chủ Douyin yêu cầu Cookie trình duyệt để tải trực tiếp file .mp4 về máy.\n\n"
                "👉 Giải pháp:\n"
                "1. Bạn có thể bấm '📊 Xuất File Excel' hoặc '📋 Sao Chép Link' để click mở xem trực tiếp trên trình duyệt (Cốc Cốc/Chrome) ngay lập tức.\n"
                "2. Hoặc vào tab '⚙️ Cài Đặt' dán Cookie tài khoản Douyin để mở khóa tải tự động 100%!"
            )

    # ================= TAB 4: SETTINGS =================
    def _create_settings_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="⚙️ Cài Đặt Hệ Thống & Cấu Hình API", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        box = ctk.CTkFrame(frame)
        box.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(box, text="Dịch vụ AI:").grid(row=0, column=0, padx=15, pady=12, sticky="w")
        self.set_ai_provider = ctk.CTkComboBox(box, values=["gemini", "openai"])
        self.set_ai_provider.set(self.config.get("ai_provider", "gemini"))
        self.set_ai_provider.grid(row=0, column=1, padx=15, pady=12, sticky="w")

        ctk.CTkLabel(box, text="AI API Key:").grid(row=1, column=0, padx=15, pady=12, sticky="w")
        self.set_api_key = ctk.CTkEntry(box, placeholder_text="Nhập Google Gemini API Key hoặc OpenAI Key...")
        self.set_api_key.insert(0, self.config.get("ai_api_key", ""))
        self.set_api_key.grid(row=1, column=1, padx=15, pady=12, sticky="ew")

        ctk.CTkLabel(box, text="Douyin Cookie:").grid(row=2, column=0, padx=15, pady=12, sticky="w")
        self.set_cookie = ctk.CTkEntry(box, placeholder_text="Dán Cookie từ Douyin.com để tăng tốc và mở khóa 100% video...")
        self.set_cookie.insert(0, self.config.get("douyin_cookie", ""))
        self.set_cookie.grid(row=2, column=1, padx=15, pady=12, sticky="ew")

        ctk.CTkLabel(box, text="Thư mục lưu video:").grid(row=3, column=0, padx=15, pady=12, sticky="w")
        dir_frame = ctk.CTkFrame(box, fg_color="transparent")
        dir_frame.grid(row=3, column=1, padx=15, pady=12, sticky="ew")
        dir_frame.grid_columnconfigure(0, weight=1)

        self.set_download_dir = ctk.CTkEntry(dir_frame)
        self.set_download_dir.insert(0, self.config.get("download_folder", ""))
        self.set_download_dir.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        btn_browse = ctk.CTkButton(dir_frame, text="📁 Chọn...", width=80, command=self._on_browse_folder)
        btn_browse.grid(row=0, column=1)

        btn_save = ctk.CTkButton(
            frame,
            text="💾 Lưu Cấu Hình",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._on_save_settings
        )
        btn_save.grid(row=2, column=0, padx=20, pady=20, sticky="e")

        return frame

    def _on_browse_folder(self):
        f = filedialog.askdirectory(initialdir=self.config.get("download_folder"))
        if f:
            self.set_download_dir.delete(0, "end")
            self.set_download_dir.insert(0, f)

    def _on_save_settings(self):
        self.config["ai_provider"] = self.set_ai_provider.get()
        self.config["ai_api_key"] = self.set_api_key.get().strip()
        self.config["douyin_cookie"] = self.set_cookie.get().strip()
        self.config["download_folder"] = self.set_download_dir.get().strip()
        self._save_config()

        self.analyzer.set_api_key(self.config["ai_api_key"], self.config["ai_provider"])
        self.scanner.update_cookie(self.config["douyin_cookie"])

        messagebox.showinfo("Thành công", "Đã lưu cấu hình thành công!")


def main():
    app = DouyinExtractorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
