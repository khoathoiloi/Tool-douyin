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
        this.loadSettings();
    }

    initElements() {
        this.inputTabs = document.querySelectorAll('.input-tab');
        this.tabContents = {
            'smartSearch': document.getElementById('tabSmartSearch'),
            'upload': document.getElementById('tabUpload'),
            'url': document.getElementById('tabUrl')
        };

        this.smartSearchInput = document.getElementById('smartSearchInput');
        this.btnExecuteSmartSearch = document.getElementById('btnExecuteSmartSearch');
        this.btnTranslatePreview = document.getElementById('btnTranslatePreview');
        this.translationPreviewPanel = document.getElementById('translationPreviewPanel');
        this.previewLangBadge = document.getElementById('previewLangBadge');
        this.previewOriginalText = document.getElementById('previewOriginalText');
        this.previewIntentText = document.getElementById('previewIntentText');
        this.previewKeywordCategories = document.getElementById('previewKeywordCategories');
        this.queriesChecklist = document.getElementById('queriesChecklist');
        this.txtCustomQuery = document.getElementById('txtCustomQuery');
        this.btnAddCustomQuery = document.getElementById('btnAddCustomQuery');
        this.btnSearchFromPreview = document.getElementById('btnSearchFromPreview');

        this.dropzone = document.getElementById('dropzone');
        this.fileInput = document.getElementById('videoFileInput');
        this.uploadDetails = document.getElementById('uploadDetails');
        this.videoPreview = document.getElementById('videoPreview');
        this.videoFileName = document.getElementById('videoFileName');
        this.videoFileSize = document.getElementById('videoFileSize');
        this.btnStartUploadPipeline = document.getElementById('btnStartUploadPipeline');

        this.douyinUrlInput = document.getElementById('douyinUrlInput');
        this.btnAnalyzeUrl = document.getElementById('btnAnalyzeUrl');

        this.progressBox = document.getElementById('progressBox');
        this.progressBarFill = document.getElementById('progressBarFill');
        this.progressStageText = document.getElementById('progressStageText');
        this.progressPercentText = document.getElementById('progressPercentText');
        this.progressSubText = document.getElementById('progressSubText');

        this.profileGrid = document.getElementById('profileGrid');
        this.queriesGrid = document.getElementById('queriesGrid');
        this.resultsGrid = document.getElementById('resultsGrid');
        this.resultsCountText = document.getElementById('resultsCountText');

        this.rngMinScore = document.getElementById('rngMinScore');
        this.lblMinScore = document.getElementById('lblMinScore');
        this.selSortBy = document.getElementById('selSortBy');
        this.numMinLikes = document.getElementById('numMinLikes');
        this.btnApplyFilters = document.getElementById('btnApplyFilters');

        this.historyDrawer = document.getElementById('historyDrawer');
        this.btnOpenHistory = document.getElementById('btnOpenHistory');
        this.btnCloseHistory = document.getElementById('btnCloseHistory');
        this.historyList = document.getElementById('historyList');

        this.settingsModal = document.getElementById('settingsModal');
        this.btnSettings = document.getElementById('btnSettings');
        this.btnCloseModal = document.getElementById('btnCloseModal');
        this.btnSaveConfig = document.getElementById('btnSaveConfig');
    }

    initEvents() {
        this.inputTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.dataset.tab;
                this.inputTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                Object.keys(this.tabContents).forEach(k => {
                    if (this.tabContents[k]) {
                        this.tabContents[k].style.display = (k === targetTab) ? 'block' : 'none';
                    }
                });
            });
        });

        document.querySelectorAll('.step-item').forEach(item => {
            item.addEventListener('click', () => {
                const s = parseInt(item.dataset.step);
                this.goToStep(s);
            });
        });

        if (this.btnExecuteSmartSearch) {
            this.btnExecuteSmartSearch.addEventListener('click', () => this.handleSmartSearchClick());
        }
        if (this.btnTranslatePreview) {
            this.btnTranslatePreview.addEventListener('click', () => this.handleTranslatePreviewClick());
        }
        if (this.btnAddCustomQuery) {
            this.btnAddCustomQuery.addEventListener('click', () => this.addCustomQuery());
        }
        if (this.btnSearchFromPreview) {
            this.btnSearchFromPreview.addEventListener('click', () => this.executeSearchWithSelectedQueries());
        }

        if (this.dropzone) {
            this.dropzone.addEventListener('click', () => this.fileInput.click());
            this.dropzone.addEventListener('dragover', (e) => { e.preventDefault(); this.dropzone.classList.add('dragover'); });
            this.dropzone.addEventListener('dragleave', () => this.dropzone.classList.remove('dragover'));
            this.dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                this.dropzone.classList.remove('dragover');
                if (e.dataTransfer.files.length) this.handleFileSelected(e.dataTransfer.files[0]);
            });
        }
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => {
                if (e.target.files.length) this.handleFileSelected(e.target.files[0]);
            });
        }
        if (this.btnStartUploadPipeline) {
            this.btnStartUploadPipeline.addEventListener('click', () => this.startUploadPipeline());
        }

        if (this.btnAnalyzeUrl) {
            this.btnAnalyzeUrl.addEventListener('click', () => this.startUrlPipeline());
        }

        if (this.rngMinScore) {
            this.rngMinScore.addEventListener('input', (e) => {
                if (this.lblMinScore) this.lblMinScore.innerText = `${e.target.value}%`;
                this.applyLocalFilters();
            });
        }
        if (this.selSortBy) {
            this.selSortBy.addEventListener('change', () => this.applyLocalFilters());
        }
        if (this.numMinLikes) {
            this.numMinLikes.addEventListener('input', () => this.applyLocalFilters());
        }
        if (this.btnApplyFilters) {
            this.btnApplyFilters.addEventListener('click', () => this.applyLocalFilters());
        }

        if (this.btnOpenHistory) {
            this.btnOpenHistory.addEventListener('click', () => this.openHistory());
        }
        if (this.btnCloseHistory) {
            this.btnCloseHistory.addEventListener('click', () => this.closeHistory());
        }

        if (this.btnSettings) {
            this.btnSettings.addEventListener('click', () => this.openSettings());
        }
        if (this.btnCloseModal) {
            this.btnCloseModal.addEventListener('click', () => this.closeSettings());
        }
        if (this.btnSaveConfig) {
            this.btnSaveConfig.addEventListener('click', () => this.saveSettings());
        }
    }

    getSelectedLanguage() {
        const rad = document.querySelector('input[name="searchLang"]:checked');
        return rad ? rad.value : 'auto';
    }

    getSelectedDepth() {
        const rad = document.querySelector('input[name="searchDepth"]:checked');
        return rad ? rad.value : 'normal';
    }

    getSelectedFlow() {
        const rad = document.querySelector('input[name="searchFlow"]:checked');
        return rad ? rad.value : 'auto';
    }

    async handleSmartSearchClick() {
        const flow = this.getSelectedFlow();
        if (flow === 'manual') {
            await this.handleTranslatePreviewClick();
        } else {
            await this.executeFullSmartSearch();
        }
    }

    async handleTranslatePreviewClick() {
        const q = this.smartSearchInput.value.trim();
        if (!q) return alert('Vui lòng nhập từ khóa tìm kiếm.');

        this.btnTranslatePreview.disabled = true;
        this.showProgress('Đang phân tích ý định tìm kiếm & sinh từ khóa tiếng Trung...', 30);

        try {
            const resp = await fetch('/api/v1/query/translate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    query: q,
                    language: this.getSelectedLanguage(),
                    mode: this.getSelectedDepth()
                })
            });

            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || 'Lỗi phân tích');

            this.currentPreviewData = data;
            this.renderPreviewPanel(data);
            this.translationPreviewPanel.style.display = 'block';
            this.progressBox.style.display = 'none';
            this.btnTranslatePreview.disabled = false;
        } catch (err) {
            alert('Lỗi: ' + err.message);
            this.progressBox.style.display = 'none';
            this.btnTranslatePreview.disabled = false;
        }
    }

    renderPreviewPanel(data) {
        if (this.previewOriginalText) this.previewOriginalText.innerText = data.original_query || this.smartSearchInput.value;
        if (this.previewLangBadge) {
            this.previewLangBadge.innerText = (data.detected_language === 'vi') ? '🇻🇳 Tiếng Việt' : (data.detected_language === 'zh' ? '🇨🇳 Tiếng Trung' : '🇬🇧 English');
        }
        if (this.previewIntentText) this.previewIntentText.innerText = data.intent || 'VISUAL_CONTENT_SEARCH';

        const cats = data.chinese_keywords || {};
        let catHtml = '';
        const catLabels = {
            'primary': 'Chủ thể / Đối tượng',
            'clothing': 'Trang phục',
            'action': 'Hành động',
            'scene': 'Bối cảnh / Không gian',
            'style': 'Phong cách / Tone'
        };

        Object.keys(catLabels).forEach(key => {
            const list = cats[key] || [];
            if (list.length > 0) {
                catHtml += `<div class="cat-chip-row"><span class="cat-label">${catLabels[key]}:</span><div class="chip-list">${list.map(w => `<span class="chip-pill ${key==='primary'?'primary':''}">${w}</span>`).join('')}</div></div>`;
            }
        });
        if (this.previewKeywordCategories) {
            this.previewKeywordCategories.innerHTML = catHtml || '<p class="text-muted">Không có nhóm từ khóa phụ trợ.</p>';
        }

        const queryScores = data.query_scores || [];
        if (this.queriesChecklist) {
            this.queriesChecklist.innerHTML = queryScores.map((item, idx) => {
                let tierClass = 'score-high';
                if (item.tier === 'exact') tierClass = 'score-exact';
                else if (item.tier === 'medium') tierClass = 'score-med';
                else if (item.tier === 'broad') tierClass = 'score-broad';

                return `<div class="query-check-item"><label><input type="checkbox" class="chk-query-item" value="${item.query}" checked><span>${item.query}</span></label><span class="query-score-tag ${tierClass}">${item.score}đ (${item.tier.toUpperCase()})</span></div>`;
            }).join('');
        }
    }

    addCustomQuery() {
        const val = this.txtCustomQuery.value.trim();
        if (!val) return;
        const itemHtml = `<div class="query-check-item"><label><input type="checkbox" class="chk-query-item" value="${val}" checked><span>${val} (Tự thêm)</span></label><span class="query-score-tag score-high">100đ (CUSTOM)</span></div>`;
        if (this.queriesChecklist) {
            this.queriesChecklist.insertAdjacentHTML('afterbegin', itemHtml);
        }
        this.txtCustomQuery.value = '';
    }

    async executeSearchWithSelectedQueries() {
        const q = this.smartSearchInput.value.trim();
        const selectedQueries = Array.from(document.querySelectorAll('.chk-query-item:checked')).map(c => c.value);
        if (!selectedQueries.length) return alert('Vui lòng chọn ít nhất một từ khóa tiếng Trung để quét.');

        await this.executeFullSmartSearch(selectedQueries);
    }

    async executeFullSmartSearch(customQueries = null) {
        const q = this.smartSearchInput.value.trim();
        if (!q) return alert('Vui lòng nhập từ khóa tìm kiếm.');

        this.btnExecuteSmartSearch.disabled = true;
        this.showProgress('Đang chuyển ngữ & quét đa tầng trên Douyin...', 45);

        try {
            const resp = await fetch('/api/v1/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    query: q,
                    language: this.getSelectedLanguage(),
                    mode: this.getSelectedDepth(),
                    custom_queries: customQueries,
                    min_likes: parseInt(this.numMinLikes ? this.numMinLikes.value : 0) || 0,
                    min_score: parseFloat(this.rngMinScore ? this.rngMinScore.value : 60.0) || 60.0,
                    sort_by: this.selSortBy ? this.selSortBy.value : 'similarity'
                })
            });

            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || 'Lỗi tìm kiếm');

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;
            this.rawResults = data.results || [];
            
            this.searchHistory.unshift({
                query: q,
                lang: data.language,
                queries_count: (data.queries || []).length,
                results_count: this.rawResults.length,
                time: new Date().toLocaleTimeString()
            });

            if (data.preview && data.preview.query_scores) {
                this.renderQueries(data.preview.query_scores.map(s => ({
                    query: s.query,
                    category: s.tier.toUpperCase(),
                    score: s.score / 100,
                    reason: s.reason || 'Phân tầng độ liên quan'
                })));
            }

            this.applyLocalFilters();
            this.goToStep(4);
            this.progressBox.style.display = 'none';
            this.btnExecuteSmartSearch.disabled = false;
        } catch (err) {
            alert('Lỗi: ' + err.message);
            this.progressBox.style.display = 'none';
            this.btnExecuteSmartSearch.disabled = false;
        }
    }

    handleFileSelected(file) {
        this.selectedFile = file;
        this.videoFileName.innerText = file.name;
        this.videoFileSize.innerText = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        this.videoPreview.src = URL.createObjectURL(file);
        this.uploadDetails.style.display = 'grid';
        this.dropzone.style.display = 'none';
    }

    goToStep(stepNumber) {
        document.querySelectorAll('.step-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.step) === stepNumber);
        });
        document.querySelectorAll('.step-section').forEach(sec => sec.classList.remove('active'));
        const sec = document.getElementById(`step${stepNumber}Section`);
        if (sec) sec.classList.add('active');
    }

    async startUploadPipeline() {
        if (!this.selectedFile) return;
        this.btnStartUploadPipeline.disabled = true;
        this.showProgress('Đang tải video lên máy chủ...', 5);

        const isDeep = document.getElementById('chkDeepSearchUpload')?.checked;
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('user_hint', document.getElementById('userHintInput') ? document.getElementById('userHintInput').value.trim() : '');
        formData.append('deep_search', isDeep ? 'true' : 'false');

        try {
            const resp = await fetch('/api/v1/analyze/video', { method: 'POST', body: formData });
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || 'Upload failed');

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;
            this.startJobPolling();
        } catch (err) {
            alert('Lỗi: ' + err.message);
            this.btnStartUploadPipeline.disabled = false;
            this.progressBox.style.display = 'none';
        }
    }

    async startUrlPipeline() {
        const url = this.douyinUrlInput.value.trim();
        if (!url) return alert('Vui lòng dán link Douyin hoặc TikTok.');

        this.btnAnalyzeUrl.disabled = true;
        this.showProgress('Đang phân tích link Douyin/TikTok...', 10);

        try {
            const resp = await fetch('/api/v1/analyze/url', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url: url, deep_search: false })
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error.message || 'Parse link failed');

            this.currentVideoId = data.video_id;
            this.currentJobId = data.job_id;
            this.startJobPolling();
        } catch (err) {
            alert('Lỗi: ' + err.message);
            this.btnAnalyzeUrl.disabled = false;
            this.progressBox.style.display = 'none';
        }
    }

    showProgress(stageText, percent) {
        this.progressBox.style.display = 'block';
        this.progressStageText.innerText = stageText;
        this.progressPercentText.innerText = percent + '%';
        this.progressBarFill.style.width = percent + '%';
    }

    startJobPolling() {
        if (this.pollInterval) clearInterval(this.pollInterval);

        const stageDescriptions = {
            'queued': 'Đang xếp hàng chờ xử lý...',
            'processing': 'FFmpeg đang trích xuất khung hình và âm thanh...',
            'analyzing': 'AI Multimodal đang phân tích bối cảnh, ASR & OCR...',
            'generating_queries': 'Đang tạo bộ 20 truy vấn tiếng Trung phân tầng...',
            'searching': 'Đang quét trên Douyin...',
            'ranking': 'Đang tính điểm 6 chiều & lọc trùng lặp...',
            'completed': 'Hoàn tất toàn bộ pipeline!',
            'failed': 'Có lỗi xảy ra trong quá trình xử lý'
        };

        this.pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`/api/v1/jobs/${this.currentJobId}`);
                const job = await resp.json();

                this.showProgress(stageDescriptions[job.stage] || job.stage, job.progress_percent);

                if (job.status === 'completed') {
                    clearInterval(this.pollInterval);
                    await this.loadAllPipelineData(job);
                } else if (job.status === 'failed') {
                    clearInterval(this.pollInterval);
                    alert('Pipeline thất bại: ' + (job.error_message || 'Không rõ nguyên nhân'));
                    if (this.btnStartUploadPipeline) this.btnStartUploadPipeline.disabled = false;
                    if (this.btnAnalyzeUrl) this.btnAnalyzeUrl.disabled = false;
                    this.progressBox.style.display = 'none';
                }
            } catch (e) {
                console.error('Polling error:', e);
            }
        }, 1500);
    }

    async loadAllPipelineData(job) {
        if (job.analysis) {
            this.renderProfile(job.analysis);
        }

        if (job.queries && job.queries.length > 0) {
            this.renderQueries(job.queries.map((q, i) => ({
                query: q,
                category: i < 5 ? 'EXACT' : (i < 10 ? 'HIGH' : 'MEDIUM'),
                score: 0.95 - (i * 0.02),
                reason: 'Phân tầng độ liên quan AI'
            })));
        }

        const respRes = await fetch(`/api/v1/search/${this.currentJobId}/results?page=1&page_size=50`);
        if (respRes.ok) {
            const rData = await respRes.json();
            this.rawResults = rData.results || [];
            this.applyLocalFilters();
        }

        this.goToStep(4);
        this.progressBox.style.display = 'none';
        if (this.btnStartUploadPipeline) this.btnStartUploadPipeline.disabled = false;
        if (this.btnAnalyzeUrl) this.btnAnalyzeUrl.disabled = false;
    }

    renderProfile(p) {
        if (!this.profileGrid) return;
        this.profileGrid.innerHTML = `
            <div class="profile-card">
                <h3><i class="fa-solid fa-list-check"></i> Tóm Tắt & Chủ Đề</h3>
                <p><strong>Chủ đề:</strong> ${p.main_topic || 'N/A'}</p>
                <p style="margin-top:8px;"><strong>Tóm tắt:</strong> ${p.summary || 'N/A'}</p>
                <div class="tag-list">
                    ${(p.secondary_topics || []).map(t => `<span class="tag">${t}</span>`).join('')}
                </div>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-person-walking"></i> Nhân Vật & Hành Động</h3>
                <p><strong>Đối tượng/Nhân vật:</strong> ${(p.people || []).join(', ') || 'N/A'}</p>
                <p style="margin-top:8px;"><strong>Hành động:</strong> ${(p.actions || []).join(', ') || 'N/A'}</p>
                <p style="margin-top:8px;"><strong>Bối cảnh:</strong> ${(p.locations || []).join(', ') || 'N/A'}</p>
            </div>
            <div class="profile-card">
                <h3><i class="fa-solid fa-microphone-lines"></i> Âm Thanh & Văn Bản (OCR/ASR)</h3>
                <p><strong>Ngôn ngữ:</strong> ${p.spoken_language || 'vi'}</p>
                <p style="margin-top:8px;"><strong>Lời thoại:</strong> ${p.transcript || 'Không có lời thoại rõ ràng'}</p>
                <p style="margin-top:8px;"><strong>Chữ trên video (OCR):</strong> ${(p.ocr_text || []).join(' | ') || 'N/A'}</p>
            </div>
        `;
    }

    renderQueries(queries) {
        if (!this.queriesGrid) return;
        this.queriesGrid.innerHTML = queries.map(q => {
            const scorePct = Math.round((q.score || 0.8) * 100);
            return `
                <div class="query-card">
                    <div class="query-header">
                        <span class="category-badge">${q.category || 'GENERAL'}</span>
                        <span class="query-score">${scorePct}%</span>
                    </div>
                    <div class="query-text">${q.query}</div>
                    <div class="query-reason"><i class="fa-solid fa-circle-info"></i> ${q.reason || 'Truy vấn tối ưu'}</div>
                </div>
            `;
        }).join('');
    }

    applyLocalFilters() {
        const minScore = parseFloat(this.rngMinScore ? this.rngMinScore.value : 60) || 60;
        const sortBy = this.selSortBy ? this.selSortBy.value : 'similarity';
        const minLikes = parseInt(this.numMinLikes ? this.numMinLikes.value : 0) || 0;

        let res = [...this.rawResults];

        res = res.filter(r => (r.final_score || r.score || 0) >= minScore);

        if (minLikes > 0) {
            res = res.filter(r => (r.likes || r.like_count || 0) >= minLikes);
        }

        if (sortBy === 'likes') {
            res.sort((a, b) => (b.likes || b.like_count || 0) - (a.likes || a.like_count || 0));
        } else if (sortBy === 'comments') {
            res.sort((a, b) => (b.comments || b.comment_count || 0) - (a.comments || a.comment_count || 0));
        } else if (sortBy === 'shares') {
            res.sort((a, b) => (b.shares || b.share_count || 0) - (a.shares || a.share_count || 0));
        } else if (sortBy === 'newest') {
            res.sort((a, b) => (b.publish_time || '').localeCompare(a.publish_time || ''));
        } else {
            res.sort((a, b) => (b.final_score || b.score || 0) - (a.final_score || a.score || 0));
        }

        this.filteredResults = res;
        this.renderResults(res);
    }

    renderResults(results) {
        if (!this.resultsGrid) return;
        if (this.resultsCountText) {
            this.resultsCountText.innerText = `Tìm thấy ${results.length} video phù hợp`;
        }

        if (results.length === 0) {
            this.resultsGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align:center; padding: 40px; color: var(--text-muted);">
                    <i class="fa-solid fa-film fa-3x" style="margin-bottom: 12px; display:block;"></i>
                    <p>Không có video nào thỏa mãn tiêu chí lọc. Vui lòng hạ ngưỡng điểm hoặc số like.</p>
                </div>
            `;
            return;
        }

        this.resultsGrid.innerHTML = results.map(r => {
            const score = r.final_score || r.score || 85;
            const tier = r.match_tier || 'High Match';
            const likes = (r.likes || r.like_count || 0).toLocaleString();
            const comments = (r.comments || r.comment_count || 0).toLocaleString();
            const shares = (r.shares || r.share_count || 0).toLocaleString();
            const cover = r.thumbnail || r.cover_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400';
            const douyinUrl = r.url || `https://www.douyin.com/video/${r.video_id}`;

            return `
                <div class="result-card">
                    <div class="result-cover-wrapper">
                        <img src="${cover}" class="result-cover" alt="Cover" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400';">
                        <span class="match-badge">${score}% ${tier}</span>
                    </div>
                    <div class="result-content">
                        <h4 class="result-title" title="${r.title}">${r.title}</h4>
                        <div class="result-meta">
                            <span><i class="fa-solid fa-user"></i> ${r.author || 'Creator'}</span>
                            <span><i class="fa-solid fa-clock"></i> ${r.duration || 30}s</span>
                        </div>
                        <div class="result-stats">
                            <span><i class="fa-solid fa-heart text-danger"></i> ${likes}</span>
                            <span><i class="fa-solid fa-comment text-primary"></i> ${comments}</span>
                            <span><i class="fa-solid fa-share text-success"></i> ${shares}</span>
                        </div>
                        <div class="result-scores-sub">
                            <span title="Keyword Score">KW: ${r.keyword_score || 80}</span>
                            <span title="Semantic Score">SEM: ${r.semantic_score || 85}</span>
                            <span title="Visual Score">VIS: ${r.visual_score || 90}</span>
                        </div>
                        <div class="result-actions" style="margin-top:12px;">
                            <a href="${douyinUrl}" target="_blank" class="btn btn-sm btn-primary" style="width:100%; text-align:center; text-decoration:none;">
                                <i class="fa-brands fa-tiktok"></i> Mở Trên Douyin
                            </a>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async openHistory() {
        if (this.historyDrawer) this.historyDrawer.classList.add('open');
        try {
            const resp = await fetch('/api/v1/history');
            const data = await resp.json();
            const list = data.history || [];
            if (this.historyList) {
                if (list.length === 0) {
                    this.historyList.innerHTML = '<p class="text-muted" style="text-align:center; padding:20px;">Chưa có lịch sử tìm kiếm.</p>';
                } else {
                    this.historyList.innerHTML = list.map(item => `
                        <div class="history-item">
                            <div class="history-title">${item.filename || item.id}</div>
                            <div class="history-meta">
                                <span>${item.results_count || 0} kết quả</span>
                                <span>${item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}</span>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (e) {
            console.error('Load history error:', e);
        }
    }

    closeHistory() {
        if (this.historyDrawer) this.historyDrawer.classList.remove('open');
    }

    async openSettings() {
        if (this.settingsModal) this.settingsModal.classList.add('open');
        await this.loadSettings();
    }

    closeSettings() {
        if (this.settingsModal) this.settingsModal.classList.remove('open');
    }

    async loadSettings() {
        try {
            const resp = await fetch('/api/v1/settings');
            if (resp.ok) {
                const s = await resp.json();
                const txtGemini = document.getElementById('txtGeminiKey');
                const txtCookie = document.getElementById('txtDouyinCookie');
                if (txtGemini && s.gemini_api_key_masked) txtGemini.placeholder = `Hiện tại: ${s.gemini_api_key_masked}`;
                if (txtCookie && s.douyin_cookie_configured) txtCookie.placeholder = `Đã cấu hình Cookie`;
            }
        } catch (e) {}
    }

    async saveSettings() {
        const geminiKey = document.getElementById('txtGeminiKey')?.value.trim();
        const cookie = document.getElementById('txtDouyinCookie')?.value.trim();

        const payload = {};
        if (geminiKey) payload.gemini_api_key = geminiKey;
        if (cookie) payload.douyin_cookie = cookie;

        try {
            const resp = await fetch('/api/v1/settings', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if (resp.ok) {
                alert('Đã lưu cấu hình backend thành công!');
                this.closeSettings();
            }
        } catch (e) {
            alert('Lỗi lưu cấu hình: ' + e.message);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new DouyinApp();
});
