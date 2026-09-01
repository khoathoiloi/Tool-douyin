class DouyinApp {
    constructor() {
        this.currentVideoId = null;
        this.currentJobId = null;
        this.selectedFile = null;
        this.pollInterval = null;
        this.rawResults = [];
        this.filteredResults = [];
        this.currentPreviewData = null;
        this.searchHistory = [];

        this.initElements();
        this.initEvents();
    }

    initElements() {
        // Tabs
        this.inputTabs = document.querySelectorAll(".input-tab");
        this.tabContents = {
            "smartSearch": document.getElementById("tabSmartSearch"),
            "upload": document.getElementById("tabUpload"),
            "url": document.getElementById("tabUrl")
        };

        // Smart Search Elements
        this.smartSearchInput = document.getElementById("smartSearchInput");
        this.btnExecuteSmartSearch = document.getElementById("btnExecuteSmartSearch");
        this.btnTranslatePreview = document.getElementById("btnTranslatePreview");
        this.translationPreviewPanel = document.getElementById("translationPreviewPanel");
        this.previewLangBadge = document.getElementById("previewLangBadge");
        this.previewOriginalText = document.getElementById("previewOriginalText");
        this.previewIntentText = document.getElementById("previewIntentText");
        this.previewKeywordCategories = document.getElementById("previewKeywordCategories");
        this.queriesChecklist = document.getElementById("queriesChecklist");
        this.txtCustomQuery = document.getElementById("txtCustomQuery");
        this.btnAddCustomQuery = document.getElementById("btnAddCustomQuery");
        this.btnSearchFromPreview = document.getElementById("btnSearchFromPreview");

        // Upload & URL Inputs
        this.dropzone = document.getElementById("dropzone");
        this.fileInput = document.getElementById("videoFileInput");
        this.uploadDetails = document.getElementById("uploadDetails");
        this.videoPreview = document.getElementById("videoPreview");
        this.videoFileName = document.getElementById("videoFileName");
        this.videoFileSize = document.getElementById("videoFileSize");
        this.btnStartUploadPipeline = document.getElementById("btnStartUploadPipeline");

        this.douyinUrlInput = document.getElementById("douyinUrlInput");
        this.btnAnalyzeUrl = document.getElementById("btnAnalyzeUrl");

        // Progress
        this.progressBox = document.getElementById("progressBox");
        this.progressBarFill = document.getElementById("progressBarFill");
        this.progressStageText = document.getElementById("progressStageText");
        this.progressPercentText = document.getElementById("progressPercentText");
        this.progressSubText = document.getElementById("progressSubText");

        // Profile & Queries & Results
        this.profileGrid = document.getElementById("profileGrid");
        this.queriesGrid = document.getElementById("queriesGrid");
        this.resultsGrid = document.getElementById("resultsGrid");
        this.resultsCountText = document.getElementById("resultsCountText");

        // Filters
        this.rngMinScore = document.getElementById("rngMinScore");
        this.lblMinScore = document.getElementById("lblMinScore");
        this.selSortBy = document.getElementById("selSortBy");
        this.numMinLikes = document.getElementById("numMinLikes");
        this.btnApplyFilters = document.getElementById("btnApplyFilters");

        // History Drawer & Settings Modal
        this.historyDrawer = document.getElementById("historyDrawer");
        this.btnOpenHistory = document.getElementById("btnOpenHistory");
        this.btnCloseHistory = document.getElementById("btnCloseHistory");
        this.historyList = document.getElementById("historyList");

        this.settingsModal = document.getElementById("settingsModal");
        this.btnSettings = document.getElementById("btnSettings");
        this.btnCloseModal = document.getElementById("btnCloseModal");
        this.btnSaveConfig = document.getElementById("btnSaveConfig");
    }

    initEvents() {
        // Tab switching
        this.inputTabs.forEach(tab => {
            tab.addEventListener("click", () => {
                const targetTab = tab.dataset.tab;
                this.inputTabs.forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                Object.keys(this.tabContents).forEach(k => {
                    if (this.tabContents[k]) {
                        this.tabContents[k].style.display = (k === targetTab) ? "block" : "none";
                    }
                });
            });
        });

        // Smart Search Actions
        this.btnExecuteSmartSearch.addEventListener("click", () => this.handleSmartSearchClick());
        this.btnTranslatePreview.addEventListener("click", () => this.handleTranslatePreviewClick());
        this.btnAddCustomQuery.addEventListener("click", () => this.addCustomQuery());
        this.btnSearchFromPreview.addEventListener("click", () => this.executeSearchWithSelectedQueries());
        this.smartSearchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") this.handleSmartSearchClick();
        });

        // Dropzone & File Upload
        if (this.dropzone) {
            this.dropzone.addEventListener("dragover", (e) => { e.preventDefault(); this.dropzone.classList.add("dragover"); });
            this.dropzone.addEventListener("dragleave", () => this.dropzone.classList.remove("dragover"));
            this.dropzone.addEventListener("drop", (e) => {
                e.preventDefault();
                this.dropzone.classList.remove("dragover");
                if (e.dataTransfer.files.length > 0) this.handleFileSelected(e.dataTransfer.files[0]);
            });
        }
        if (this.fileInput) {
            this.fileInput.addEventListener("change", (e) => {
                if (e.target.files.length > 0) this.handleFileSelected(e.target.files[0]);
            });
        }

        // Upload & URL Buttons
        if (this.btnStartUploadPipeline) this.btnStartUploadPipeline.addEventListener("click", () => this.startUploadPipeline());
        if (this.btnAnalyzeUrl) this.btnAnalyzeUrl.addEventListener("click", () => this.startUrlPipeline());

        // Stepper
        document.querySelectorAll(".step-item").forEach(item => {
            item.addEventListener("click", () => this.goToStep(parseInt(item.dataset.step)));
        });

        // Filters
        if (this.rngMinScore) {
            this.rngMinScore.addEventListener("input", (e) => {
                this.lblMinScore.innerText = `${e.target.value}%`;
                this.applyLocalFilters();
            });
        }
        if (this.selSortBy) this.selSortBy.addEventListener("change", () => this.applyLocalFilters());
        if (this.btnApplyFilters) this.btnApplyFilters.addEventListener("click", () => this.applyLocalFilters());

        // Export & Copy
        document.getElementById("btnExportCSV").addEventListener("click", () => this.exportCSV());
        document.getElementById("btnExportJSON").addEventListener("click", () => this.exportJSON());
        document.getElementById("btnCopyAll").addEventListener("click", () => this.copyAllUrls());

        // History Drawer
        this.btnOpenHistory.addEventListener("click", () => {
            this.historyDrawer.classList.add("open");
            this.loadHistory();
        });
        this.btnCloseHistory.addEventListener("click", () => this.historyDrawer.classList.remove("open"));

        // Settings Modal
        this.btnSettings.addEventListener("click", () => this.settingsModal.classList.add("open"));
        this.btnCloseModal.addEventListener("click", () => this.settingsModal.classList.remove("open"));
        this.btnSaveConfig.addEventListener("click", () => this.saveConfig());
    }

    getSelectedLanguage() {
        const checked = document.querySelector('input[name="searchLang"]:checked');
        return checked ? checked.value : "auto";
    }

    getSelectedDepth() {
        const checked = document.querySelector('input[name="searchDepth"]:checked');
        return checked ? checked.value : "normal";
    }

    getSelectedFlow() {
        const checked = document.querySelector('input[name="searchFlow"]:checked');
        return checked ? checked.value : "auto";
    }

    async handleSmartSearchClick() {
        const flow = this.getSelectedFlow();
        if (flow === "manual") {
            await this.handleTranslatePreviewClick();
        } else {
            await this.executeFullSmartSearch();
        }
    }

    async handleTranslatePreviewClick() {
        const q = this.smartSearchInput.value.trim();
        if (!q) return alert("Vui lòng nhập từ khóa tìm kiếm.");

        this.btnTranslatePreview.disabled = true;
        this.showProgress("AI đang phân tích ý định và sinh từ khóa tiếng Trung...", 40);

        try {
            const resp = await fetch("/api/v1/query/translate", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    query: q,
                    language: this.getSelectedLanguage(),
                    mode: this.getSelectedDepth()
                })
            });

            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || "Lỗi phân tích");

            this.currentPreviewData = data;
            this.renderPreviewPanel(data);
            this.translationPreviewPanel.style.display = "block";
            this.progressBox.style.display = "none";
            this.btnTranslatePreview.disabled = false;
        } catch (err) {
            alert("Lỗi: " + err.message);
            this.progressBox.style.display = "none";
            this.btnTranslatePreview.disabled = false;
        }
    }

    renderPreviewPanel(data) {
        this.previewOriginalText.innerText = data.original_query || this.smartSearchInput.value;
        this.previewLangBadge.innerText = (data.detected_language === "vi") ? "🇻🇳 Tiếng Việt" : (data.detected_language === "zh" ? "🇨🇳 Tiếng Trung" : "🇬🇧 English");
        this.previewIntentText.innerText = data.intent || "VISUAL_CONTENT_SEARCH";

        // Render Keyword Categories
        const cats = data.chinese_keywords || {};
        let catHtml = "";
        const catLabels = {
            "primary": "Chủ thể / Đối tượng",
            "clothing": "Trang phục",
            "action": "Hành động",
            "scene": "Bối cảnh / Không gian",
            "style": "Phong cách / Tone"
        };

        Object.keys(catLabels).forEach(key => {
            const list = cats[key] || [];
            if (list.length > 0) {
                catHtml += `
                    <div class="cat-chip-row">
                        <span class="cat-label">${catLabels[key]}:</span>
                        <div class="chip-list">
                            ${list.map(w => `<span class="chip-pill ${key==='primary'?'primary':''}">${w}</span>`).join("")}
                        </div>
                    </div>
                `;
            }
        });
        this.previewKeywordCategories.innerHTML = catHtml || `<p class="text-muted">Không có nhóm từ khóa phụ trợ.</p>`;

        // Render Queries Checklist
        const queryScores = data.query_scores || [];
        this.queriesChecklist.innerHTML = queryScores.map((item, idx) => {
            let tierClass = "score-high";
            if (item.tier === "exact") tierClass = "score-exact";
            else if (item.tier === "medium") tierClass = "score-med";
            else if (item.tier === "broad") tierClass = "score-broad";

            return `
                <div class="query-check-item">
                    <label>
                        <input type="checkbox" class="chk-query-item" value="${item.query}" checked>
                        <span>${item.query}</span>
                    </label>
                    <span class="query-score-tag ${tierClass}">${item.score}đ (${item.tier.toUpperCase()})</span>
                </div>
            `;
        }).join("");
    }

    addCustomQuery() {
        const val = this.txtCustomQuery.value.trim();
        if (!val) return;
        const itemHtml = `
            <div class="query-check-item">
                <label>
                    <input type="checkbox" class="chk-query-item" value="${val}" checked>
                    <span>${val} (Tự thêm)</span>
                </label>
                <span class="query-score-tag score-high">100đ (CUSTOM)</span>
            </div>
        `;
        this.queriesChecklist.insertAdjacentHTML("afterbegin", itemHtml);
        this.txtCustomQuery.value = "";
    }

    async executeSearchWithSelectedQueries() {
        const q = this.smartSearchInput.value.trim();
        const selectedQueries = Array.from(document.querySelectorAll(".chk-query-item:checked")).map(c => c.value);
        if (!selectedQueries.length) return alert("Vui lòng chọn ít nhất một từ khóa tiếng Trung để quét.");

        await this.executeFullSmartSearch(selectedQueries);
    }

    async executeFullSmartSearch(customQueries = null) {
        const q = this.smartSearchInput.value.trim();
        if (!q) return alert("Vui lòng nhập từ khóa tìm kiếm.");

        this.btnExecuteSmartSearch.disabled = true;
        this.showProgress(`Đang chuyển ngữ & quét đa tầng trên Douyin...`, 45);

        try {
            const resp = await fetch("/api/v1/search/smart", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    query: q,
                    language: this.getSelectedLanguage(),
                    mode: this.getSelectedDepth(),
                    custom_queries: customQueries,
                    min_likes: parseInt(this.numMinLikes ? this.numMinLikes.value : 0) || 0
                })
            });

            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || "Lỗi tìm kiếm");

            this.currentVideoId = data.video_id;
            this.rawResults = data.results || [];
            
            // Save search history entry
            this.searchHistory.unshift({
                query: q,
                lang: data.language,
                queries_count: (data.queries || []).length,
                results_count: this.rawResults.length,
                time: new Date().toLocaleTimeString()
            });

            // Update queries step 3 view
            if (data.preview && data.preview.query_scores) {
                this.renderQueries(data.preview.query_scores.map(s => ({
                    query: s.query,
                    category: s.tier.toUpperCase(),
                    score: s.score / 100,
                    reason: s.reason || "Phân tầng độ liên quan"
                })));
            }

            this.applyLocalFilters();
            this.goToStep(4);
            this.progressBox.style.display = "none";
            this.btnExecuteSmartSearch.disabled = false;
        } catch (err) {
            alert("Lỗi: " + err.message);
            this.progressBox.style.display = "none";
            this.btnExecuteSmartSearch.disabled = false;
        }
    }

    handleFileSelected(file) {
        this.selectedFile = file;
        this.videoFileName.innerText = file.name;
        this.videoFileSize.innerText = (file.size / (1024 * 1024)).toFixed(2) + " MB";
        this.videoPreview.src = URL.createObjectURL(file);
        this.uploadDetails.style.display = "grid";
        this.dropzone.style.display = "none";
    }

    goToStep(stepNumber) {
        document.querySelectorAll(".step-item").forEach(item => {
            item.classList.toggle("active", parseInt(item.dataset.step) === stepNumber);
        });
        document.querySelectorAll(".step-section").forEach(sec => sec.classList.remove("active"));
        const sec = document.getElementById(`step${stepNumber}Section`);
        if (sec) sec.classList.add("active");
    }

    async startUploadPipeline() {
        if (!this.selectedFile) return;
        this.btnStartUploadPipeline.disabled = true;
        this.showProgress("Đang tải video lên máy chủ...", 5);

        const isDeep = document.getElementById("chkDeepSearchUpload")?.checked;
        const formData = new FormData();
        formData.append("file", this.selectedFile);
        formData.append("user_hint", document.getElementById("userHintInput").value.trim());
        formData.append("deep_search", isDeep ? "true" : "false");

        try {
            const resp = await fetch("/api/input/upload", { method: "POST", body: formData });
            const data = await resp.json();
            if (!data.success) throw new Error(data.detail || "Upload failed");

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;
            this.startJobPolling();
        } catch (err) {
            alert("Lỗi: " + err.message);
            this.btnStartUploadPipeline.disabled = false;
        }
    }

    async startUrlPipeline() {
        const url = this.douyinUrlInput.value.trim();
        if (!url) return alert("Vui lòng dán link Douyin hoặc TikTok.");

        this.btnAnalyzeUrl.disabled = true;
        this.showProgress("Đang phân tích link Douyin/TikTok...", 10);

        try {
            const resp = await fetch("/api/input/url", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ url: url })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.detail || "Parse link failed");

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;
            this.startJobPolling();
        } catch (err) {
            alert("Lỗi: " + err.message);
            this.btnAnalyzeUrl.disabled = false;
        }
    }

    showProgress(stageText, percent) {
        this.progressBox.style.display = "block";
        this.progressStageText.innerText = stageText;
        this.progressPercentText.innerText = percent + "%";
        this.progressBarFill.style.width = percent + "%";
    }

    startJobPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);

        const stageDescriptions = {
            "queued": "Đang xếp hàng chờ xử lý...",
            "processing": "FFmpeg đang trích xuất khung hình và âm thanh...",
            "analyzing": "AI Multimodal đang phân tích bối cảnh, ASR & OCR...",
            "generating_queries": "Đang tạo bộ truy vấn tiếng Trung phân tầng...",
            "searching": "Đang quét trên Douyin...",
            "ranking": "Đang tính điểm tương đồng & lọc trùng lặp...",
            "completed": "Hoàn tất toàn bộ pipeline!",
            "failed": "Có lỗi xảy ra trong quá trình xử lý"
        };

        this.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/jobs/${this.currentJobId}`);
                const job = await resp.json();

                this.showProgress(stageDescriptions[job.stage] || job.stage, job.progress_percent);

                if (job.status === "completed") {
                    clearInterval(this.pollInterval);
                    await this.loadAllPipelineData();
                } else if (job.status === "failed") {
                    clearInterval(this.pollInterval);
                    alert("Pipeline thất bại: " + (job.error_message || "Không rõ nguyên nhân"));
                    if (this.btnStartUploadPipeline) this.btnStartUploadPipeline.disabled = false;
                    if (this.btnAnalyzeUrl) this.btnAnalyzeUrl.disabled = false;
                }
            } catch (e) {
                console.error("Polling error:", e);
            }
        }, 1500);
    }

    async loadAllPipelineData() {
        // Load Profile
        const respProf = await fetch(`/api/videos/${this.currentVideoId}/analysis`);
        if (respProf.ok) {
            const p = await respProf.json();
            this.renderProfile(p);
        }

        // Load Queries
        const respQ = await fetch(`/api/videos/${this.currentVideoId}/queries`);
        if (respQ.ok) {
            const qData = await respQ.json();
            this.renderQueries(qData.queries || []);
        }

        // Load Results
        const respRes = await fetch(`/api/videos/${this.currentVideoId}/results`);
        if (respRes.ok) {
            const rData = await respRes.json();
            this.rawResults = rData.results || [];
            this.applyLocalFilters();
        }

        this.goToStep(4);
    }

    renderProfile(p) {
        if (!this.profileGrid) return;
        this.profileGrid.innerHTML = `
            <div class="profile-card">
                <h3><i class="fa-solid fa-list-check"></i> Tóm Tắt & Chủ Đề</h3>
                <p><strong>Chủ đề:</strong> ${p.main_topic || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Tóm tắt:</strong> ${p.summary || "N/A"}</p>
                <div class="tag-list">
                    ${(p.secondary_topics || []).map(t => `<span class="tag">${t}</span>`).join("")}
                </div>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-person-walking"></i> Nhân Vật & Hành Động</h3>
                <p><strong>Đối tượng/Nhân vật:</strong> ${(p.people || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Hành động:</strong> ${(p.actions || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Bối cảnh:</strong> ${(p.locations || []).join(", ") || "N/A"}</p>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-camera"></i> Phong Cách & Cảm Xúc</h3>
                <p><strong>Phong cách hình ảnh:</strong> ${(p.visual_style || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Góc quay:</strong> ${(p.camera_style || []).join(", ") || "N/A"}</p>
                <p style="margin-top:8px;"><strong>Tone cảm xúc:</strong> ${(p.emotional_tone || []).join(", ") || "N/A"}</p>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-file-lines"></i> Phụ Đề & Chữ Trên Màn Hình</h3>
                <p><strong>Phụ đề (ASR):</strong> ${p.transcript || "Không có lời thoại"}</p>
                <p style="margin-top:8px;"><strong>Chữ OCR:</strong> ${(p.ocr_text || []).join(", ") || "Không phát hiện"}</p>
            </div>
        `;
    }

    renderQueries(queries) {
        if (!this.queriesGrid) return;
        this.queriesGrid.innerHTML = queries.map(q => `
            <div class="query-card">
                <div class="query-header">
                    <span class="query-category">${q.category}</span>
                    <span style="font-size:12px; color:#10b981;">Score: ${q.score}</span>
                </div>
                <div class="query-text">${q.query}</div>
                <div style="font-size:12px; color:#94a3b8;">${q.reason || ''}</div>
            </div>
        `).join("");
    }

    applyLocalFilters() {
        const minScore = parseFloat(this.rngMinScore ? this.rngMinScore.value : 70);
        const minLikes = parseInt(this.numMinLikes ? this.numMinLikes.value : 0) || 0;
        const sortBy = this.selSortBy ? this.selSortBy.value : "similarity";

        let list = [...this.rawResults].filter(r => {
            const score = r.score !== undefined ? r.score : ((r.final_score || 0.8) * 100);
            if (score < minScore) return false;
            if (minLikes > 0 && (r.like_count || 0) < minLikes) return false;
            return true;
        });

        // Sorting
        if (sortBy === "likes") list.sort((a, b) => (b.like_count || 0) - (a.like_count || 0));
        else if (sortBy === "comments") list.sort((a, b) => (b.comment_count || 0) - (a.comment_count || 0));
        else if (sortBy === "shares") list.sort((a, b) => (b.share_count || 0) - (a.share_count || 0));
        else if (sortBy === "newest") list.sort((a, b) => (b.publish_time || "").localeCompare(a.publish_time || ""));
        else list.sort((a, b) => (b.score || (b.final_score * 100) || 0) - (a.score || (a.final_score * 100) || 0));

        this.filteredResults = list;
        if (this.resultsCountText) {
            this.resultsCountText.innerText = `Tìm thấy ${list.length} video Douyin phù hợp (Lọc từ ${this.rawResults.length} candidates)`;
        }
        this.renderResults(list);
    }

    renderResults(results) {
        if (!this.resultsGrid) return;
        if (!results.length) {
            this.resultsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 40px; color:#94a3b8;">Không có video nào đạt tiêu chí lọc này. Hãy hạ thấp mức điểm tương đồng hoặc số like.</div>`;
            return;
        }

        this.resultsGrid.innerHTML = results.map(r => {
            const scorePct = r.score !== undefined ? r.score : Math.round((r.final_score || 0.8) * 100);
            let tierClass = "good";
            if (scorePct >= 90) tierClass = "vhigh";
            else if (scorePct >= 80) tierClass = "high";
            else if (scorePct < 60) tierClass = "low";

            return `
            <div class="result-card">
                <img src="${r.cover_url || 'https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg'}" class="result-cover" onerror="this.src='https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/demo.jpeg'">
                <div class="result-body">
                    <div class="result-title">${r.title}</div>
                    <div class="result-stats">
                        <span><i class="fa-solid fa-user"></i> ${r.author}</span>
                        <span><i class="fa-solid fa-heart" style="color:#ef4444;"></i> ${(r.like_count || 0).toLocaleString()}</span>
                    </div>
                    <div class="result-scores">
                        <span>Độ khớp: <strong class="score-badge ${tierClass}">${scorePct}%</strong></span>
                        <span>Từ khóa: ${r.search_query}</span>
                    </div>
                    <div style="display:flex; gap:8px; margin-top:auto;">
                        <a href="${r.url}" target="_blank" class="btn btn-primary result-btn">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Mở Douyin
                        </a>
                        <button class="btn btn-outline" onclick="navigator.clipboard.writeText('${r.url}'); alert('Đã sao chép link!');" title="Sao chép link">
                            <i class="fa-solid fa-copy"></i>
                        </button>
                    </div>
                </div>
            </div>
            `;
        }).join("");
    }

    exportCSV() {
        if (!this.filteredResults.length) return alert("Không có dữ liệu để xuất.");
        let csv = "Rank,Title,Author,Likes,Score,Search_Query,Douyin_URL\n";
        this.filteredResults.forEach((r, idx) => {
            const cleanTitle = (r.title || "").replace(/[\r\n,]/g, " ");
            const scoreVal = r.score !== undefined ? r.score : Math.round((r.final_score || 0.8) * 100);
            csv += `${idx + 1},${cleanTitle},${r.author},${r.like_count},${scoreVal}%,${r.search_query},${r.url}\n`;
        });
        this.downloadFile(csv, `douyin_results_${this.currentVideoId || 'export'}.csv`, "text/csv;charset=utf-8;");
    }

    exportJSON() {
        if (!this.filteredResults.length) return alert("Không có dữ liệu để xuất.");
        const jsonStr = JSON.stringify(this.filteredResults, null, 2);
        this.downloadFile(jsonStr, `douyin_results_${this.currentVideoId || 'export'}.json`, "application/json");
    }

    copyAllUrls() {
        if (!this.filteredResults.length) return alert("Không có link để sao chép.");
        const urls = this.filteredResults.map(r => r.url).join("\n");
        navigator.clipboard.writeText(urls);
        alert(`Đã sao chép ${this.filteredResults.length} link Douyin vào Clipboard!`);
    }

    downloadFile(content, fileName, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    async loadHistory() {
        if (!this.searchHistory.length) {
            this.historyList.innerHTML = `<p class="text-muted" style="text-align:center; padding:20px;">Chưa có lịch sử tìm kiếm nào.</p>`;
            return;
        }
        this.historyList.innerHTML = this.searchHistory.map((h, idx) => `
            <div style="background:#0f172a; padding:12px; border-radius:8px; margin-bottom:10px; border:1px solid #334155;">
                <div style="font-weight:bold; color:#38bdf8;">${idx+1}. "${h.query}"</div>
                <div style="font-size:12px; color:#94a3b8; margin-top:4px;">Ngôn ngữ: ${h.lang} • ${h.queries_count} queries • ${h.time}</div>
                <div style="font-size:12px; color:#10b981; margin-top:2px;">Kết quả: ${h.results_count} video Douyin</div>
            </div>
        `).join("");
    }

    saveConfig() {
        this.settingsModal.classList.remove("open");
        alert("Đã lưu cấu hình!");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.app = new DouyinApp();
});
