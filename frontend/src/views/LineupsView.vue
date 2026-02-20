<template>
  <div class="home-page">
    <header class="header">
      <AppNav />

      <!-- Controls row -->
      <div class="header-row header-row-controls">
        <div class="controls-group">
          <div class="league-switcher">
            <button
              v-for="league in lineupsLeagues"
              :key="league.code"
              :class="['league-btn', { active: lineupsSelectedLeague === league.code }]"
              @click="switchLineupsLeague(league.code)"
            >
              {{ league.name }}
            </button>
          </div>
        </div>

        <div class="controls-group">
          <div class="day-switcher">
            <button
              v-for="day in lineupsDays"
              :key="day.offset"
              :class="['day-btn', { active: lineupsSelectedDay === day.offset }]"
              @click="switchLineupsDay(day.offset)"
            >
              {{ day.label }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="lineups-content">
      <!-- Loading State -->
      <div v-if="lineupsLoading" class="loading">
        <div class="spinner"></div>
        <span>Загрузка матчей и составов...</span>
      </div>

      <!-- No Matches -->
      <div v-else-if="lineupsAllMatches.length === 0" class="empty-state">
        <div class="empty-state-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <p class="empty-state-text">Нет матчей на выбранную дату</p>
        <p class="empty-state-hint">Попробуйте выбрать другую дату или лигу</p>
      </div>

      <!-- All Matches with Lineups -->
      <div v-else class="lineups-all-matches">
        <div v-for="match in lineupsAllMatches" :key="match.id" class="lineup-match-block">
          <!-- Match Header -->
          <div class="lineup-match-header">
            <span class="match-time" v-if="match.timestamp">{{ formatKyivTime(match.timestamp) }}</span>
            <span class="match-title">{{ match.home }} — {{ match.away }}</span>
            <span v-if="match.loading" class="loading-indicator">
              <span class="spinner-small"></span> Загрузка составов...
            </span>
          </div>

          <!-- Lineups Grid -->
          <div v-if="match.lineups" class="lineup-match-grid">
            <!-- Home Team -->
            <div class="lineup-team-block">
              <div class="lineup-team-name home">{{ match.lineups.home?.team || match.home }}</div>
              <div v-if="match.lineups.home?.players" class="lineup-players-tables">
                <table class="lineup-stats-table">
                  <thead>
                    <tr>
                      <th class="col-name">Игрок</th>
                      <th class="col-stat">Матчи</th>
                      <th class="col-stat">Голы</th>
                      <th class="col-stat">Пасы</th>
                      <th class="col-stat col-points">Очки</th>
                      <th class="col-stat col-eff">О/Матч</th>
                      <th class="col-status">Статус</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in match.lineups.home.players.leaders_active" :key="'active-'+p.name" class="row-green">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-ok">заявлен</td>
                    </tr>
                    <tr v-for="p in match.lineups.home.players.leaders_questionable" :key="'quest-'+p.name" class="row-orange">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-quest">{{ p.status || 'под вопросом' }}</td>
                    </tr>
                    <tr v-for="p in match.lineups.home.players.absent.slice(0, 10)" :key="'absent-'+p.name" class="row-red">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-absent">{{ p.status || 'не заявлен' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="match.lineups.home.players.absent?.length > 10" class="more-players">
                  +{{ match.lineups.home.players.absent.length - 10 }} ещё
                </div>
              </div>
              <div v-else class="no-lineup-data">Нет данных</div>
            </div>

            <!-- Away Team -->
            <div class="lineup-team-block">
              <div class="lineup-team-name away">{{ match.lineups.away?.team || match.away }}</div>
              <div v-if="match.lineups.away?.players" class="lineup-players-tables">
                <table class="lineup-stats-table">
                  <thead>
                    <tr>
                      <th class="col-name">Игрок</th>
                      <th class="col-stat">Матчи</th>
                      <th class="col-stat">Голы</th>
                      <th class="col-stat">Пасы</th>
                      <th class="col-stat col-points">Очки</th>
                      <th class="col-stat col-eff">О/Матч</th>
                      <th class="col-status">Статус</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in match.lineups.away.players.leaders_active" :key="'active-'+p.name" class="row-green">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-ok">заявлен</td>
                    </tr>
                    <tr v-for="p in match.lineups.away.players.leaders_questionable" :key="'quest-'+p.name" class="row-orange">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-quest">{{ p.status || 'под вопросом' }}</td>
                    </tr>
                    <tr v-for="p in match.lineups.away.players.absent.slice(0, 10)" :key="'absent-'+p.name" class="row-red">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-absent">{{ p.status || 'не заявлен' }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="match.lineups.away.players.absent?.length > 10" class="more-players">
                  +{{ match.lineups.away.players.absent.length - 10 }} ещё
                </div>
              </div>
              <div v-else class="no-lineup-data">Нет данных</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { lineupsApi } from '../services/api.js'
import AppNav from '../components/AppNav.vue'

export default {
  name: 'LineupsView',
  components: {
    AppNav
  },
  data() {
    return {
      lineupsLeagues: [
        { code: 'NHL', name: 'NHL' },
        { code: 'AHL', name: 'AHL' },
        { code: 'KHL', name: 'КХЛ' },
        { code: 'LIIGA', name: 'Финляндия' },
        { code: 'DEL', name: 'Германия' },
        { code: 'CZECH', name: 'Чехия' },
        { code: 'DENMARK', name: 'Дания' },
        { code: 'AUSTRIA', name: 'Австрия' },
        { code: 'SWISS', name: 'Швейцария' }
      ],
      lineupsSelectedLeague: 'KHL',
      lineupsSelectedDay: 0,
      lineupsAllMatches: [],
      lineupsLoading: false
    }
  },
  computed: {
    lineupsDays() {
      const result = [{ offset: 0, label: 'Сегодня' }]
      const kyivOffset = 2 * 60
      const now = new Date()
      const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000)
      const kyivTime = new Date(utcTime + (kyivOffset * 60000))

      for (let i = 1; i <= 5; i++) {
        const date = new Date(kyivTime)
        date.setDate(kyivTime.getDate() + i)
        const day = date.getDate().toString().padStart(2, '0')
        const month = (date.getMonth() + 1).toString().padStart(2, '0')
        result.push({ offset: i, label: `${day}.${month}` })
      }
      return result
    }
  },
  async mounted() {
    await this.loadLineupsMatches()
  },
  methods: {
    formatKyivTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp * 1000)
      const kyivTime = date.toLocaleString('ru-RU', {
        timeZone: 'Europe/Kiev',
        hour: '2-digit',
        minute: '2-digit'
      })
      return kyivTime
    },

    async loadLineupsMatches() {
      this.lineupsLoading = true
      this.lineupsAllMatches = []
      try {
        const response = await lineupsApi.getMatches(this.lineupsSelectedLeague, this.lineupsSelectedDay)
        if (response.success) {
          const allMatches = []
          for (const [leagueName, matches] of Object.entries(response.leagues || {})) {
            for (const match of matches) {
              allMatches.push({
                ...match,
                leagueName,
                loading: true,
                lineups: null
              })
            }
          }
          this.lineupsAllMatches = allMatches
          this.lineupsLoading = false

          await this.loadAllMatchLineups()
        }
      } catch (error) {
        console.error('Error loading lineups matches:', error)
        this.lineupsLoading = false
      }
    },

    async loadAllMatchLineups() {
      const promises = this.lineupsAllMatches.map((match, idx) =>
        this.loadMatchLineupByIndex(idx)
      )
      await Promise.all(promises)
    },

    async loadMatchLineupByIndex(idx) {
      const match = this.lineupsAllMatches[idx]
      if (!match) return

      try {
        const response = await lineupsApi.getMatchLineup(match.url)
        if (response.success) {
          this.lineupsAllMatches[idx].lineups = {
            home: response.home,
            away: response.away
          }
        }
      } catch (error) {
        console.error('Error loading lineup for', match.home, '-', match.away, ':', error)
      } finally {
        this.lineupsAllMatches[idx].loading = false
      }
    },

    async switchLineupsLeague(code) {
      this.lineupsSelectedLeague = code
      await this.loadLineupsMatches()
    },

    async switchLineupsDay(offset) {
      this.lineupsSelectedDay = offset
      await this.loadLineupsMatches()
    }
  }
}
</script>

<style scoped>
/* Day switcher */
.day-switcher {
  display: flex;
  gap: 2px;
  background-color: rgba(0, 0, 0, 0.4);
  padding: 4px;
  border-radius: 0;
  border: 1px solid var(--border-light);
}

.day-btn {
  padding: 6px 12px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.day-btn:hover {
  color: var(--text-primary);
  background-color: rgba(255, 255, 255, 0.05);
}

.day-btn.active {
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.2) 0%, rgba(37, 99, 235, 0.1) 100%);
  color: var(--accent-blue-light);
}

/* Lineups content */
.lineups-content {
  margin-top: 20px;
}

.empty-state-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 8px;
}

/* Matches layout */
.lineups-all-matches {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 20px;
}

.lineup-match-block {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.lineup-match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);
}

.match-time {
  font-weight: 600;
  font-size: 14px;
  color: var(--accent-blue);
  margin-right: 12px;
  min-width: 45px;
}

.match-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.lineup-match-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--border-color);
}

.lineup-team-block {
  background: var(--bg-primary);
  padding: 12px;
}

.lineup-team-name {
  font-weight: 600;
  font-size: 14px;
  padding: 8px 12px;
  margin-bottom: 12px;
  border-left: 3px solid;
}

.lineup-team-name.home {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.lineup-team-name.away {
  border-color: #ef4444;
  color: #ef4444;
}

/* Lineup Stats Table */
.lineup-players-tables {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lineup-stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.lineup-stats-table thead {
  background: rgba(0, 0, 0, 0.3);
}

.lineup-stats-table th {
  padding: 6px 8px;
  text-align: left;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  font-size: 10px;
  text-transform: uppercase;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.lineup-stats-table td {
  padding: 6px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.lineup-stats-table .col-name {
  color: var(--text-primary);
  font-weight: 500;
}

.lineup-stats-table .col-stat {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  width: 40px;
}

.lineup-stats-table .col-points {
  color: #4fc3f7;
  font-weight: 600;
}

.lineup-stats-table .col-eff {
  color: #81c784;
  font-weight: 600;
}

.lineup-stats-table .col-status {
  text-align: center;
  font-size: 11px;
  min-width: 90px;
}

/* Row colors */
.lineup-stats-table .row-green {
  background: rgba(76, 175, 80, 0.15);
  border-left: 3px solid #4caf50;
}

.lineup-stats-table .row-green:hover {
  background: rgba(76, 175, 80, 0.25);
}

.lineup-stats-table .row-orange {
  background: rgba(30, 64, 175, 0.25);
  border-left: 3px solid #1e40af;
}

.lineup-stats-table .row-orange:hover {
  background: rgba(30, 64, 175, 0.35);
}

.lineup-stats-table .row-red {
  background: rgba(244, 67, 54, 0.15);
  border-left: 3px solid #f44336;
}

.lineup-stats-table .row-red:hover {
  background: rgba(244, 67, 54, 0.25);
}

/* Status cell colors */
.status-ok {
  color: #4caf50;
  font-weight: 500;
}

.status-quest {
  color: #60a5fa;
  font-weight: 500;
}

.status-absent {
  color: #f44336;
  font-weight: 500;
}

.more-players {
  font-size: 11px;
  color: var(--text-muted);
  padding: 4px 8px;
  font-style: italic;
}

.no-lineup-data {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 768px) {
  .lineup-match-grid {
    grid-template-columns: 1fr;
  }
}
</style>
