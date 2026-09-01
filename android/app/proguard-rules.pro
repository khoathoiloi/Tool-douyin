-keepattributes *Annotation*
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}
-keep class com.douyin.contentfinder.api.** { *; }
-dontwarn okhttp3.**
-dontwarn retrofit2.**
