<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="news-modal">
      <div class="modal-header">
        <h3>Новости</h3>
        <button class="modal-close" @click="$emit('close')">×</button>
      </div>

      <div class="team-tabs">
        <button
          :class="['tab-btn', { active: activeTab === 'away' }]"
          @click="activeTab = 'away'"
        >
          {{ awayTeam.name_ru || awayTeam.abbrev }}
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'home' }]"
          @click="activeTab = 'home'"
        >
          {{ homeTeam.name_ru || homeTeam.abbrev }}
        </button>
      </div>

      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <div class="spinner-small"></div>
          <span>Загрузка новостей...</span>
        </div>

        <div v-else-if="error" class="error-state">
          {{ error }}
        </div>

        <div v-else-if="currentNews.length === 0" class="empty-state">
          Нет новостей
        </div>

        <div v-else class="news-list">
          <div
            v-for="(article, index) in currentNews"
            :key="index"
            class="news-item"
            @click="openArticle(article)"
          >
            <div class="news-date" v-if="article.date">
              {{ formatDate(article.date) }}
            </div>
            <div class="news-title">{{ article.title_ru || article.title }}</div>
            <div class="news-content" v-if="article.content_ru || article.content">
              {{ truncateText(article.content_ru || article.content, 200) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { hockeyApi } from '../services/api.js'

export default {
  name: 'NewsModal',
  props: {
    homeTeam: {
      type: Object,
      required: true
    },
    awayTeam: {
      type: Object,
      required: true
    },
    league: {
      type: String,
      default: 'DEL'
    }
  },
  emits: ['close'],
  data() {
    return {
      activeTab: 'away',
      loading: false,
      error: null,
      newsData: {
        home: null,
        away: null
      }
    }
  },
  computed: {
    currentNews() {
      const data = this.newsData[this.activeTab]
      return data?.articles || []
    }
  },
  watch: {
    activeTab: {
      immediate: true,
      handler(tab) {
        if (!this.newsData[tab]) {
          this.loadNews(tab)
        }
      }
    }
  },
  methods: {
    async loadNews(tab) {
      const team = tab === 'home' ? this.homeTeam : this.awayTeam

      this.loading = true
      this.error = null

      try {
        const data = await hockeyApi.getTeamNews(team.abbrev, this.league, 5)
        this.newsData[tab] = data
      } catch (err) {
        console.error('Failed to load news:', err)
        this.error = 'Не удалось загрузить новости'
      } finally {
        this.loading = false
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      try {
        const date = new Date(dateStr)
        return date.toLocaleDateString('ru-RU', {
          day: 'numeric',
          month: 'short'
        })
      } catch {
        return dateStr
      }
    },
    truncateText(text, maxLength) {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength).trim() + '...'
    },
    openArticle(article) {
      if (article.link) {
        window.open(article.link, '_blank', 'noopener,noreferrer')
      }
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.news-modal {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-close:hover {
  color: var(--text-primary);
}

.team-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  flex: 1;
  padding: 12px 16px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.tab-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 20px;
  color: var(--text-muted);
}

.error-state {
  color: var(--accent-red);
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.news-item {
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.news-item:hover {
  border-color: var(--accent-blue);
  background: var(--bg-hover);
}

.news-date {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.news-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 10px;
}

.news-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>
