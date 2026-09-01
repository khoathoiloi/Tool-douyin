package com.douyin.contentfinder.api

import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface ApiService {

    // 1. Unified Smart Search (Vietnamese / Chinese / English / Auto)
    @POST("api/v1/search")
    suspend fun smartSearch(
        @Body request: SmartSearchRequest
    ): Response<SearchResultsResponse>

    // 2. Keyword Translation & Chinese Query Preview
    @POST("api/v1/query/translate")
    suspend fun translateQuery(
        @Body request: TranslateQueryRequest
    ): Response<TranslateQueryResponse>

    // 3. Video File Upload & Multimodal Analysis
    @Multipart
    @POST("api/v1/analyze/video")
    suspend fun uploadVideo(
        @Part file: MultipartBody.Part,
        @Part("user_hint") userHint: RequestBody,
        @Part("deep_search") deepSearch: RequestBody
    ): Response<SearchInitResponse>

    // 4. Douyin / TikTok URL Analysis
    @POST("api/v1/analyze/url")
    suspend fun searchByUrl(
        @Body request: UrlSearchRequest
    ): Response<SearchInitResponse>

    // 5. Job Status & Progress Polling
    @GET("api/v1/jobs/{job_id}")
    suspend fun getJobStatus(
        @Path("job_id") jobId: String
    ): Response<JobStatusResponse>

    // 6. Job Final Ranked Results
    @GET("api/v1/search/{job_id}/results")
    suspend fun getJobResults(
        @Path("job_id") jobId: String,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 30,
        @Query("min_score") minScore: Float = 60.0f
    ): Response<SearchResultsResponse>

    // 7. Search History
    @GET("api/v1/history")
    suspend fun getHistory(): Response<HistoryResponse>

    // 8. Backend Configuration
    @GET("api/v1/settings")
    suspend fun getSettings(): Response<SettingsResponse>

    // 9. Health Check
    @GET("health")
    suspend fun checkHealth(): Response<HealthResponse>

    companion object {
        private var defaultBaseUrl = "http://10.0.2.2:8000/" // Android Emulator fallback

        fun create(baseUrl: String = defaultBaseUrl): ApiService {
            val url = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            val client = OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(60, TimeUnit.SECONDS)
                .addInterceptor(logging)
                .build()

            return Retrofit.Builder()
                .baseUrl(url)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(ApiService::class.java)
        }
    }
}
