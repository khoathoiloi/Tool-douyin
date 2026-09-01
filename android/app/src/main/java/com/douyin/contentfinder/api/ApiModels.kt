package com.douyin.contentfinder.api

import com.google.gson.annotations.SerializedName

// ==========================================
// 1. REQUEST DATA MODELS
// ==========================================

data class SmartSearchRequest(
    @SerializedName("query") val query: String,
    @SerializedName("keyword") val keyword: String? = null,
    @SerializedName("language") val language: String = "auto",
    @SerializedName("mode") val mode: String = "normal",
    @SerializedName("deep_search") val deepSearch: Boolean = false,
    @SerializedName("min_score") val minScore: Float = 60.0f,
    @SerializedName("min_likes") val minLikes: Int = 0,
    @SerializedName("sort_by") val sortBy: String = "similarity",
    @SerializedName("limit") val limit: Int = 20
)

data class UrlSearchRequest(
    @SerializedName("url") val url: String,
    @SerializedName("douyin_url") val douyinUrl: String? = null,
    @SerializedName("user_hint") val userHint: String = "",
    @SerializedName("deep_search") val deepSearch: Boolean = false,
    @SerializedName("mode") val mode: String = "normal"
)

data class TranslateQueryRequest(
    @SerializedName("query") val query: String,
    @SerializedName("language") val language: String = "auto",
    @SerializedName("mode") val mode: String = "normal"
)

data class KeywordSearchRequest(
    @SerializedName("keyword") val keyword: String,
    @SerializedName("deep_search") val deepSearch: Boolean = false,
    @SerializedName("limit") val limit: Int = 20,
    @SerializedName("min_likes") val minLikes: Int = 0
)

// ==========================================
// 2. RESPONSE DATA MODELS
// ==========================================

data class SearchInitResponse(
    @SerializedName("job_id") val jobId: String,
    @SerializedName("video_id") val videoId: String? = null,
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
    @SerializedName("summary") val summary: String? = null,
    @SerializedName("main_topic") val mainTopic: String? = null,
    @SerializedName("transcript") val transcript: String? = null
)

data class QueryScoreItem(
    @SerializedName("query") val query: String,
    @SerializedName("score") val score: Int,
    @SerializedName("tier") val tier: String
)

data class TranslateQueryResponse(
    @SerializedName("original_query") val originalQuery: String,
    @SerializedName("detected_language") val detectedLanguage: String,
    @SerializedName("intent") val intent: String,
    @SerializedName("chinese_keywords") val chineseKeywords: Map<String, List<String>> = emptyMap(),
    @SerializedName("queries") val queries: List<String> = emptyList(),
    @SerializedName("query_scores") val queryScores: List<QueryScoreItem> = emptyList()
)

data class SearchResultItem(
    @SerializedName("rank") val rank: Int = 0,
    @SerializedName("score") val score: Int = 0,
    @SerializedName("final_score") val finalScore: Int = 0,
    @SerializedName("match_tier") val matchTier: String = "High",
    @SerializedName("video_id") val videoId: String = "",
    @SerializedName("url") val url: String = "",
    @SerializedName("author") val author: String = "",
    @SerializedName("title") val title: String = "",
    @SerializedName("cover_url") val coverUrl: String? = null,
    @SerializedName("thumbnail") val thumbnail: String? = null,
    @SerializedName("like_count") val likeCount: Long = 0,
    @SerializedName("likes") val likes: Long = 0,
    @SerializedName("comment_count") val commentCount: Long = 0,
    @SerializedName("comments") val comments: Long = 0,
    @SerializedName("share_count") val shareCount: Long = 0,
    @SerializedName("shares") val shares: Long = 0,
    @SerializedName("duration") val duration: Int = 0,
    @SerializedName("search_query") val searchQuery: String = "",
    
    // 6 Sub-Scores Breakdown
    @SerializedName("keyword_score") val keywordScore: Int = 0,
    @SerializedName("semantic_score") val semanticScore: Int = 0,
    @SerializedName("visual_score") val visualScore: Int = 0,
    @SerializedName("scene_score") val sceneScore: Int = 0,
    @SerializedName("action_score") val actionScore: Int = 0,
    @SerializedName("query_score") val queryScore: Int = 0
) {
    fun getEffectiveScore(): Int = if (finalScore > 0) finalScore else score
    fun getEffectiveLikes(): Long = if (likes > 0) likes else likeCount
    fun getEffectiveComments(): Long = if (comments > 0) comments else commentCount
    fun getEffectiveThumbnail(): String? = coverUrl ?: thumbnail
}

data class SearchResultsResponse(
    @SerializedName("job_id") val jobId: String? = null,
    @SerializedName("query") val query: String? = null,
    @SerializedName("total_results") val totalResults: Int = 0,
    @SerializedName("count") val count: Int = 0,
    @SerializedName("page") val page: Int = 1,
    @SerializedName("has_more") val hasMore: Boolean = false,
    @SerializedName("results") val results: List<SearchResultItem> = emptyList()
)

data class HistoryItem(
    @SerializedName("id") val id: String,
    @SerializedName("filename") val filename: String? = null,
    @SerializedName("results_count") val resultsCount: Int = 0,
    @SerializedName("created_at") val createdAt: String? = null
)

data class HistoryResponse(
    @SerializedName("history") val history: List<HistoryItem> = emptyList()
)

data class SettingsResponse(
    @SerializedName("project_name") val projectName: String? = null,
    @SerializedName("version") val version: String? = null,
    @SerializedName("ai_provider") val aiProvider: String? = null,
    @SerializedName("douyin_search_provider") val douyinSearchProvider: String? = null
)

data class HealthResponse(
    @SerializedName("status") val status: String,
    @SerializedName("service") val service: String? = null,
    @SerializedName("version") val version: String? = null
)
