package com.douyin.contentfinder.ui

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.douyin.contentfinder.R
import com.douyin.contentfinder.utils.IntentUtils
import com.google.android.material.bottomnavigation.BottomNavigationView

class MainActivity : AppCompatActivity() {

    private lateinit var bottomNav: BottomNavigationView
    private val searchFragment = SearchFragment()
    private val historyFragment = HistoryFragment()
    private val settingsFragment = SettingsFragment()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        bottomNav = findViewById(R.id.bottomNavigation)
        loadFragment(searchFragment)

        bottomNav.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_search -> loadFragment(searchFragment)
                R.id.nav_history -> loadFragment(historyFragment)
                R.id.nav_settings -> loadFragment(settingsFragment)
            }
            true
        }

        handleShareIntent(intent)
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        handleShareIntent(intent)
    }

    private fun handleShareIntent(intent: Intent?) {
        if (intent?.action == Intent.ACTION_SEND && intent.type == "text/plain") {
            val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)
            val extractedUrl = IntentUtils.extractUrlFromText(sharedText)
            if (!extractedUrl.isNullOrBlank()) {
                bottomNav.selectedItemId = R.id.nav_search
                searchFragment.setSharedUrl(extractedUrl)
            }
        }
    }

    private fun loadFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, fragment)
            .commit()
    }
}
