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

    @Multipart
    @POST("api/v1/search/video")
    suspend fun uploadVideo(
        @Part file: MultipartBody.Part,
        @Part("user_hint") userHint: RequestBody,
        @Part("deep_search") deepSearch: RequestBody
    ): Response<SearchInitResponse>

    @POST("api/v1/search/url")
    suspend fun searchByUrl(
        @Body request: UrlSearchRequest
    ): Response<SearchInitResponse>

    @POST("api/v1/search/keyword")
    suspend fun searchByKeyword(
        @Body request: KeywordSearchRequest
    ): Response<SearchResultsResponse>

    @GET("api/v1/search/{job_id}")
    suspend fun getJobStatus(
        @Path("job_id") jobId: String
    ): Response<JobStatusResponse>

    @GET("api/v1/search/{job_id}/results")
    suspend fun getJobResults(
        @Path("job_id") jobId: String,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
        @Query("min_score") minScore: Float = 70.0f
    ): Response<SearchResultsResponse>

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
