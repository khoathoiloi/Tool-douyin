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

sealed interface SearchUiState {
    object Idle : SearchUiState
    data class Loading(val message: String) : SearchUiState
    data class Polling(val stage: String, val percent: Int, val jobId: String) : SearchUiState
    data class KeywordPreview(val preview: TranslateQueryResponse) : SearchUiState
    data class Success(
        val results: List<SearchResultItem>,
        val rawResults: List<SearchResultItem>,
        val totalCount: Int,
        val jobId: String? = null
    ) : SearchUiState
    data class Error(val message: String) : SearchUiState
}

class SearchViewModel(
    private val repository: SearchRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<SearchUiState>(SearchUiState.Idle)
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()

    private var pollingJob: Job? = null
    private var allRawResults: List<SearchResultItem> = emptyList()

    var currentMinScore: Float = 60.0f
    var currentMinLikes: Int = 0
    var currentSortBy: String = "similarity"
    var isDeepSearch: Boolean = false
    var selectedLanguage: String = "auto"

    fun executeSmartSearch(query: String) {
        val q = query.trim()
        if (q.isEmpty()) {
            _uiState.value = SearchUiState.Error("Vui lòng nhập từ khóa tìm kiếm.")
            return
        }

        _uiState.value = SearchUiState.Loading("Đang phân tích và tìm kiếm trên Douyin...")
        val mode = if (isDeepSearch) "deep" else "normal"

        viewModelScope.launch {
            val res = repository.smartSearch(
                query = q,
                language = selectedLanguage,
                mode = mode,
                minScore = currentMinScore,
                minLikes = currentMinLikes,
                sortBy = currentSortBy
            )
            res.onSuccess { data ->
                allRawResults = data.results
                _uiState.value = SearchUiState.Success(
                    results = data.results,
                    rawResults = data.results,
                    totalCount = data.results.size,
                    jobId = data.jobId
                )
            }.onFailure { err ->
                _uiState.value = SearchUiState.Error(err.message ?: "Lỗi kết nối Backend")
            }
        }
    }

    fun previewKeywords(query: String) {
        val q = query.trim()
        if (q.isEmpty()) {
            _uiState.value = SearchUiState.Error("Vui lòng nhập từ khóa để xem trước.")
            return
        }

        _uiState.value = SearchUiState.Loading("Đang phân tích ý định và sinh từ khóa...")
        val mode = if (isDeepSearch) "deep" else "normal"

        viewModelScope.launch {
            val res = repository.previewKeywords(query = q, mode = mode)
            res.onSuccess { previewData ->
                _uiState.value = SearchUiState.KeywordPreview(previewData)
            }.onFailure { err ->
                _uiState.value = SearchUiState.Error(err.message ?: "Không thể sinh từ khóa")
            }
        }
    }

    fun uploadVideo(file: File, userHint: String = "") {
        _uiState.value = SearchUiState.Loading("Đang tải video lên server...")
        viewModelScope.launch {
            val res = repository.uploadVideo(file = file, userHint = userHint, deepSearch = isDeepSearch)
            res.onSuccess { initData ->
                startPolling(initData.jobId)
            }.onFailure { err ->
                _uiState.value = SearchUiState.Error(err.message ?: "Upload video thất bại")
            }
        }
    }

    fun searchDouyinUrl(url: String, userHint: String = "") {
        val u = url.trim()
        if (u.isEmpty()) {
            _uiState.value = SearchUiState.Error("Vui lòng dán đường link video Douyin.")
            return
        }

        _uiState.value = SearchUiState.Loading("Đang bóc tách metadata link Douyin...")
        viewModelScope.launch {
            val res = repository.searchByUrl(url = u, userHint = userHint, deepSearch = isDeepSearch)
            res.onSuccess { initData ->
                startPolling(initData.jobId)
            }.onFailure { err ->
                _uiState.value = SearchUiState.Error(err.message ?: "Không thể phân tích URL này")
            }
        }
    }

    private fun startPolling(jobId: String) {
        pollingJob?.cancel()
        pollingJob = viewModelScope.launch {
            while (true) {
                delay(1500)
                val statusRes = repository.getJobStatus(jobId)
                statusRes.onSuccess { job ->
                    _uiState.value = SearchUiState.Polling(
                        stage = job.stage,
                        percent = job.progressPercent,
                        jobId = jobId
                    )
                    if (job.status == "completed") {
                        fetchFinalResults(jobId)
                        return@launch
                    } else if (job.status == "failed") {
                        _uiState.value = SearchUiState.Error(job.errorMessage ?: "Pipeline xử lý thất bại.")
                        return@launch
                    }
                }.onFailure {
                    // Retry on transient network glitch
                }
            }
        }
    }

    private fun fetchFinalResults(jobId: String) {
        viewModelScope.launch {
            val res = repository.getJobResults(jobId = jobId, minScore = currentMinScore)
            res.onSuccess { data ->
                allRawResults = data.results
                _uiState.value = SearchUiState.Success(
                    results = data.results,
                    rawResults = data.results,
                    totalCount = data.results.size,
                    jobId = jobId
                )
            }.onFailure { err ->
                _uiState.value = SearchUiState.Error(err.message ?: "Lỗi tải danh sách kết quả")
            }
        }
    }

    fun applyFilters(minScore: Float, minLikes: Int, sortBy: String) {
        currentMinScore = minScore
        currentMinLikes = minLikes
        currentSortBy = sortBy

        if (allRawResults.isEmpty()) return

        var filtered = allRawResults.filter { item ->
            item.getEffectiveScore() >= minScore && item.getEffectiveLikes() >= minLikes
        }

        filtered = when (sortBy) {
            "likes" -> filtered.sortedByDescending { it.getEffectiveLikes() }
            "comments" -> filtered.sortedByDescending { it.getEffectiveComments() }
            "newest" -> filtered.sortedByDescending { it.videoId }
            else -> filtered.sortedByDescending { it.getEffectiveScore() }
        }

        _uiState.value = SearchUiState.Success(
            results = filtered,
            rawResults = allRawResults,
            totalCount = filtered.size
        )
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
