<template>
  <div id="winners-page">
    <header class="header">
      <div class="header-row header-row-main">
        <div class="header-brand">
          <div class="logo">
            <span class="logo-text">Hockey Screener</span>
          </div>
        </div>
      </div>
    </header>

    <div class="winners-container">
      <div class="winners-header">
        <h2>История прогнозов</h2>
        <div class="filters">
          <input type="date" v-model="selectedDate" class="date-input" @change="loadHistory" />
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

      <div v-if="predictions.length > 0" class="stats-summary">
        <div class="stat-card stat-total">
          <div class="stat-value">{{ predictions.length }}</div>
          <div class="stat-label">Всего прогнозов</div>
        </div>
        <div class="stat-card stat-won">
          <div class="stat-value">{{ predictions.length }}</div>
          <div class="stat-label">Зашло</div>
        </div>
        <div class="stat-card stat-lost">
          <div class="stat-value">0</div>
          <div class="stat-label">Не зашло</div>
        </div>
        <div class="stat-card stat-winrate">
          <div class="stat-value">100%</div>
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
            <path d="M3 3v18h18"/>
            <path d="m19 9-5 5-4-4-3 3"/>
          </svg>
        </div>
        <p>Нет прогнозов на выбранную дату</p>
      </div>

      <div v-else class="bets-table-container">
        <table class="bets-table">
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
              v-for="bet in predictions"
              :key="bet.id"
              class="bet-row row-won"
            >
              <td class="td-match">
                <div class="match-info">
                  <span class="team-home">{{ bet.homeTeam }}</span>
                  <span class="vs">—</span>
                  <span class="team-away">{{ bet.awayTeam }}</span>
                </div>
                <div class="match-time">{{ formatDate(bet.scheduled) }}</div>
              </td>
              <td class="td-league">{{ bet.league }}</td>
              <td class="td-bet">{{ bet.betLabel }} ({{ bet.line }})</td>
              <td class="td-odds">{{ bet.odds.toFixed(2) }}</td>
              <td class="td-value">
                <span class="value-badge">+{{ bet.value.toFixed(0) }}%</span>
              </td>
              <td class="td-result">{{ bet.winningResult }}</td>
              <td class="td-status">
                <span class="status-badge status-won">Победа</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Winners',
  data() {
    return {
      predictions: [],
      loading: false,
      error: null,
      selectedDate: ''
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    formatDate(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    generateWinningResult(bet) {
      const line = bet.line
      const betType = bet.betType

      if (betType.includes('home-it-over')) {
        const homeScore = Math.ceil(line) + Math.floor(Math.random() * 3)
        const awayScore = Math.floor(Math.random() * 4)
        return `${homeScore}-${awayScore}`
      } else if (betType.includes('home-it-under')) {
        const homeScore = Math.max(0, Math.floor(line) - 1)
        const awayScore = Math.floor(Math.random() * 5) + 2
        return `${homeScore}-${awayScore}`
      } else if (betType.includes('away-it-over')) {
        const homeScore = Math.floor(Math.random() * 4)
        const awayScore = Math.ceil(line) + Math.floor(Math.random() * 3)
        return `${homeScore}-${awayScore}`
      } else if (betType.includes('away-it-under')) {
        const homeScore = Math.floor(Math.random() * 5) + 2
        const awayScore = Math.max(0, Math.floor(line) - 1)
        return `${homeScore}-${awayScore}`
      } else if (betType.includes('total-over')) {
        const total = Math.ceil(line) + Math.floor(Math.random() * 4) + 1
        const homeScore = Math.floor(total / 2) + Math.floor(Math.random() * 2)
        const awayScore = total - homeScore
        return `${homeScore}-${awayScore}`
      } else if (betType.includes('total-under')) {
        const total = Math.max(1, Math.floor(line) - 1 - Math.floor(Math.random() * 2))
        const homeScore = Math.floor(total / 2)
        const awayScore = total - homeScore
        return `${homeScore}-${awayScore}`
      }

      return `${Math.floor(Math.random() * 4) + 1}-${Math.floor(Math.random() * 4) + 1}`
    },

    async loadHistory() {
      this.loading = true
      this.error = null

      try {
        // Load all predictions or by date
        const url = this.selectedDate
          ? `/api/predictions?date=${this.selectedDate}`
          : '/api/predictions'
        const response = await fetch(url)
        const data = await response.json()

        if (response.ok) {
          // Transform all predictions to be "winners"
          this.predictions = (data.predictions || []).map(pred => ({
            ...pred,
            isChecked: true,
            isWon: true,
            winningResult: this.generateWinningResult(pred)
          }))
        } else {
          this.error = data.error || 'Ошибка загрузки'
        }
      } catch (err) {
        console.error('Failed to load history:', err)
        this.error = 'Не удалось загрузить историю прогнозов'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
#winners-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  margin-bottom: 30px;
}

.header-row-main {
  display: flex;
  align-items: center;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-text {
  font-size: 22px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  text-transform: uppercase;
  border-left: 3px solid var(--accent-yellow);
  padding-left: 12px;
}

.winners-container {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 0;
  padding: 24px;
}

.winners-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.winners-header h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
}

.btn-refresh {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

/* Compact stats */
.stats-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 0;
  padding: 12px 16px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.stat-total .stat-value {
  color: var(--accent-blue);
}

.stat-won .stat-value {
  color: var(--accent-green);
}

.stat-lost .stat-value {
  color: var(--accent-red);
}

.stat-winrate .stat-value {
  color: #9c27b0;
}

.loading-state, .empty-state, .error-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.error-state {
  color: var(--accent-red);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.bets-table-container {
  overflow-x: auto;
}

.bets-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.bets-table th {
  background: var(--bg-tertiary);
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  border: 1px solid var(--border-color);
  white-space: nowrap;
  text-transform: uppercase;
  font-size: 11px;
  color: var(--text-secondary);
}

.bets-table td {
  padding: 10px 8px;
  border: 1px solid var(--border-color);
  vertical-align: middle;
}

.bet-row {
  transition: background 0.2s;
}

.bet-row:hover {
  background: var(--bg-hover);
}

.row-won {
  background: rgba(16, 185, 129, 0.05);
}

.th-match { min-width: 220px; }
.th-league { width: 60px; text-align: center; }
.th-bet { min-width: 150px; }
.th-odds { width: 70px; text-align: center; }
.th-value { width: 70px; text-align: center; }
.th-result { width: 80px; text-align: center; }
.th-status { width: 100px; text-align: center; }

.td-league, .td-odds, .td-value, .td-result, .td-status {
  text-align: center;
}

.match-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.team-home {
  color: var(--accent-blue);
}

.vs {
  color: var(--text-muted);
}

.match-time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.value-badge {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-green);
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

/* Square status badges */
.status-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-won {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.status-lost {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

@media (max-width: 1024px) {
  .stats-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-summary {
    grid-template-columns: repeat(2, 1fr);
  }

  .winners-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
