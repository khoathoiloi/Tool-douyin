package com.douyin.contentfinder.ui

import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.douyin.contentfinder.R

class SettingsFragment : Fragment() {

    private lateinit var etBaseUrl: EditText
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
        btnSaveSettings = view.findViewById(R.id.btnSaveSettings)
        btnClearCache = view.findViewById(R.id.btnClearCache)

        val prefs = requireContext().getSharedPreferences("app_settings", Context.MODE_PRIVATE)
        etBaseUrl.setText(prefs.getString("base_url", "http://10.0.2.2:8000"))

        btnSaveSettings.setOnClickListener {
            val url = etBaseUrl.text.toString().trim()
            prefs.edit().putString("base_url", url).apply()
            Toast.makeText(requireContext(), "Đã lưu cài đặt!", Toast.LENGTH_SHORT).show()
        }

        btnClearCache.setOnClickListener {
            requireContext().cacheDir.deleteRecursively()
            Toast.makeText(requireContext(), "Đã dọn dẹp cache!", Toast.LENGTH_SHORT).show()
        }
    }
}
