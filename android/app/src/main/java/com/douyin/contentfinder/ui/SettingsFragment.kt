package com.douyin.contentfinder.ui

import android.content.Context
import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.douyin.contentfinder.R
import com.douyin.contentfinder.api.ApiService
import kotlinx.coroutines.launch

class SettingsFragment : Fragment() {

    private lateinit var etBaseUrl: EditText
    private lateinit var tvHealthStatus: TextView
    private lateinit var btnTestConnection: Button
    private lateinit var btnSaveSettings: Button
    private lateinit var btnClearCache: Button

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_settings, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        etBaseUrl = view.findViewById(R.id.etBaseUrl)
        tvHealthStatus = view.findViewById(R.id.tvHealthStatus)
        btnTestConnection = view.findViewById(R.id.btnTestConnection)
        btnSaveSettings = view.findViewById(R.id.btnSaveSettings)
        btnClearCache = view.findViewById(R.id.btnClearCache)

        val prefs = requireContext().getSharedPreferences("app_settings", Context.MODE_PRIVATE)
        val currentUrl = prefs.getString("base_url", "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000"
        etBaseUrl.setText(currentUrl)

        btnTestConnection.setOnClickListener {
            val targetUrl = etBaseUrl.text.toString().trim()
            testConnection(targetUrl)
        }

        btnSaveSettings.setOnClickListener {
            val url = etBaseUrl.text.toString().trim()
            prefs.edit().putString("base_url", url).apply()
            Toast.makeText(requireContext(), "Đã lưu cấu hình Backend URL!", Toast.LENGTH_SHORT).show()
        }

        btnClearCache.setOnClickListener {
            requireContext().cacheDir.deleteRecursively()
            Toast.makeText(requireContext(), "Đã dọn dẹp bộ nhớ đệm cache!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun testConnection(url: String) {
        tvHealthStatus.text = "⏳ Đang kết nối..."
        tvHealthStatus.setTextColor(Color.parseColor("#ECC94B"))

        lifecycleScope.launch {
            try {
                val service = ApiService.create(baseUrl = url)
                val resp = service.checkHealth()
                if (resp.isSuccessful && resp.body()?.status == "healthy") {
                    tvHealthStatus.text = "🟢 Kết nối Backend (${resp.body()?.version ?: "OK"}) Thành Công!"
                    tvHealthStatus.setTextColor(Color.parseColor("#48BB78"))
                    Toast.makeText(requireContext(), "Kết nối Backend thành công!", Toast.LENGTH_SHORT).show()
                } else {
                    tvHealthStatus.text = "🔴 Backend phản hồi lỗi HTTP ${resp.code()}"
                    tvHealthStatus.setTextColor(Color.parseColor("#E53E3E"))
                }
            } catch (e: Exception) {
                tvHealthStatus.text = "🔴 Không thể kết nối: ${e.message}"
                tvHealthStatus.setTextColor(Color.parseColor("#E53E3E"))
            }
        }
    }
}
