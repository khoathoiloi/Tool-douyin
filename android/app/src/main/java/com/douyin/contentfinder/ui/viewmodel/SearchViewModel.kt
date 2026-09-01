package com.douyin.contentfinder.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.douyin.contentfinder.api.*
import com.douyin.contentfinder.data.repository.SearchRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import java.io.IOException

// =================================================================
// 8 EXPLICIT PIPELINE STATES REQUIRED FOR APK <-> BACKEND SYNC
// =================================================================
sealed interface SearchUiState {
    object Idle : SearchUiState
    data class Uploading(val percent: Int, val message: String = "Đang tải video lên Backend...") : SearchUiState
    data class Queued(val jobId: String, val message: String = "Đang chờ hàng đợi xử lý...") : SearchUiState
    data class Analyzing(val percent: Int, val message: String = "Đang phân tích bối cảnh & âm thanh video...", val jobId: String) : SearchUiState
    data class Searching(val percent: Int, val message: String = "Đang quét tìm kiếm trên Douyin...", val jobId: String) : SearchUiState
    data class Ranking(val percent: Int, val message: String = "Đang lọc và chấm điểm 6 tầng tương đồng...", val jobId: String) : SearchUiState
    data class Completed(
        val results: List<SearchResultItem>,
        val totalCount: Int,
        val page: Int = 1,
        val hasMore: Boolean = false,
        val jobId: String? = null
    ) : SearchUiState
    data class KeywordPreview(val preview: TranslateQueryResponse) : SearchUiState
    data class Error(val message: String, val jobId: String? = null, val canRetry: Boolean = true) : SearchUiState
}

class SearchViewModel(
    private val repository: SearchRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<SearchUiState>(SearchUiState.Idle)
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()

    private var pollingJob: Job? = null
    var activeJobId: String? = null
        private set

    private var allLoadedResults: MutableList<SearchResultItem> = mutableListOf()
    private var currentPage: Int = 1
    private var isFetchingNextPage: Boolean = false

    var currentMinScore: Float = 60.0f
    var currentMinLikes: Int = 0
    var currentSortBy: String = "similarity"
    var isDeepSearch: Boolean = false
    var selectedLanguage: String = "auto"

    // 1. SMART TEXT SEARCH
    fun executeSmartSearch(query: String) {
        val q = query.trim()
        if (q.isEmpty()) {
            _uiState.value = SearchUiState.Error("Vui lòng nhập từ khóa tìm kiếm.", canRetry = false)
            return
        }

        _uiState.value = SearchUiState.Searching(percent = 25, message = "Đang phân tích Tiếng Việt & quét Douyin...", jobId = "")
        val mode = if (isDeepSearch) "deep" else "normal"

        viewModelScope.launch {
            try {
                val res = repository.smartSearch(
                    query = q,
                    language = selectedLanguage,
                    mode = mode,
                    minScore = currentMinScore,
                    minLikes = currentMinLikes,
                    sortBy = currentSortBy
                )
                res.onSuccess { data ->
                    activeJobId = data.jobId
                    allLoadedResults = data.results.toMutableList()
                    currentPage = 1
                    _uiState.value = SearchUiState.Completed(
                        results = allLoadedResults,
                        totalCount = data.totalResults.takeIf { it > 0 } ?: data.results.size,
                        page = 1,
                        hasMore = data.hasMore,
                        jobId = data.jobId
                    )
                }.onFailure { err ->
                    _uiState.value = SearchUiState.Error(err.message ?: "Lỗi kết nối Backend", canRetry = true)
                }
            } catch (e: Exception) {
                _uiState.value = SearchUiState.Error("Không thể kết nối Backend: ${e.message}", canRetry = true)
            }
        }
    }

    // 2. PREVIEW KEYWORDS
    fun previewKeywords(query: String) {
        val q = query.trim()
        if (q.isEmpty()) {
            _uiState.value = SearchUiState.Error("Vui lòng nhập từ khóa để xem trước.", canRetry = false)
            return
        }

        _uiState.value = SearchUiState.Analyzing(percent = 40, message = "Đang phân tích ý định & sinh từ khóa...", jobId = "")
        val mode = if (isDeepSearch) "deep" else "normal"

        viewModelScope.launch {
            try {
                val res = repository.previewKeywords(query = q, mode = mode)
                res.onSuccess { previewData ->
                    _uiState.value = SearchUiState.KeywordPreview(previewData)
                }.onFailure { err ->
                    _uiState.value = SearchUiState.Error(err.message ?: "Không thể sinh từ khóa", canRetry = true)
                }
            } catch (e: Exception) {
                _uiState.value = SearchUiState.Error("Lỗi kết nối: ${e.message}", canRetry = true)
            }
        }
    }

    // 3. VIDEO UPLOAD PIPELINE
    fun uploadVideo(file: File, userHint: String = "") {
        _uiState.value = SearchUiState.Uploading(percent = 15, message = "Đang tải video lên server...")
        viewModelScope.launch {
            try {
                val res = repository.uploadVideo(file = file, userHint = userHint, deepSearch = isDeepSearch)
                res.onSuccess { initData ->
                    activeJobId = initData.jobId
                    _uiState.value = SearchUiState.Queued(jobId = initData.jobId, message = "Video đã tải lên, đang vào hàng đợi phân tích...")
                    startPollingWithRetry(initData.jobId)
                }.onFailure { err ->
                    _uiState.value = SearchUiState.Error(err.message ?: "Upload video thất bại", canRetry = true)
                }
            } catch (e: Exception) {
                _uiState.value = SearchUiState.Error("Lỗi mạng khi upload: ${e.message}", canRetry = true)
            }
        }
    }

    // 4. DOUYIN URL PIPELINE
    fun searchDouyinUrl(url: String, userHint: String = "") {
        val u = url.trim()
        if (u.isEmpty()) {
            _uiState.value = SearchUiState.Error("Vui lòng dán đường link video Douyin.", canRetry = false)
            return
        }

        _uiState.value = SearchUiState.Analyzing(percent = 20, message = "Đang bóc tách metadata link Douyin...", jobId = "")
        viewModelScope.launch {
            try {
                val res = repository.searchByUrl(url = u, userHint = userHint, deepSearch = isDeepSearch)
                res.onSuccess { initData ->
                    activeJobId = initData.jobId
                    _uiState.value = SearchUiState.Queued(jobId = initData.jobId, message = "Đang xếp hàng phân tích link...")
                    startPollingWithRetry(initData.jobId)
                }.onFailure { err ->
                    _uiState.value = SearchUiState.Error(err.message ?: "Không thể phân tích URL này", canRetry = true)
                }
            } catch (e: Exception) {
                _uiState.value = SearchUiState.Error("Lỗi kết nối URL: ${e.message}", canRetry = true)
            }
        }
    }

    // 5. RESILIENT POLLING WITH AUTO-RECONNECT & RETRY DEFENSE
    fun startPollingWithRetry(jobId: String) {
        activeJobId = jobId
        pollingJob?.cancel()
        pollingJob = viewModelScope.launch {
            var retryCount = 0
            val maxRetries = 15

            while (true) {
                delay(1500)
                try {
                    val statusRes = repository.getJobStatus(jobId)
                    statusRes.onSuccess { job ->
                        retryCount = 0 // Reset retry counter on successful heartbeat

                        val stageLower = job.stage.lowercase()
                        val pct = job.progressPercent

                        when {
                            job.status == "completed" -> {
                                _uiState.value = SearchUiState.Ranking(percent = 95, message = "Đang hoàn tất bảng xếp hạng...", jobId = jobId)
                                fetchFinalResults(jobId)
                                return@launch
                            }
                            job.status == "failed" -> {
                                _uiState.value = SearchUiState.Error(job.errorMessage ?: "Pipeline xử lý thất bại.", jobId = jobId, canRetry = true)
                                return@launch
                            }
                            "analyz" in stageLower || "vision" in stageLower || "audio" in stageLower || "ocr" in stageLower -> {
                                _uiState.value = SearchUiState.Analyzing(percent = pct, message = job.stage, jobId = jobId)
                            }
                            "search" in stageLower || "query" in stageLower || "douyin" in stageLower -> {
                                _uiState.value = SearchUiState.Searching(percent = pct, message = job.stage, jobId = jobId)
                            }
                            "rank" in stageLower || "filter" in stageLower || "score" in stageLower -> {
                                _uiState.value = SearchUiState.Ranking(percent = pct, message = job.stage, jobId = jobId)
                            }
                            else -> {
                                _uiState.value = SearchUiState.Queued(jobId = jobId, message = job.stage)
                            }
                        }
                    }.onFailure {
                        retryCount++
                        if (retryCount >= maxRetries) {
                            _uiState.value = SearchUiState.Error("Mất kết nối với Backend. Bạn có thể bấm Thử Lại để tiếp tục.", jobId = jobId, canRetry = true)
                            return@launch
                        }
                    }
                } catch (e: IOException) {
                    retryCount++
                    if (retryCount >= maxRetries) {
                        _uiState.value = SearchUiState.Error("Mất kết nối mạng. Vui lòng kiểm tra WiFi/4G và bấm Thử Lại.", jobId = jobId, canRetry = true)
                        return@launch
                    }
                } catch (e: Exception) {
                    // Retain job_id and keep retrying
                }
            }
        }
    }

    private fun fetchFinalResults(jobId: String) {
        viewModelScope.launch {
            try {
                val res = repository.getJobResults(jobId = jobId, minScore = currentMinScore)
                res.onSuccess { data ->
                    allLoadedResults = data.results.toMutableList()
                    currentPage = 1
                    _uiState.value = SearchUiState.Completed(
                        results = allLoadedResults,
                        totalCount = data.totalResults.takeIf { it > 0 } ?: data.results.size,
                        page = 1,
                        hasMore = data.hasMore,
                        jobId = jobId
                    )
                }.onFailure { err ->
                    _uiState.value = SearchUiState.Error(err.message ?: "Lỗi tải danh sách kết quả", jobId = jobId, canRetry = true)
                }
            } catch (e: Exception) {
                _uiState.value = SearchUiState.Error("Không thể tải kết quả: ${e.message}", jobId = jobId, canRetry = true)
            }
        }
    }

    // 6. PAGINATION
    fun loadNextPage() {
        val jId = activeJobId ?: return
        if (isFetchingNextPage) return

        val state = _uiState.value
        if (state !is SearchUiState.Completed || !state.hasMore) return

        isFetchingNextPage = true
        val nextPage = currentPage + 1

        viewModelScope.launch {
            try {
                val res = repository.getJobResults(jobId = jId, minScore = currentMinScore)
                res.onSuccess { data ->
                    if (data.results.isNotEmpty()) {
                        currentPage = nextPage
                        allLoadedResults.addAll(data.results)
                        _uiState.value = SearchUiState.Completed(
                            results = allLoadedResults,
                            totalCount = data.totalResults,
                            page = nextPage,
                            hasMore = data.hasMore,
                            jobId = jId
                        )
                    }
                }
            } finally {
                isFetchingNextPage = false
            }
        }
    }

    fun retryActiveJob() {
        val jId = activeJobId
        if (!jId.isNullOrEmpty()) {
            startPollingWithRetry(jId)
        }
    }

    fun resetState() {
        _uiState.value = SearchUiState.Idle
    }
}

class SearchViewModelFactory(
    private val repository: SearchRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(SearchViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return SearchViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
