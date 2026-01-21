<template>
  <div class="value-bets">
    <div class="value-bets-header">
      <h2>Value Bets</h2>
      <div class="filters">
        <select v-model="selectedLeague" class="filter-select" @change="loadOdds">
          <option value="">Все лиги</option>
          <option value="NHL">NHL</option>
          <option value="AHL">AHL</option>
          <option value="LIIGA">Финляндия</option>
          <option value="DEL">Германия</option>
        </select>
        <button class="btn-refresh" @click="loadOdds" :disabled="loading">
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

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Загрузка коэффициентов...</span>
    </div>

    <div v-else-if="error" class="error-state">
      {{ error }}
    </div>

    <div v-else-if="filteredValueBets.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 3v18h18"/>
          <path d="m19 9-5 5-4-4-3 3"/>
        </svg>
      </div>
      <p>Нет валуйных ставок по выбранным критериям</p>
    </div>

    <div v-else class="value-bets-table-container">
      <table class="value-bets-table">
        <thead>
          <tr>
            <th class="th-match">Матч</th>
            <th class="th-league">Лига</th>
            <th class="th-bet">Ставка</th>
            <th class="th-odds">Коэф.</th>
            <th class="th-prob">Вероятность</th>
            <th class="th-fair">Fair Odds</th>
            <th class="th-value">Value</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="bet in filteredValueBets"
            :key="bet.id"
            class="bet-row"
            :class="getValueClass(bet.value)"
          >
            <td class="td-match">
              <div class="match-info">
                <div class="team-with-logo">
                  <img v-if="bet.homeLogo" :src="bet.homeLogo" :alt="bet.homeAbbrev" class="team-logo" />
                  <span class="team-home">{{ bet.homeTeam }}</span>
                </div>
                <span class="vs">—</span>
                <div class="team-with-logo">
                  <img v-if="bet.awayLogo" :src="bet.awayLogo" :alt="bet.awayAbbrev" class="team-logo" />
                  <span class="team-away">{{ bet.awayTeam }}</span>
                </div>
              </div>
              <div class="match-time">{{ formatTime(bet.scheduled) }}</div>
            </td>
            <td class="td-league">{{ bet.league || '—' }}</td>
            <td class="td-bet">{{ bet.betLabel }} ({{ bet.line }})</td>
            <td class="td-odds">{{ bet.odds.toFixed(2) }}</td>
            <td class="td-prob">{{ (bet.probability * 100).toFixed(1) }}%</td>
            <td class="td-fair">{{ bet.fairOdds.toFixed(2) }}</td>
            <td class="td-value" :class="getValueClass(bet.value)">
              <span class="value-badge">+{{ bet.value.toFixed(0) }}%</span>
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
  name: 'ValueBets',
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
      oddsData: [],
      selectedLeague: ''
    }
  },
  computed: {
    valueBets() {
      const bets = []
      const MIN_ODDS = 1.80
      const MIN_VALUE = 50

      for (const event of this.oddsData) {
        if (!event.home_team?.abbrev || !event.away_team?.abbrev) {
          continue
        }

        const homeStats = this.statsCache[event.home_team.abbrev]
        const awayStats = this.statsCache[event.away_team.abbrev]

        const homeTeamInfo = homeStats?.team || {}
        const awayTeamInfo = awayStats?.team || {}

        const homeTeamName = homeTeamInfo.name_ru || homeTeamInfo.name || event.home_team.name
        const awayTeamName = awayTeamInfo.name_ru || awayTeamInfo.name || event.away_team.name

        // Process home team individual totals (ИТБ and ИТМ)
        if (event.odds?.home_total && homeStats?.stats?.home?.individual_totals) {
          for (const total of event.odds.home_total) {
            const thresholdNum = Math.ceil(total.line)
            const threshold = `${thresholdNum}+`
            const statsData = homeStats.stats.home.individual_totals[threshold]

            if (statsData && statsData.percentage != null) {
              const probOver = statsData.percentage / 100
              if (probOver > 0 && total.over >= MIN_ODDS) {
                const fairOdds = 1 / probOver
                const value = ((total.over - fairOdds) / fairOdds) * 100

                if (value >= MIN_VALUE) {
                  bets.push({
                    id: `${event.event_id}-home-it-over-${total.line}`,
                    eventId: event.event_id,
                    homeTeam: homeTeamName,
                    homeAbbrev: event.home_team.abbrev,
                    homeLogo: homeTeamInfo.logo_url,
                    awayTeam: awayTeamName,
                    awayAbbrev: event.away_team.abbrev,
                    awayLogo: awayTeamInfo.logo_url,
                    league: event.league,
                    scheduled: event.scheduled,
                    betType: 'home-it-over',
                    betLabel: `ИТБ ${homeTeamName}`,
                    line: total.line,
                    odds: total.over,
                    probability: probOver,
                    fairOdds: fairOdds,
                    value: value
                  })
                }
              }

              const probUnder = 1 - probOver
              if (probUnder > 0 && total.under >= MIN_ODDS) {
                const fairOdds = 1 / probUnder
                const value = ((total.under - fairOdds) / fairOdds) * 100

                if (value >= MIN_VALUE) {
                  bets.push({
                    id: `${event.event_id}-home-it-under-${total.line}`,
                    eventId: event.event_id,
                    homeTeam: homeTeamName,
                    homeAbbrev: event.home_team.abbrev,
                    homeLogo: homeTeamInfo.logo_url,
                    awayTeam: awayTeamName,
                    awayAbbrev: event.away_team.abbrev,
                    awayLogo: awayTeamInfo.logo_url,
                    league: event.league,
                    scheduled: event.scheduled,
                    betType: 'home-it-under',
                    betLabel: `ИТМ ${homeTeamName}`,
                    line: total.line,
                    odds: total.under,
                    probability: probUnder,
                    fairOdds: fairOdds,
                    value: value
                  })
                }
              }
            }
          }
        }

        // Process away team individual totals
        if (event.odds?.away_total && awayStats?.stats?.away?.individual_totals) {
          for (const total of event.odds.away_total) {
            const thresholdNum = Math.ceil(total.line)
            const threshold = `${thresholdNum}+`
            const statsData = awayStats.stats.away.individual_totals[threshold]

            if (statsData && statsData.percentage != null) {
              const probOver = statsData.percentage / 100
              if (probOver > 0 && total.over >= MIN_ODDS) {
                const fairOdds = 1 / probOver
                const value = ((total.over - fairOdds) / fairOdds) * 100

                if (value >= MIN_VALUE) {
                  bets.push({
                    id: `${event.event_id}-away-it-over-${total.line}`,
                    eventId: event.event_id,
                    homeTeam: homeTeamName,
                    homeAbbrev: event.home_team.abbrev,
                    homeLogo: homeTeamInfo.logo_url,
                    awayTeam: awayTeamName,
                    awayAbbrev: event.away_team.abbrev,
                    awayLogo: awayTeamInfo.logo_url,
                    league: event.league,
                    scheduled: event.scheduled,
                    betType: 'away-it-over',
                    betLabel: `ИТБ ${awayTeamName}`,
                    line: total.line,
                    odds: total.over,
                    probability: probOver,
                    fairOdds: fairOdds,
                    value: value
                  })
                }
              }

              const probUnder = 1 - probOver
              if (probUnder > 0 && total.under >= MIN_ODDS) {
                const fairOdds = 1 / probUnder
                const value = ((total.under - fairOdds) / fairOdds) * 100

                if (value >= MIN_VALUE) {
                  bets.push({
                    id: `${event.event_id}-away-it-under-${total.line}`,
                    eventId: event.event_id,
                    homeTeam: homeTeamName,
                    homeAbbrev: event.home_team.abbrev,
                    homeLogo: homeTeamInfo.logo_url,
                    awayTeam: awayTeamName,
                    awayAbbrev: event.away_team.abbrev,
                    awayLogo: awayTeamInfo.logo_url,
                    league: event.league,
                    scheduled: event.scheduled,
                    betType: 'away-it-under',
                    betLabel: `ИТМ ${awayTeamName}`,
                    line: total.line,
                    odds: total.under,
                    probability: probUnder,
                    fairOdds: fairOdds,
                    value: value
                  })
                }
              }
            }
          }
        }

        // Process match totals (ТБ and ТМ)
        if (event.odds?.match_total && homeStats?.stats?.home?.match_totals) {
          for (const total of event.odds.match_total) {
            const thresholdNum = Math.ceil(total.line)
            const threshold = `${thresholdNum}+`
            const statsData = homeStats.stats.home.match_totals[threshold]

            if (statsData && statsData.percentage != null) {
              const probOver = statsData.percentage / 100
              if (probOver > 0 && total.over >= MIN_ODDS) {
                const fairOdds = 1 / probOver
                const value = ((total.over - fairOdds) / fairOdds) * 100

                if (value >= MIN_VALUE) {
                  bets.push({
                    id: `${event.event_id}-match-total-over-${total.line}`,
                    eventId: event.event_id,
                    homeTeam: homeTeamName,
                    homeAbbrev: event.home_team.abbrev,
                    homeLogo: homeTeamInfo.logo_url,
                    awayTeam: awayTeamName,
                    awayAbbrev: event.away_team.abbrev,
                    awayLogo: awayTeamInfo.logo_url,
                    league: event.league,
                    scheduled: event.scheduled,
                    betType: 'match-total-over',
                    betLabel: 'ТБ',
                    line: total.line,
                    odds: total.over,
                    probability: probOver,
                    fairOdds: fairOdds,
                    value: value
                  })
                }
              }

              const probUnder = 1 - probOver
              if (probUnder > 0 && total.under >= MIN_ODDS) {
                const fairOdds = 1 / probUnder
                const value = ((total.under - fairOdds) / fairOdds) * 100

                if (value >= MIN_VALUE) {
                  bets.push({
                    id: `${event.event_id}-match-total-under-${total.line}`,
                    eventId: event.event_id,
                    homeTeam: homeTeamName,
                    homeAbbrev: event.home_team.abbrev,
                    homeLogo: homeTeamInfo.logo_url,
                    awayTeam: awayTeamName,
                    awayAbbrev: event.away_team.abbrev,
                    awayLogo: awayTeamInfo.logo_url,
                    league: event.league,
                    scheduled: event.scheduled,
                    betType: 'match-total-under',
                    betLabel: 'ТМ',
                    line: total.line,
                    odds: total.under,
                    probability: probUnder,
                    fairOdds: fairOdds,
                    value: value
                  })
                }
              }
            }
          }
        }
      }

      return bets.sort((a, b) => b.value - a.value)
    },
    bestValuePerMatch() {
      const matchBets = {}
      for (const bet of this.valueBets) {
        const matchKey = bet.eventId
        if (!matchBets[matchKey] || matchBets[matchKey].value < bet.value) {
          matchBets[matchKey] = bet
        }
      }
      return Object.values(matchBets).sort((a, b) => b.value - a.value)
    },
    filteredValueBets() {
      return this.bestValuePerMatch
    }
  },
  async mounted() {
    await this.loadOdds()
  },
  methods: {
    async loadOdds() {
      this.loading = true
      this.error = null

      try {
        const response = await hockeyApi.getOdds(this.selectedLeague || null)
        let events = response.events || []

        const detailedPromises = events
          .filter(e => e.home_team?.abbrev && (!e.odds?.home_total?.length || !e.odds?.away_total?.length))
          .slice(0, 10)
          .map(async (event) => {
            try {
              const detailed = await hockeyApi.getEventOdds(event.event_id)
              if (detailed?.odds) {
                event.odds = { ...event.odds, ...detailed.odds }
              }
            } catch (err) {
              // Ignore
            }
          })

        await Promise.all(detailedPromises)
        this.oddsData = events

        await this.loadStatsForOdds()

        // Auto-save predictions after loading
        await this.savePredictionsAuto()
      } catch (err) {
        console.error('Failed to load odds:', err)
        this.error = 'Не удалось загрузить коэффициенты'
      } finally {
        this.loading = false
      }
    },

    async loadStatsForOdds() {
      const teamsToLoad = new Set()

      for (const event of this.oddsData) {
        if (event.home_team?.abbrev && !this.statsCache[event.home_team.abbrev]) {
          teamsToLoad.add({ abbrev: event.home_team.abbrev, league: event.league })
        }
        if (event.away_team?.abbrev && !this.statsCache[event.away_team.abbrev]) {
          teamsToLoad.add({ abbrev: event.away_team.abbrev, league: event.league })
        }
      }

      const promises = Array.from(teamsToLoad).map(async ({ abbrev, league }) => {
        try {
          const stats = await hockeyApi.getTeamStats(abbrev, league || 'NHL', 0)
          this.$emit('stats-loaded', { abbrev, stats })
        } catch (err) {
          console.error(`Failed to load stats for ${abbrev}:`, err)
        }
      })

      await Promise.all(promises)
    },

    async savePredictionsAuto() {
      // Auto-save predictions silently in background
      if (this.filteredValueBets.length === 0) return

      try {
        await fetch('/api/predictions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            predictions: this.filteredValueBets
          })
        })
      } catch (err) {
        console.error('Failed to auto-save predictions:', err)
      }
    },

    formatTime(timestamp) {
      if (!timestamp) return ''
      // Handle both Unix timestamp (seconds) and milliseconds
      const date = new Date(timestamp > 10000000000 ? timestamp : timestamp * 1000)
      const day = date.getDate().toString().padStart(2, '0')
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      return `${day}.${month} ${hours}:${minutes}`
    },

    getValueClass(value) {
      if (value >= 100) return 'value-excellent'
      if (value >= 75) return 'value-great'
      if (value >= 50) return 'value-good'
      return 'value-ok'
    }
  }
}
</script>

<style scoped>
.value-bets {
  padding: 20px;
}

.value-bets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.value-bets-header h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Filter select - styled like main page */
.filter-select {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-light);
  border-radius: 0;
  padding: 9px 36px 9px 16px;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-family: inherit;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%239ca3af' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
}

.filter-select:hover {
  background-color: rgba(255, 255, 255, 0.05);
  border-color: var(--accent-blue);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%233b82f6' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
}

.filter-select:focus {
  outline: none;
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2), inset 0 1px 2px rgba(0, 0, 0, 0.5);
  background-color: rgba(37, 99, 235, 0.05);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%233b82f6' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
}

.filter-select option {
  background: var(--bg-secondary);
  color: var(--text-primary);
  padding: 8px;
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
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
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

.loading-state,
.empty-state,
.error-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.loading-state .spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  margin-bottom: 16px;
  color: var(--text-muted);
}

.error-state {
  color: var(--accent-red);
}

.value-bets-table-container {
  overflow-x: auto;
}

.value-bets-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.value-bets-table th {
  background-color: var(--bg-tertiary);
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  border: 1px solid var(--border-color);
  white-space: nowrap;
}

.value-bets-table td {
  padding: 10px;
  border: 1px solid var(--border-color);
}

.bet-row:hover {
  background-color: var(--bg-hover);
}

.th-match { min-width: 280px; }
.th-league { width: 60px; text-align: center; }
.th-bet { min-width: 180px; }
.th-odds { width: 70px; text-align: center; }
.th-prob { width: 90px; text-align: center; }
.th-fair { width: 80px; text-align: center; }
.th-value { width: 80px; text-align: center; }

.td-league, .td-odds, .td-prob, .td-fair, .td-value {
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

.td-league {
  font-weight: 500;
}

.td-bet {
  font-weight: 500;
}

.td-odds {
  font-weight: 600;
  color: var(--accent-blue);
}

.value-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

.value-ok .value-badge {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.value-good .value-badge {
  background: rgba(76, 175, 80, 0.25);
  color: #4caf50;
}

.value-great .value-badge {
  background: rgba(255, 193, 7, 0.25);
  color: #ffc107;
}

.value-excellent .value-badge {
  background: rgba(255, 87, 34, 0.25);
  color: #ff5722;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@media (max-width: 768px) {
  .value-bets-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filters {
    width: 100%;
    justify-content: center;
  }
}
</style>
