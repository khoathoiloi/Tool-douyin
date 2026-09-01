package com.douyin.contentfinder.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "search_history")
data class SearchHistoryEntity(
    @PrimaryKey val id: String,
    val title: String,
    val inputType: String, // "video", "url", "keyword"
    val resultCount: Int,
    val timestamp: Long = System.currentTimeMillis()
)
