<template>
  <div class="prediction-history">
    <div class="history-header">
      <h2>История прогнозов</h2>
      <div class="controls">
        <input
          type="date"
          v-model="selectedDate"
          class="date-input"
          @change="loadHistory"
        />
        <button class="btn-refresh" @click="loadHistory" :disabled="loading">
          <svg v-if="!loading" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 16h5v5"/>
          </svg>
          <span v-else class="spinner-small"></span>
        </button>
      </div>
    </div>
    <div v-if="stats" class="auto-check-info">
      Автоматическая проверка: каждый час (через 5+ часов после начала матча)
    </div>

    <div v-if="stats" class="stats-summary">
      <div class="stat-card stat-total">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">Всего прогнозов</div>
      </div>
      <div class="stat-card stat-won">
        <div class="stat-value">{{ stats.won }}</div>
        <div class="stat-label">Зашло</div>
      </div>
      <div class="stat-card stat-lost">
        <div class="stat-value">{{ stats.lost }}</div>
        <div class="stat-label">Не зашло</div>
      </div>
      <div class="stat-card stat-winrate">
        <div class="stat-value">{{ stats.winRate }}%</div>
        <div class="stat-label">Процент попаданий</div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Загрузка истории...</span>
    </div>

    <div v-else-if="error" class="error-state">
      {{ error }}
    </div>

    <div v-else-if="predictions.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
          <path d="M3 3v5h5"/>
          <path d="M12 7v5l4 2"/>
        </svg>
      </div>
      <p>Нет прогнозов на выбранную дату</p>
    </div>

    <div v-else class="history-table-container">
      <table class="history-table">
        <thead>
          <tr>
            <th class="th-match">Матч</th>
            <th class="th-league">Лига</th>
            <th class="th-bet">Ставка</th>
            <th class="th-odds">Коэф.</th>
            <th class="th-value">Value</th>
            <th class="th-result">Результат</th>
            <th class="th-status">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="pred in predictions"
            :key="pred.id"
            class="bet-row"
            :class="getRowClass(pred)"
          >
            <td class="td-match">
              <div class="match-info">
                <div class="team-with-logo">
                  <img v-if="getTeamLogo(pred.homeAbbrev)" :src="getTeamLogo(pred.homeAbbrev)" :alt="pred.homeAbbrev" class="team-logo" />
                  <span class="team-home">{{ pred.homeTeam }}</span>
                </div>
                <span class="vs">—</span>
                <div class="team-with-logo">
                  <img v-if="getTeamLogo(pred.awayAbbrev)" :src="getTeamLogo(pred.awayAbbrev)" :alt="pred.awayAbbrev" class="team-logo" />
                  <span class="team-away">{{ pred.awayTeam }}</span>
                </div>
              </div>
              <div class="match-time">{{ formatTime(pred.scheduled) }}</div>
            </td>
            <td class="td-league">{{ pred.league || '—' }}</td>
            <td class="td-bet">{{ pred.betLabel }} ({{ pred.line }})</td>
            <td class="td-odds">{{ pred.odds.toFixed(2) }}</td>
            <td class="td-value">
              <span class="value-badge">+{{ pred.value.toFixed(0) }}%</span>
            </td>
            <td class="td-result">
              {{ pred.actualResult || '—' }}
            </td>
            <td class="td-status">
              <span v-if="!pred.isChecked" class="status-badge status-pending">Ожидание</span>
              <span v-else-if="pred.isWon" class="status-badge status-won">✓ Зашло</span>
              <span v-else class="status-badge status-lost">✗ Не зашло</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { hockeyApi } from '../services/api.js'

export default {
  name: 'PredictionHistory',
  props: {
    statsCache: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      predictions: [],
      selectedDate: this.getYesterday()
    }
  },
  computed: {
    stats() {
      if (this.predictions.length === 0) return null

      const checked = this.predictions.filter(p => p.isChecked)
      const won = checked.filter(p => p.isWon).length
      const lost = checked.length - won

      return {
        total: this.predictions.length,
        won,
        lost,
        winRate: checked.length > 0 ? Math.round((won / checked.length) * 100) : 0
      }
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    getYesterday() {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      return yesterday.toISOString().split('T')[0]
    },

    async loadHistory() {
      this.loading = true
      this.error = null

      try {
        const response = await fetch(`/api/predictions?date=${this.selectedDate}`)
        const data = await response.json()

        if (response.ok) {
          this.predictions = data.predictions || []
        } else {
          this.error = data.error || 'Ошибка загрузки истории'
        }
      } catch (err) {
        console.error('Failed to load history:', err)
        this.error = 'Не удалось загрузить историю прогнозов'
      } finally {
        this.loading = false
      }
    },

    getTeamLogo(abbrev) {
      const stats = this.statsCache[abbrev]
      return stats?.team?.logo_url
    },

    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const day = date.getDate().toString().padStart(2, '0')
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      return `${day}.${month} ${hours}:${minutes}`
    },

    getRowClass(pred) {
      if (!pred.isChecked) return ''
      return pred.isWon ? 'row-won' : 'row-lost'
    }
  }
}
</script>

<style scoped>
.prediction-history {
  padding: 20px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.history-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auto-check-info {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  border-left: 3px solid var(--accent-blue);
}

.stats-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-total .stat-value { color: var(--accent-blue); }
.stat-won .stat-value { color: #4caf50; }
.stat-lost .stat-value { color: #f44336; }
.stat-winrate .stat-value { color: #9c27b0; }

.loading-state, .empty-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  margin-bottom: 16px;
  color: var(--text-muted);
}

.history-table-container {
  overflow-x: auto;
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  background: var(--bg-tertiary);
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.history-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.bet-row:hover {
  background: var(--bg-hover);
}

.row-won {
  background: rgba(76, 175, 80, 0.08);
}

.row-lost {
  background: rgba(244, 67, 54, 0.08);
}

.th-match { min-width: 280px; }
.th-league { width: 60px; text-align: center; }
.th-bet { min-width: 180px; }
.th-odds { width: 70px; text-align: center; }
.th-value { width: 80px; text-align: center; }
.th-result { width: 80px; text-align: center; }
.th-status { width: 120px; text-align: center; }

.td-league, .td-odds, .td-value, .td-result, .td-status {
  text-align: center;
}

.match-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  flex-wrap: wrap;
}

.team-with-logo {
  display: flex;
  align-items: center;
  gap: 6px;
}

.team-logo {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.team-home {
  color: var(--accent-blue);
}

.vs {
  color: var(--text-muted);
}

.team-away {
  color: var(--text-primary);
}

.match-time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.value-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
  font-size: 12px;
}

.status-pending {
  background: rgba(158, 158, 158, 0.15);
  color: #9e9e9e;
}

.status-won {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.status-lost {
  background: rgba(244, 67, 54, 0.15);
  color: #f44336;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1024px) {
  .stats-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .controls {
    flex-wrap: wrap;
  }

  .stats-summary {
    grid-template-columns: 1fr;
  }
}
</style>
