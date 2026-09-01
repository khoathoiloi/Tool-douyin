package com.douyin.contentfinder.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import coil.load
import coil.transform.RoundedCornersTransformation
import com.douyin.contentfinder.R
import com.douyin.contentfinder.api.SearchResultItem
import com.douyin.contentfinder.utils.IntentUtils

class ResultsAdapter(
    private val items: MutableList<SearchResultItem> = mutableListOf()
) : RecyclerView.Adapter<ResultsAdapter.ResultViewHolder>() {

    fun setResults(newItems: List<SearchResultItem>) {
        items.clear()
        items.addAll(newItems)
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ResultViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_search_result, parent, false)
        return ResultViewHolder(view)
    }

    override fun onBindViewHolder(holder: ResultViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    inner class ResultViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val ivCover: ImageView = itemView.findViewById(R.id.ivCover)
        private val tvTitle: TextView = itemView.findViewById(R.id.tvTitle)
        private val tvAuthor: TextView = itemView.findViewById(R.id.tvAuthor)
        private val tvLikes: TextView = itemView.findViewById(R.id.tvLikes)
        private val tvScore: TextView = itemView.findViewById(R.id.tvScore)
        private val tvQuery: TextView = itemView.findViewById(R.id.tvQuery)
        private val btnOpenDouyin: Button = itemView.findViewById(R.id.btnOpenDouyin)
        private val btnCopyLink: Button = itemView.findViewById(R.id.btnCopyLink)

        fun bind(item: SearchResultItem) {
            tvTitle.text = item.title
            tvAuthor.text = item.author
            tvLikes.text = String.format("❤️ %,d", item.likeCount)
            tvQuery.text = "Query: ${item.searchQuery}"
            tvScore.text = "${item.score}% Match"

            // Color tier
            val colorRes = when {
                item.score >= 90 -> R.color.score_very_high
                item.score >= 80 -> R.color.score_high
                item.score >= 70 -> R.color.score_good
                else -> R.color.score_low
            }
            tvScore.setTextColor(ContextCompat.getColor(itemView.context, colorRes))

            // Efficient image loading via Coil (low memory for Galaxy S9)
            ivCover.load(item.coverUrl) {
                crossfade(true)
                transformations(RoundedCornersTransformation(16f))
                placeholder(android.R.drawable.ic_menu_gallery)
                error(android.R.drawable.ic_menu_report_image)
            }

            btnOpenDouyin.setOnClickListener {
                IntentUtils.openDouyinVideo(itemView.context, item.url)
            }

            btnCopyLink.setOnClickListener {
                val clipboard = itemView.context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("Douyin URL", item.url)
                clipboard.setPrimaryClip(clip)
                Toast.makeText(itemView.context, "Đã sao chép link Douyin!", Toast.LENGTH_SHORT).show()
            }
        }
    }
}
