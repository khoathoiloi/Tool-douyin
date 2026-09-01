package com.douyin.contentfinder.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.douyin.contentfinder.R
import com.douyin.contentfinder.data.SearchHistoryEntity

class HistoryAdapter(
    private val onItemClick: (SearchHistoryEntity) -> Unit
) : RecyclerView.Adapter<HistoryAdapter.HistoryViewHolder>() {

    private val items: MutableList<SearchHistoryEntity> = mutableListOf()

    fun setItems(newItems: List<SearchHistoryEntity>) {
        items.clear()
        items.addAll(newItems)
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): HistoryViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_history, parent, false)
        return HistoryViewHolder(view)
    }

    override fun onBindViewHolder(holder: HistoryViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    inner class HistoryViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvHistoryIcon: TextView = itemView.findViewById(R.id.tvHistoryIcon)
        private val tvHistoryTitle: TextView = itemView.findViewById(R.id.tvHistoryTitle)
        private val tvHistoryType: TextView = itemView.findViewById(R.id.tvHistoryType)

        fun bind(entity: SearchHistoryEntity) {
            tvHistoryTitle.text = entity.title
            
            val icon = when (entity.inputType) {
                "video_upload", "video" -> "📹"
                "douyin_url", "url" -> "🔗"
                else -> "🇻🇳"
            }
            tvHistoryIcon.text = icon
            tvHistoryType.text = "${entity.inputType.replace("_", " ").uppercase()} • ${entity.resultCount} kết quả"

            itemView.setOnClickListener {
                onItemClick(entity)
            }
        }
    }
}
