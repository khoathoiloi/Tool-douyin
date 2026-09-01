package com.douyin.contentfinder.data.repository

import com.douyin.contentfinder.api.*
import com.douyin.contentfinder.data.SearchHistoryDao
import com.douyin.contentfinder.data.SearchHistoryEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

class SearchRepository(
    private val apiService: ApiService,
    private val historyDao: SearchHistoryDao
) {
    suspend fun smartSearch(
        query: String,
        language: String = "auto",
        mode: String = "normal",
        minScore: Float = 60.0f,
        minLikes: Int = 0,
        sortBy: String = "similarity"
    ): Result<SearchResultsResponse> = withContext(Dispatchers.IO) {
        try {
            val req = SmartSearchRequest(
                query = query,
                language = language,
                mode = mode,
                deepSearch = (mode == "deep"),
                minScore = minScore,
                minLikes = minLikes,
                sortBy = sortBy
            )
            val resp = apiService.smartSearch(req)
            if (resp.isSuccessful && resp.body() != null) {
                val data = resp.body()!!
                historyDao.insert(
                    SearchHistoryEntity(
                        id = data.jobId ?: "kw_${System.currentTimeMillis()}",
                        title = query,
                        inputType = "smart_search",
                        resultCount = data.results.size
                    )
                )
                Result.success(data)
            } else {
                Result.failure(Exception("Lỗi Backend (${resp.code()}): ${resp.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun previewKeywords(query: String, mode: String = "normal"): Result<TranslateQueryResponse> = withContext(Dispatchers.IO) {
        try {
            val req = TranslateQueryRequest(query = query, mode = mode)
            val resp = apiService.translateQuery(req)
            if (resp.isSuccessful && resp.body() != null) {
                Result.success(resp.body()!!)
            } else {
                Result.failure(Exception("Không thể sinh từ khóa: ${resp.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun uploadVideo(file: File, userHint: String = "", deepSearch: Boolean = false): Result<SearchInitResponse> = withContext(Dispatchers.IO) {
        try {
            val reqFile = file.asRequestBody("video/*".toMediaTypeOrNull())
            val body = MultipartBody.Part.createFormData("file", file.name, reqFile)
            val hintBody = userHint.toRequestBody("text/plain".toMediaTypeOrNull())
            val deepBody = deepSearch.toString().toRequestBody("text/plain".toMediaTypeOrNull())

            val resp = apiService.uploadVideo(body, hintBody, deepBody)
            if (resp.isSuccessful && resp.body() != null) {
                val data = resp.body()!!
                historyDao.insert(
                    SearchHistoryEntity(
                        id = data.jobId,
                        title = file.name,
                        inputType = "video_upload",
                        resultCount = 0
                    )
                )
                Result.success(data)
            } else {
                Result.failure(Exception("Upload thất bại: ${resp.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun searchByUrl(url: String, userHint: String = "", deepSearch: Boolean = false): Result<SearchInitResponse> = withContext(Dispatchers.IO) {
        try {
            val req = UrlSearchRequest(url = url, userHint = userHint, deepSearch = deepSearch)
            val resp = apiService.searchByUrl(req)
            if (resp.isSuccessful && resp.body() != null) {
                val data = resp.body()!!
                historyDao.insert(
                    SearchHistoryEntity(
                        id = data.jobId,
                        title = data.title ?: url,
                        inputType = "douyin_url",
                        resultCount = 0
                    )
                )
                Result.success(data)
            } else {
                Result.failure(Exception("Phân tích URL thất bại: ${resp.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getJobStatus(jobId: String): Result<JobStatusResponse> = withContext(Dispatchers.IO) {
        try {
            val resp = apiService.getJobStatus(jobId)
            if (resp.isSuccessful && resp.body() != null) {
                Result.success(resp.body()!!)
            } else {
                Result.failure(Exception("Lỗi trạng thái Job: ${resp.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getJobResults(jobId: String, minScore: Float = 60.0f): Result<SearchResultsResponse> = withContext(Dispatchers.IO) {
        try {
            val resp = apiService.getJobResults(jobId = jobId, minScore = minScore)
            if (resp.isSuccessful && resp.body() != null) {
                Result.success(resp.body()!!)
            } else {
                Result.failure(Exception("Lấy kết quả thất bại: ${resp.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun getAllHistory(): Flow<List<SearchHistoryEntity>> = historyDao.getAllHistory()

    suspend fun clearHistory() = withContext(Dispatchers.IO) {
        historyDao.clearAll()
    }
}
