package com.douyin.contentfinder.utils

import android.content.Context
import android.content.Intent
import android.net.Uri
import java.util.regex.Pattern

object IntentUtils {
    fun extractUrlFromText(text: String?): String? {
        if (text.isNullOrBlank()) return null
        val matcher = Pattern.compile("https?://[\\S]+").matcher(text)
        return if (matcher.find()) matcher.group(0) else null
    }

    fun openDouyinVideo(context: Context, url: String) {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            // Fallback to browser
            val webIntent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            context.startActivity(webIntent)
        }
    }
}
