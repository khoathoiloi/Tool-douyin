package com.douyin.contentfinder.ui

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.douyin.contentfinder.R
import com.douyin.contentfinder.api.*
import com.douyin.contentfinder.data.AppDatabase
import com.douyin.contentfinder.data.SearchHistoryEntity
import com.google.android.material.tabs.TabLayout
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.io.FileOutputStream

class SearchFragment : Fragment() {

    private lateinit var tabLayout: TabLayout
    private lateinit var layoutVideoInput: View
    private lateinit var layoutUrlInput: View
    private lateinit var layoutKeywordInput: View
    private lateinit var btnPickVideo: Button
    private lateinit var tvSelectedVideoName: TextView
    private lateinit var etDouyinUrl: EditText
    private lateinit var etManualKeyword: EditText
    private lateinit var switchDeepSearch: CompoundButton
    private lateinit var tvSimilarityLabel: TextView
    private lateinit var seekBarSimilarity: SeekBar
    private lateinit var btnStartSearch: Button

    private lateinit var cardProgress: View
    private lateinit var tvProgressStage: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var tvResultsHeader: TextView
    private lateinit var rvResults: RecyclerView
    private lateinit var adapter: ResultsAdapter

    private var selectedVideoUri: Uri? = null
    private var selectedVideoFile: File? = null
    private var currentTab = 0 // 0: Video, 1: URL, 2: Keyword
    private var pollingJob: Job? = null
    private val apiService = ApiService.create()

    private val videoPickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            val uri = result.data?.data
            if (uri != null) {
                selectedVideoUri = uri
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
    }

    private fun initViews(v: View) {
        tabLayout = v.findViewById(R.id.tabLayout)
        layoutVideoInput = v.findViewById(R.id.layoutVideoInput)
        layoutUrlInput = v.findViewById(R.id.layoutUrlInput)
        layoutKeywordInput = v.findViewById(R.id.layoutKeywordInput)
        btnPickVideo = v.findViewById(R.id.btnPickVideo)
        tvSelectedVideoName = v.findViewById(R.id.tvSelectedVideoName)
        etDouyinUrl = v.findViewById(R.id.etDouyinUrl)
        etManualKeyword = v.findViewById(R.id.etManualKeyword)
        switchDeepSearch = v.findViewById(R.id.switchDeepSearch)
        tvSimilarityLabel = v.findViewById(R.id.tvSimilarityLabel)
        seekBarSimilarity = v.findViewById(R.id.seekBarSimilarity)
        btnStartSearch = v.findViewById(R.id.btnStartSearch)

        cardProgress = v.findViewById(R.id.cardProgress)
        tvProgressStage = v.findViewById(R.id.tvProgressStage)
        progressBar = v.findViewById(R.id.progressBar)
        tvResultsHeader = v.findViewById(R.id.tvResultsHeader)
        rvResults = v.findViewById(R.id.rvResults)

        adapter = ResultsAdapter()
        rvResults.layoutManager = LinearLayoutManager(requireContext())
        rvResults.adapter = adapter
    }

    private fun setupEvents() {
        tabLayout.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab?) {
                currentTab = tab?.position ?: 0
                layoutVideoInput.visibility = if (currentTab == 0) View.VISIBLE else View.GONE
                layoutUrlInput.visibility = if (currentTab == 1) View.VISIBLE else View.GONE
                layoutKeywordInput.visibility = if (currentTab == 2) View.VISIBLE else View.GONE
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

        seekBarSimilarity.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                tvSimilarityLabel.text = "Độ tương đồng tối thiểu: $progress%"
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })

        btnStartSearch.setOnClickListener {
            when (currentTab) {
                0 -> startVideoUploadSearch()
                1 -> startUrlSearch()
                2 -> startKeywordSearch()
            }
        }
    }

    fun setSharedUrl(url: String) {
        tabLayout.getTabAt(1)?.select()
        etDouyinUrl.setText(url)
        startUrlSearch()
    }

    private fun startVideoUploadSearch() {
        val file = selectedVideoFile ?: run {
            Toast.makeText(requireContext(), "Vui lòng chọn video trước", Toast.LENGTH_SHORT).show()
            return
        }
        showProgress("Đang tải video lên server...", 10)

        lifecycleScope.launch {
            try {
                val reqFile = file.asRequestBody("video/*".toMediaTypeOrNull())
                val body = MultipartBody.Part.createFormData("file", file.name, reqFile)
                val hint = "".toRequestBody("text/plain".toMediaTypeOrNull())
                val isDeep = switchDeepSearch.isChecked.toString().toRequestBody("text/plain".toMediaTypeOrNull())

                val resp = apiService.uploadVideo(body, hint, isDeep)
                if (resp.isSuccessful && resp.body() != null) {
                    val jobId = resp.body()!!.jobId
                    saveHistory(jobId, file.name, "video")
                    startPolling(jobId)
                } else {
                    hideProgress()
                    Toast.makeText(requireContext(), "Lỗi tải video", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                hideProgress()
                Toast.makeText(requireContext(), "Lỗi kết nối: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun startUrlSearch() {
        val url = etDouyinUrl.text.toString().trim()
        if (url.isEmpty()) {
            Toast.makeText(requireContext(), "Vui lòng dán link Douyin", Toast.LENGTH_SHORT).show()
            return
        }
        showProgress("Đang phân tích link Douyin...", 15)

        lifecycleScope.launch {
            try {
                val req = UrlSearchRequest(url = url, deepSearch = switchDeepSearch.isChecked)
                val resp = apiService.searchByUrl(req)
                if (resp.isSuccessful && resp.body() != null) {
                    val jobId = resp.body()!!.jobId
                    saveHistory(jobId, resp.body()!!.title ?: url, "url")
                    startPolling(jobId)
                } else {
                    hideProgress()
                    Toast.makeText(requireContext(), "Không thể phân tích URL này", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                hideProgress()
                Toast.makeText(requireContext(), "Lỗi kết nối: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun startKeywordSearch() {
        val kw = etManualKeyword.text.toString().trim()
        if (kw.isEmpty()) {
            Toast.makeText(requireContext(), "Vui lòng nhập từ khóa tiếng Trung", Toast.LENGTH_SHORT).show()
            return
        }
        showProgress("Đang quét Douyin theo từ khóa '$kw'...", 50)

        lifecycleScope.launch {
            try {
                val req = KeywordSearchRequest(keyword = kw, deepSearch = switchDeepSearch.isChecked, limit = 30)
                val resp = apiService.searchByKeyword(req)
                hideProgress()
                if (resp.isSuccessful && resp.body() != null) {
                    val items = resp.body()!!.results
                    adapter.setResults(items)
                    tvResultsHeader.visibility = View.VISIBLE
                    saveHistory(resp.body()!!.jobId, kw, "keyword")
                } else {
                    Toast.makeText(requireContext(), "Không tìm thấy kết quả", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                hideProgress()
                Toast.makeText(requireContext(), "Lỗi: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun startPolling(jobId: String) {
        pollingJob?.cancel()
        pollingJob = lifecycleScope.launch {
            while (true) {
                delay(1500)
                try {
                    val resp = apiService.getJobStatus(jobId)
                    if (resp.isSuccessful && resp.body() != null) {
                        val job = resp.body()!!
                        showProgress(job.stage, job.progressPercent)

                        if (job.status == "completed") {
                            fetchResults(jobId)
                            break
                        } else if (job.status == "failed") {
                            hideProgress()
                            Toast.makeText(requireContext(), "Thất bại: ${job.errorMessage}", Toast.LENGTH_LONG).show()
                            break
                        }
                    }
                } catch (e: Exception) {
                    // Retry on network glitch
                }
            }
        }
    }

    private fun fetchResults(jobId: String) {
        lifecycleScope.launch {
            try {
                val minScore = seekBarSimilarity.progress.toFloat()
                val resp = apiService.getJobResults(jobId, page = 1, pageSize = 30, minScore = minScore)
                hideProgress()
                if (resp.isSuccessful && resp.body() != null) {
                    val list = resp.body()!!.results
                    adapter.setResults(list)
                    tvResultsHeader.visibility = View.VISIBLE
                }
            } catch (e: Exception) {
                hideProgress()
            }
        }
    }

    private fun showProgress(stage: String, percent: Int) {
        cardProgress.visibility = View.VISIBLE
        tvProgressStage.text = stage
        progressBar.progress = percent
    }

    private fun hideProgress() {
        cardProgress.visibility = View.GONE
    }

    private fun saveHistory(id: String, title: String, type: String) {
        lifecycleScope.launch {
            try {
                val db = AppDatabase.getInstance(requireContext())
                db.historyDao().insert(SearchHistoryEntity(id = id, title = title, inputType = type, resultCount = 0))
            } catch (e: Exception) {}
        }
    }

    private fun getFileFromUri(uri: Uri): File {
        val inputStream = requireContext().contentResolver.openInputStream(uri)
        val file = File(requireContext().cacheDir, "temp_upload_${System.currentTimeMillis()}.mp4")
        val outputStream = FileOutputStream(file)
        inputStream?.copyTo(outputStream)
        inputStream?.close()
        outputStream.close()
        return file
    }
}
