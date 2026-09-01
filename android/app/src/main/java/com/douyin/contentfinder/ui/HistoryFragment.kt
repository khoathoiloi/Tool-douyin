package com.douyin.contentfinder.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.douyin.contentfinder.R
import com.douyin.contentfinder.data.AppDatabase
import kotlinx.coroutines.launch

class HistoryFragment : Fragment() {

    private lateinit var rvHistory: RecyclerView
    private lateinit var btnClearHistory: Button

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_history, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        rvHistory = view.findViewById(R.id.rvHistory)
        btnClearHistory = view.findViewById(R.id.btnClearHistory)

        rvHistory.layoutManager = LinearLayoutManager(requireContext())

        btnClearHistory.setOnClickListener {
            lifecycleScope.launch {
                AppDatabase.getInstance(requireContext()).historyDao().clearAll()
                Toast.makeText(requireContext(), "Đã xóa lịch sử!", Toast.LENGTH_SHORT).show()
            }
        }
    }
}
