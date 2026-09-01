package com.douyin.contentfinder

import android.app.Application
import android.content.ComponentCallbacks2
import android.graphics.Bitmap
import coil.ImageLoader
import coil.ImageLoaderFactory
import coil.disk.DiskCache
import coil.memory.MemoryCache
import okhttp3.OkHttpClient
import java.io.File
import java.util.concurrent.TimeUnit

/**
 * Custom Application class optimized specifically for Samsung Galaxy S9 (4GB RAM).
 * Implements fine-tuned Coil ImageLoader, RGB_565 bitmap compression,
 * strict memory cache limits, and system onTrimMemory callbacks.
 */
class ContentFinderApp : Application(), ImageLoaderFactory {

    private var imageLoaderInstance: ImageLoader? = null

    override fun onCreate() {
        super.onCreate()
    }

    override fun newImageLoader(): ImageLoader {
        return imageLoaderInstance ?: synchronized(this) {
            imageLoaderInstance ?: buildOptimizedImageLoader().also { imageLoaderInstance = it }
        }
    }

    private fun buildOptimizedImageLoader(): ImageLoader {
        // Optimized OkHttpClient for Galaxy S9 network (fast connection recycling)
        val okHttpClient = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()

        return ImageLoader.Builder(this)
            .okHttpClient(okHttpClient)
            // 1. Strict Memory Cache: Max 20% of available app heap to avoid OOM
            .memoryCache {
                MemoryCache.Builder(this)
                    .maxSizePercent(0.20)
                    .strongReferencesEnabled(true)
                    .build()
            }
            // 2. Disk Cache: Max 50MB in app cache directory
            .diskCache {
                DiskCache.Builder()
                    .directory(File(cacheDir, "douyin_image_cache"))
                    .maxSizeBytes(50L * 1024 * 1024)
                    .build()
            }
            // 3. RGB_565: Consumes 50% less RAM than ARGB_8888 (2 bytes vs 4 bytes per pixel)
            .bitmapConfig(Bitmap.Config.RGB_565)
            .allowRgb565(true)
            .crossfade(true)
            .build()
    }

    override fun onTrimMemory(level: Int) {
        super.onTrimMemory(level)
        // Aggressively free bitmap caches when Galaxy S9 background memory is tight
        if (level >= ComponentCallbacks2.TRIM_MEMORY_RUNNING_LOW) {
            imageLoaderInstance?.memoryCache?.clear()
        }
    }

    override fun onLowMemory() {
        super.onLowMemory()
        imageLoaderInstance?.memoryCache?.clear()
    }
}
