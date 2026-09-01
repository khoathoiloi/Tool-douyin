package com.douyin.contentfinder.ui

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.douyin.contentfinder.R
import com.douyin.contentfinder.api.ApiService
import com.douyin.contentfinder.data.AppDatabase
import com.douyin.contentfinder.data.repository.SearchRepository
import com.douyin.contentfinder.ui.viewmodel.SearchUiState
import com.douyin.contentfinder.ui.viewmodel.SearchViewModel
import com.douyin.contentfinder.ui.viewmodel.SearchViewModelFactory
import com.google.android.material.switchmaterial.SwitchMaterial
import com.google.android.material.tabs.TabLayout
import kotlinx.coroutines.launch
import java.io.File
import java.io.FileOutputStream

class SearchFragment : Fragment() {

    private lateinit var tabLayout: TabLayout
    private lateinit var layoutSmartInput: View
    private lateinit var layoutVideoInput: View
    private lateinit var layoutUrlInput: View

    private lateinit var etSmartQuery: EditText
    private lateinit var btnPreviewKeywords: Button
    private lateinit var btnPickVideo: Button
    private lateinit var tvSelectedVideoName: TextView
    private lateinit var etVideoHint: EditText
    private lateinit var etDouyinUrl: EditText
    private lateinit var btnPasteClipboard: Button
    private lateinit var switchDeepSearch: SwitchMaterial
    private lateinit var btnStartSearch: Button

    private lateinit var cardKeywordPreview: View
    private lateinit var tvPreviewContent: TextView
    private lateinit var cardProgress: View
    private lateinit var tvProgressStage: TextView
    private lateinit var progressBar: ProgressBar

    private lateinit var layoutResultsHeader: View
    private lateinit var tvResultsHeader: TextView
    private lateinit var tvResultsCount: TextView
    private lateinit var rvResults: RecyclerView
    private lateinit var adapter: ResultsAdapter

    private var selectedVideoFile: File? = null
    private var currentTab = 0 // 0: Smart Vietnamese, 1: Video File, 2: Douyin URL

    private val viewModel: SearchViewModel by viewModels {
        val db = AppDatabase.getInstance(requireContext())
        val repo = SearchRepository(ApiService.create(), db.historyDao())
        SearchViewModelFactory(repo)
    }

    private val videoPickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            val uri = result.data?.data
            if (uri != null) {
                selectedVideoFile = getFileFromUri(uri)
                tvSelectedVideoName.text = selectedVideoFile?.name ?: "Đã chọn video"
            }
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_search, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        initViews(view)
        setupEvents()
        observeViewModel()
    }

    private fun initViews(v: View) {
        tabLayout = v.findViewById(R.id.tabLayout)
        layoutSmartInput = v.findViewById(R.id.layoutSmartInput)
        layoutVideoInput = v.findViewById(R.id.layoutVideoInput)
        layoutUrlInput = v.findViewById(R.id.layoutUrlInput)

        etSmartQuery = v.findViewById(R.id.etSmartQuery)
        btnPreviewKeywords = v.findViewById(R.id.btnPreviewKeywords)
        btnPickVideo = v.findViewById(R.id.btnPickVideo)
        tvSelectedVideoName = v.findViewById(R.id.tvSelectedVideoName)
        etVideoHint = v.findViewById(R.id.etVideoHint)
        etDouyinUrl = v.findViewById(R.id.etDouyinUrl)
        btnPasteClipboard = v.findViewById(R.id.btnPasteClipboard)
        switchDeepSearch = v.findViewById(R.id.switchDeepSearch)
        btnStartSearch = v.findViewById(R.id.btnStartSearch)

        cardKeywordPreview = v.findViewById(R.id.cardKeywordPreview)
        tvPreviewContent = v.findViewById(R.id.tvPreviewContent)
        cardProgress = v.findViewById(R.id.cardProgress)
        tvProgressStage = v.findViewById(R.id.tvProgressStage)
        progressBar = v.findViewById(R.id.progressBar)

        layoutResultsHeader = v.findViewById(R.id.layoutResultsHeader)
        tvResultsHeader = v.findViewById(R.id.tvResultsHeader)
        tvResultsCount = v.findViewById(R.id.tvResultsCount)
        rvResults = v.findViewById(R.id.rvResults)

        adapter = ResultsAdapter()
        rvResults.layoutManager = LinearLayoutManager(requireContext())
        rvResults.adapter = adapter
    }

    private fun setupEvents() {
        tabLayout.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab?) {
                currentTab = tab?.position ?: 0
                layoutSmartInput.visibility = if (currentTab == 0) View.VISIBLE else View.GONE
                layoutVideoInput.visibility = if (currentTab == 1) View.VISIBLE else View.GONE
                layoutUrlInput.visibility = if (currentTab == 2) View.VISIBLE else View.GONE
            }
            override fun onTabUnselected(tab: TabLayout.Tab?) {}
            override fun onTabReselected(tab: TabLayout.Tab?) {}
        })

        btnPickVideo.setOnClickListener {
            val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                type = "video/*"
                addCategory(Intent.CATEGORY_OPENABLE)
            }
            videoPickerLauncher.launch(intent)
        }

        btnPasteClipboard.setOnClickListener {
            val clipboard = requireContext().getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = clipboard.primaryClip
            if (clip != null && clip.itemCount > 0) {
                val text = clip.getItemAt(0).text.toString().trim()
                etDouyinUrl.setText(text)
                Toast.makeText(requireContext(), "Đã dán link từ Clipboard!", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(requireContext(), "Clipboard trống", Toast.LENGTH_SHORT).show()
            }
        }

        btnPreviewKeywords.setOnClickListener {
            viewModel.isDeepSearch = switchDeepSearch.isChecked
            viewModel.previewKeywords(etSmartQuery.text.toString())
        }

        btnStartSearch.setOnClickListener {
            viewModel.isDeepSearch = switchDeepSearch.isChecked
            when (currentTab) {
                0 -> viewModel.executeSmartSearch(etSmartQuery.text.toString())
                1 -> {
                    val file = selectedVideoFile
                    if (file == null) {
                        Toast.makeText(requireContext(), "Vui lòng chọn file video .mp4", Toast.LENGTH_SHORT).show()
                    } else {
                        viewModel.uploadVideo(file, etVideoHint.text.toString())
                    }
                }
                2 -> viewModel.searchDouyinUrl(etDouyinUrl.text.toString())
            }
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    when (state) {
                        is SearchUiState.Idle -> {
                            cardProgress.visibility = View.GONE
                            btnStartSearch.isEnabled = true
                            btnStartSearch.text = "🚀 [SEARCH] BẮT ĐẦU TÌM KIẾM"
                        }
                        is SearchUiState.Uploading -> {
                            cardProgress.visibility = View.VISIBLE
                            tvProgressStage.text = "📹 [Uploading] ${state.message} (${state.percent}%)"
                            progressBar.progress = state.percent
                            btnStartSearch.isEnabled = false
                            btnStartSearch.text = "⏳ Đang tải lên..."
                        }
                        is SearchUiState.Queued -> {
                            cardProgress.visibility = View.VISIBLE
                            tvProgressStage.text = "⏳ [Queued] ${state.message}"
                            progressBar.progress = 20
                            btnStartSearch.isEnabled = false
                            btnStartSearch.text = "⏳ Đang xếp hàng..."
                        }
                        is SearchUiState.Analyzing -> {
                            cardProgress.visibility = View.VISIBLE
                            tvProgressStage.text = "🧠 [Analyzing] ${state.message} (${state.percent}%)"
                            progressBar.progress = state.percent
                            btnStartSearch.isEnabled = false
                            btnStartSearch.text = "⏳ AI đang phân tích..."
                        }
                        is SearchUiState.Searching -> {
                            cardProgress.visibility = View.VISIBLE
                            tvProgressStage.text = "🔍 [Searching] ${state.message} (${state.percent}%)"
                            progressBar.progress = state.percent
                            btnStartSearch.isEnabled = false
                            btnStartSearch.text = "⏳ Đang quét Douyin..."
                        }
                        is SearchUiState.Ranking -> {
                            cardProgress.visibility = View.VISIBLE
                            tvProgressStage.text = "📊 [Ranking] ${state.message} (${state.percent}%)"
                            progressBar.progress = state.percent
                            btnStartSearch.isEnabled = false
                            btnStartSearch.text = "⏳ Đang xếp hạng..."
                        }
                        is SearchUiState.KeywordPreview -> {
                            cardProgress.visibility = View.GONE
                            btnStartSearch.isEnabled = true
                            btnStartSearch.text = "🚀 [SEARCH] BẮT ĐẦU TÌM KIẾM"
                            cardKeywordPreview.visibility = View.VISIBLE

                            val sb = StringBuilder()
                            val cats = state.preview.chineseKeywords
                            cats.forEach { (k, v) ->
                                sb.append("• ${k.uppercase()}: ${v.joinToString(", ")}\n")
                            }
                            sb.append("\n🔥 Top Search Queries:\n")
                            state.preview.queryScores.take(5).forEach { q ->
                                sb.append("  [${q.tier.uppercase()} - ${q.score}đ] ${q.query}\n")
                            }
                            tvPreviewContent.text = sb.toString().trim()
                        }
                        is SearchUiState.Completed -> {
                            cardProgress.visibility = View.GONE
                            btnStartSearch.isEnabled = true
                            btnStartSearch.text = "🚀 [SEARCH] BẮT ĐẦU TÌM KIẾM"
                            layoutResultsHeader.visibility = View.VISIBLE
                            tvResultsCount.text = "(${state.totalCount} video)"
                            adapter.setResults(state.results)
                        }
                        is SearchUiState.Error -> {
                            cardProgress.visibility = View.GONE
                            btnStartSearch.isEnabled = true
                            btnStartSearch.text = if (state.canRetry && !state.jobId.isNullOrEmpty()) "🔄 THỬ LẠI JOB NÀY" else "🚀 [SEARCH] BẮT ĐẦU TÌM KIẾM"
                            Toast.makeText(requireContext(), state.message, Toast.LENGTH_LONG).show()
                        }

                    }
                }
            }
        }
    }

    fun setSharedUrl(url: String) {
        tabLayout.getTabAt(2)?.select()
        etDouyinUrl.setText(url)
        viewModel.searchDouyinUrl(url)
    }

    fun setSharedQuery(query: String) {
        tabLayout.getTabAt(0)?.select()
        etSmartQuery.setText(query)
        viewModel.executeSmartSearch(query)
    }


    private fun getFileFromUri(uri: Uri): File {
        val inputStream = requireContext().contentResolver.openInputStream(uri)
        val file = File(requireContext().cacheDir, "temp_video_${System.currentTimeMillis()}.mp4")
        val outputStream = FileOutputStream(file)
        inputStream?.copyTo(outputStream)
        inputStream?.close()
        outputStream.close()
        return file
    }
}
