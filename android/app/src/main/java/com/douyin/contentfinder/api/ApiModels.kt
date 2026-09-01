package com.douyin.contentfinder.api

import com.google.gson.annotations.SerializedName

data class UrlSearchRequest(
    @SerializedName("url") val url: String,
    @SerializedName("user_hint") val userHint: String = "",
    @SerializedName("deep_search") val deepSearch: Boolean = false
)

data class KeywordSearchRequest(
    @SerializedName("keyword") val keyword: String,
    @SerializedName("deep_search") val deepSearch: Boolean = false,
    @SerializedName("limit") val limit: Int = 20,
    @SerializedName("min_likes") val minLikes: Int = 0
)

data class SearchInitResponse(
    @SerializedName("job_id") val jobId: String,
    @SerializedName("video_id") val videoId: String?,
    @SerializedName("status") val status: String,
    @SerializedName("title") val title: String? = null,
    @SerializedName("cover_url") val coverUrl: String? = null
)

data class JobStatusResponse(
    @SerializedName("job_id") val jobId: String,
    @SerializedName("stage") val stage: String,
    @SerializedName("status") val status: String,
    @SerializedName("progress_percent") val progressPercent: Int,
    @SerializedName("error_message") val errorMessage: String? = null,
    @SerializedName("analysis") val analysis: AnalysisSummary? = null,
    @SerializedName("queries") val queries: List<String>? = null
)

data class AnalysisSummary(
    @SerializedName("summary") val summary: String?,
    @SerializedName("main_topic") val mainTopic: String?,
    @SerializedName("transcript") val transcript: String?
)

data class SearchResultItem(
    @SerializedName("rank") val rank: Int,
    @SerializedName("score") val score: Int,
    @SerializedName("match_tier") val matchTier: String,
    @SerializedName("video_id") val videoId: String,
    @SerializedName("url") val url: String,
    @SerializedName("author") val author: String,
    @SerializedName("title") val title: String,
    @SerializedName("cover_url") val coverUrl: String?,
    @SerializedName("like_count") val likeCount: Long,
    @SerializedName("comment_count") val commentCount: Long,
    @SerializedName("search_query") val searchQuery: String
)

data class SearchResultsResponse(
    @SerializedName("job_id") val jobId: String,
    @SerializedName("total_results") val totalResults: Int,
    @SerializedName("page") val page: Int,
    @SerializedName("has_more") val hasMore: Boolean,
    @SerializedName("results") val results: List<SearchResultItem>
)
