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
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class HistoryFragment : Fragment() {

    private lateinit var rvHistory: RecyclerView
    private lateinit var btnClearHistory: Button
    private lateinit var adapter: HistoryAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_history, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        rvHistory = view.findViewById(R.id.rvHistory)
        btnClearHistory = view.findViewById(R.id.btnClearHistory)

        adapter = HistoryAdapter { item ->
            // Re-run search or navigate to SearchFragment
            (activity as? MainActivity)?.navigateToSearchWithQuery(item.title, item.inputType)
        }

        rvHistory.layoutManager = LinearLayoutManager(requireContext())
        rvHistory.adapter = adapter

        val dao = AppDatabase.getInstance(requireContext()).historyDao()

        lifecycleScope.launch {
            dao.getAllHistory().collectLatest { list ->
                adapter.setItems(list)
            }
        }

        btnClearHistory.setOnClickListener {
            lifecycleScope.launch {
                dao.clearAll()
                Toast.makeText(requireContext(), "Đã xóa toàn bộ lịch sử tìm kiếm!", Toast.LENGTH_SHORT).show()
            }
        }
    }
}
