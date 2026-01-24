<template>
  <div class="home-page">
    <header class="header">
      <!-- Row 1: Logo and main navigation -->
      <div class="header-row header-row-main">
        <div class="header-brand">
          <div class="logo">
            <span class="logo-text">Hockey Screener</span>
          </div>
          <nav class="main-nav">
            <button
              :class="['nav-btn', { active: activeTab === 'stats' }]"
              @click="activeTab = 'stats'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3v18h18"/>
                <path d="m19 9-5 5-4-4-3 3"/>
              </svg>
              Статистика
            </button>
            <button
              :class="['nav-btn', 'nav-btn-value', { active: activeTab === 'value' }]"
              @click="activeTab = 'value'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
              Value Bets
            </button>
            <button
              :class="['nav-btn', 'nav-btn-lineups', { active: activeTab === 'lineups' }]"
              @click="activeTab = 'lineups'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              Составы
            </button>
          </nav>
        </div>
      </div>

      <!-- Row 2: Context-specific controls (Stats) -->
      <div v-if="activeTab === 'stats'" class="header-row header-row-controls">
        <div class="controls-group">
          <div class="league-switcher">
            <button
              v-for="league in leagues"
              :key="league.code"
              :class="['league-btn', { active: selectedLeague === league.code }]"
              @click="switchLeague(league.code)"
            >
              {{ league.name }}
            </button>
          </div>

          <div class="control-divider"></div>

          <div class="stats-mode-switcher">
            <button
              :class="['mode-btn', { active: statsMode === 'scored' }]"
              @click="statsMode = 'scored'"
            >
              Забитые
            </button>
            <button
              :class="['mode-btn', { active: statsMode === 'conceded' }]"
              @click="statsMode = 'conceded'"
            >
              Пропущенные
            </button>
          </div>
        </div>

        <div class="controls-group">
          <div class="filter-group">
            <select v-model="selectedDate" class="filter-select" @change="onDateChange">
              <option v-for="date in availableDates" :key="date.value" :value="date.value">
                {{ date.label }}
              </option>
            </select>
          </div>
          <div class="filter-group">
            <select v-model="lastN" class="filter-select" @change="onPeriodChange">
              <option :value="0">Сезон</option>
              <option :value="5">5 матчей</option>
              <option :value="10">10 матчей</option>
              <option :value="15">15 матчей</option>
            </select>
          </div>
          <button class="btn-icon" @click="syncData" :disabled="syncing" title="Обновить данные">
            <svg v-if="!syncing" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
              <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
              <path d="M16 16h5v5"/>
            </svg>
            <span v-else class="spinner-small"></span>
          </button>
        </div>
      </div>

      <!-- Row 2: Context-specific controls (Lineups) -->
      <div v-if="activeTab === 'lineups'" class="header-row header-row-controls">
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

    <!-- Value Bets Tab -->
    <ValueBets
      v-if="activeTab === 'value'"
      :stats-cache="allStatsCache"
      @stats-loaded="onValueBetsStatsLoaded"
    />

    <!-- Lineups Tab -->
    <div v-else-if="activeTab === 'lineups'" class="lineups-content">
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
                    <!-- Leaders Active (Green) - 0.5+ ppg, in roster -->
                    <tr v-for="p in match.lineups.home.players.leaders_active" :key="'active-'+p.name" class="row-green">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-ok">заявлен</td>
                    </tr>
                    <!-- Leaders Questionable (Orange) - 0.5+ ppg, missed last match -->
                    <tr v-for="p in match.lineups.home.players.leaders_questionable" :key="'quest-'+p.name" class="row-orange">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-quest">{{ p.status || 'под вопросом' }}</td>
                    </tr>
                    <!-- Absent (Red) - not in roster -->
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
                    <!-- Leaders Active (Green) - 0.5+ ppg, in roster -->
                    <tr v-for="p in match.lineups.away.players.leaders_active" :key="'active-'+p.name" class="row-green">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-ok">заявлен</td>
                    </tr>
                    <!-- Leaders Questionable (Orange) - 0.5+ ppg, missed last match -->
                    <tr v-for="p in match.lineups.away.players.leaders_questionable" :key="'quest-'+p.name" class="row-orange">
                      <td class="col-name">{{ p.name }}</td>
                      <td class="col-stat">{{ p.matches }}</td>
                      <td class="col-stat">{{ p.goals }}</td>
                      <td class="col-stat">{{ p.assists }}</td>
                      <td class="col-stat col-points">{{ p.points }}</td>
                      <td class="col-stat col-eff">{{ p.efficiency?.toFixed(2) || '0.00' }}</td>
                      <td class="col-status status-quest">{{ p.status || 'под вопросом' }}</td>
                    </tr>
                    <!-- Absent (Red) - not in roster -->
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

    <!-- Stats Tab -->
    <template v-else-if="activeTab === 'stats'">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <span>Загрузка данных...</span>
      </div>

      <div v-else-if="filteredGames.length === 0" class="empty-state">
        <div class="empty-state-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="m4.93 4.93 4.24 4.24"/>
            <path d="m14.83 9.17 4.24-4.24"/>
            <path d="m14.83 14.83 4.24 4.24"/>
            <path d="m9.17 14.83-4.24 4.24"/>
            <circle cx="12" cy="12" r="4"/>
          </svg>
        </div>
        <p class="empty-state-text">
          Нет матчей на выбранную дату.
        </p>
      </div>

      <div v-else class="games-table-container">
      <table class="games-table">
        <thead>
          <tr>
            <th rowspan="2" class="th-match">Матч</th>
            <th colspan="5" class="th-group">ИТ Хозяева {{ statsMode === 'conceded' ? '(проп.)' : '' }}</th>
            <th colspan="5" class="th-group">ИТ Гости {{ statsMode === 'conceded' ? '(проп.)' : '' }}</th>
            <th colspan="4" class="th-group">Тотал (хозяева)</th>
            <th colspan="4" class="th-group">Тотал (гости)</th>
          </tr>
          <tr>
            <!-- Individual totals home -->
            <th class="th-stat">2+</th>
            <th class="th-stat">3+</th>
            <th class="th-stat">4+</th>
            <th class="th-stat">5+</th>
            <th class="th-stat">6+</th>
            <!-- Individual totals away -->
            <th class="th-stat">2+</th>
            <th class="th-stat">3+</th>
            <th class="th-stat">4+</th>
            <th class="th-stat">5+</th>
            <th class="th-stat">6+</th>
            <!-- Match totals home -->
            <th class="th-stat">5+</th>
            <th class="th-stat">6+</th>
            <th class="th-stat">7+</th>
            <th class="th-stat">8+</th>
            <!-- Match totals away -->
            <th class="th-stat">5+</th>
            <th class="th-stat">6+</th>
            <th class="th-stat">7+</th>
            <th class="th-stat">8+</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="game in filteredGamesWithStats" :key="game.game_id" class="game-row">
            <td class="td-match">
              <div class="match-info">
                <img :src="game.home_team.logo_url" :alt="game.home_team.abbrev" class="team-logo">
                <span class="team-home">{{ game.home_team.name_ru || game.home_team.abbrev }}</span>
                <span class="vs-divider">—</span>
                <img :src="game.away_team.logo_url" :alt="game.away_team.abbrev" class="team-logo">
                <span class="team-away">{{ game.away_team.name_ru || game.away_team.abbrev }}</span>
              </div>
            </td>

            <!-- News button (DEL only) -->
            <!-- <td class="td-news" v-if="selectedLeague === 'DEL'">
              <button class="btn-news" @click="openNewsModal(game)" title="Новости команд">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>
                  <path d="M18 14h-8"/>
                  <path d="M15 18h-5"/>
                  <path d="M10 6h8v4h-8V6Z"/>
                </svg>
              </button>
            </td> -->

            <!-- Home team individual totals (home games stats) -->
            <td v-for="t in [2,3,4,5,6]" :key="'home-it-'+t" class="td-stat">
              <StatCell
                :data="getHomeIndividualTotal(game, t, statsMode)"
                @click="showDetails(game, 'home', 'individual', t)"
              />
            </td>

            <!-- Away team individual totals (away games stats) -->
            <td v-for="t in [2,3,4,5,6]" :key="'away-it-'+t" class="td-stat">
              <StatCell
                :data="getAwayIndividualTotal(game, t, statsMode)"
                @click="showDetails(game, 'away', 'individual', t)"
              />
            </td>

            <!-- Home team match totals (home games stats) -->
            <td v-for="t in [5,6,7,8]" :key="'home-mt-'+t" class="td-stat">
              <StatCell
                :data="getHomeMatchTotal(game, t)"
                @click="showDetails(game, 'home', 'total', t)"
              />
            </td>

            <!-- Away team match totals (away games stats) -->
            <td v-for="t in [5,6,7,8]" :key="'away-mt-'+t" class="td-stat">
              <StatCell
                :data="getAwayMatchTotal(game, t)"
                @click="showDetails(game, 'away', 'total', t)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    </template>

    <!-- Details Modal -->
    <div v-if="detailsModal" class="modal-overlay" @click.self="detailsModal = null">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ detailsModal.title }}</h3>
          <button class="modal-close" @click="detailsModal = null">×</button>
        </div>
        <div class="modal-body">
          <div v-if="detailsModal.matches.length === 0" class="no-matches">
            Нет матчей
          </div>
          <div v-else class="matches-list-modal">
            <div v-for="match in detailsModal.matches" :key="match.date + match.opponent" class="match-item-modal">
              <span class="match-date">{{ match.date }}</span>
              <span class="match-opponent">{{ match.opponent }}</span>
              <span class="match-score">{{ match.score }}</span>
              <span v-if="match.total" class="match-total">({{ match.total }})</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-toast">
      {{ error }}
      <button @click="error = null">×</button>
    </div>

    <!-- News Modal -->
    <NewsModal
      v-if="newsModal"
      :home-team="newsModal.homeTeam"
      :away-team="newsModal.awayTeam"
      :league="selectedLeague"
      @close="newsModal = null"
    />
  </div>
</template>

<script>
import { hockeyApi, lineupsApi } from '../services/api.js'
import StatCell from '../components/StatCell.vue'
import NewsModal from '../components/NewsModal.vue'
import ValueBets from '../components/ValueBets.vue'

export default {
  name: 'App',
  components: {
    StatCell,
    NewsModal,
    ValueBets
  },
  data() {
    return {
      // Per-league cached data
      leagueData: {
        NHL: { games: [], statsCache: {}, loaded: false },
        AHL: { games: [], statsCache: {}, loaded: false },
        KHL: { games: [], statsCache: {}, loaded: false },
        LIIGA: { games: [], statsCache: {}, loaded: false },
        DEL: { games: [], statsCache: {}, loaded: false },
        CZECH: { games: [], statsCache: {}, loaded: false },
        DENMARK: { games: [], statsCache: {}, loaded: false },
        AUSTRIA: { games: [], statsCache: {}, loaded: false }
      },
      status: null,
      loading: false,
      syncing: false,
      error: null,
      lastN: 0,
      detailsModal: null,
      newsModal: null,
      selectedDate: null,
      selectedLeague: 'NHL',
      statsMode: 'scored', // 'scored' or 'conceded'
      activeTab: 'stats', // 'stats' or 'value'
      leagues: [
        { code: 'NHL', name: 'NHL', name_ru: 'НХЛ' },
        { code: 'AHL', name: 'AHL', name_ru: 'АХЛ' },
        { code: 'KHL', name: 'КХЛ', name_ru: 'КХЛ' },
        { code: 'LIIGA', name: 'Финляндия', name_ru: 'Финляндия' },
        { code: 'DEL', name: 'Германия', name_ru: 'Германия' },
        { code: 'CZECH', name: 'Чехия', name_ru: 'Чехия' },
        { code: 'DENMARK', name: 'Дания', name_ru: 'Дания' },
        { code: 'AUSTRIA', name: 'Австрия', name_ru: 'Австрия' }
      ],
      // Lineups tab data - same leagues as stats tab
      lineupsLeagues: [
        { code: 'NHL', name: 'NHL' },
        { code: 'AHL', name: 'AHL' },
        { code: 'KHL', name: 'КХЛ' },
        { code: 'LIIGA', name: 'Финляндия' },
        { code: 'DEL', name: 'Германия' },
        { code: 'CZECH', name: 'Чехия' },
        { code: 'DENMARK', name: 'Дания' },
        { code: 'AUSTRIA', name: 'Австрия' }
      ],
      lineupsSelectedLeague: 'KHL',
      lineupsSelectedDay: 0,
      lineupsMatches: {},
      lineupsAllMatches: [], // Array of matches with lineups data
      lineupsLoading: false
    }
  },
  computed: {
    // Current league data shortcuts
    selectedLeagueName() {
      const league = this.leagues.find(l => l.code === this.selectedLeague)
      return league?.name || this.selectedLeague
    },
    games() {
      return this.leagueData[this.selectedLeague]?.games || []
    },
    statsCache() {
      return this.leagueData[this.selectedLeague]?.statsCache || {}
    },
    availableDates() {
      const dates = []
      // Use Kyiv timezone (UTC+2) for date calculations to match backend
      const kyivOffset = 2 * 60 // Kyiv is UTC+2
      const now = new Date()
      const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000)
      const kyivTime = new Date(utcTime + (kyivOffset * 60000))

      for (let i = 0; i <= 7; i++) {
        const date = new Date(kyivTime)
        date.setDate(kyivTime.getDate() + i)
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const value = `${year}-${month}-${day}`
        const dayNames = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
        const dayName = dayNames[date.getDay()]
        const label = `${dayName}, ${day}.${month}`
        dates.push({ value, label })
      }
      return dates
    },
    filteredGames() {
      if (!this.selectedDate) return []
      return this.games.filter(game => {
        if (!game.date_iso) return false
        const gameDate = game.date_iso.split('T')[0]
        return gameDate === this.selectedDate
      })
    },
    filteredGamesWithStats() {
      return this.filteredGames.map(game => ({
        ...game,
        homeStats: this.statsCache[game.home_team.abbrev],
        awayStats: this.statsCache[game.away_team.abbrev]
      }))
    },
    allStatsCache() {
      // Combine stats cache from all leagues for ValueBets
      const combined = {}
      for (const league of Object.keys(this.leagueData)) {
        Object.assign(combined, this.leagueData[league].statsCache)
      }
      return combined
    },
    lineupsDays() {
      const result = [{ offset: 0, label: 'Сегодня' }]
      // Use Kyiv timezone (UTC+2)
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
    // По умолчанию выбираем сегодня по Киевскому времени
    const kyivOffset = 2 * 60 // Kyiv is UTC+2
    const now = new Date()
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000)
    const kyivTime = new Date(utcTime + (kyivOffset * 60000))
    const year = kyivTime.getFullYear()
    const month = String(kyivTime.getMonth() + 1).padStart(2, '0')
    const day = String(kyivTime.getDate()).padStart(2, '0')
    this.selectedDate = `${year}-${month}-${day}`

    await this.loadStatus()
    await this.loadGames()

    // Если нет матчей на выбранную дату, выбираем первую дату с матчами
    this.selectFirstAvailableDate()
  },
  methods: {
    async loadStatus() {
      try {
        this.status = await hockeyApi.getStatus(this.selectedLeague)
      } catch (err) {
        console.error('Failed to load status:', err)
      }
    },

    async loadGames() {
      const league = this.selectedLeague

      // Check if already loaded in frontend cache
      if (this.leagueData[league].loaded && this.leagueData[league].games.length > 0) {
        return
      }

      this.loading = true
      try {
        const response = await hockeyApi.getUpcomingGames(league, 7)
        this.leagueData[league].games = response.games || []
        await this.loadAllStats()
        this.leagueData[league].loaded = true
      } catch (err) {
        console.error('Failed to load games:', err)
        this.error = 'Не удалось загрузить расписание матчей'
      } finally {
        this.loading = false
      }
    },

    async loadAllStats() {
      const league = this.selectedLeague
      const games = this.leagueData[league].games
      const statsCache = this.leagueData[league].statsCache

      const teams = new Set()
      games.forEach(game => {
        teams.add(game.home_team.abbrev)
        teams.add(game.away_team.abbrev)
      })

      // Only load stats for teams not already cached
      const teamsToLoad = Array.from(teams).filter(abbrev => !statsCache[abbrev])

      const promises = teamsToLoad.map(async (abbrev) => {
        try {
          const stats = await hockeyApi.getTeamStats(abbrev, league, this.lastN)
          statsCache[abbrev] = stats
        } catch (err) {
          console.error(`Failed to load stats for ${abbrev}:`, err)
        }
      })

      await Promise.all(promises)
      // Force reactivity update
      this.leagueData[league].statsCache = { ...statsCache }
    },

    async loadFilteredStats() {
      const league = this.selectedLeague
      const statsCache = this.leagueData[league].statsCache

      const teams = new Set()
      this.filteredGames.forEach(game => {
        teams.add(game.home_team.abbrev)
        teams.add(game.away_team.abbrev)
      })

      // Only load stats for teams not already cached
      const teamsToLoad = Array.from(teams).filter(abbrev => !statsCache[abbrev])

      const promises = teamsToLoad.map(async (abbrev) => {
        try {
          const stats = await hockeyApi.getTeamStats(abbrev, league, this.lastN)
          statsCache[abbrev] = stats
        } catch (err) {
          console.error(`Failed to load stats for ${abbrev}:`, err)
        }
      })

      await Promise.all(promises)
      this.leagueData[league].statsCache = { ...statsCache }
    },

    async onDateChange() {
      await this.loadFilteredStats()
    },

    async onPeriodChange() {
      // Clear stats cache for current league and reload
      const league = this.selectedLeague
      this.leagueData[league].statsCache = {}
      this.loading = true
      try {
        await this.loadAllStats()
      } finally {
        this.loading = false
      }
    },

    async switchLeague(league) {
      if (this.selectedLeague === league) return
      this.selectedLeague = league

      // Load data for this league if not cached
      if (!this.leagueData[league].loaded) {
        await this.loadStatus()
        await this.loadGames()
      }

      // Выбираем первую доступную дату с матчами для новой лиги
      this.selectFirstAvailableDate()
    },

    selectFirstAvailableDate() {
      // Если на текущую дату есть матчи — оставляем
      if (this.filteredGames.length > 0) return

      // Иначе ищем первую дату с матчами
      for (const dateOption of this.availableDates) {
        const gamesOnDate = this.games.filter(game => {
          if (!game.date_iso) return false
          return game.date_iso.split('T')[0] === dateOption.value
        })
        if (gamesOnDate.length > 0) {
          this.selectedDate = dateOption.value
          return
        }
      }
    },

    getAwayIndividualTotal(game, threshold, mode = 'scored') {
      const stats = this.statsCache[game.away_team.abbrev]
      const statType = mode === 'conceded' ? 'individual_conceded' : 'individual_totals'
      const data = stats?.stats?.away?.[statType]?.[`${threshold}+`]
      if (!data) return null
      return { ...data, total_matches: stats?.stats?.away?.total_matches }
    },

    getHomeIndividualTotal(game, threshold, mode = 'scored') {
      const stats = this.statsCache[game.home_team.abbrev]
      const statType = mode === 'conceded' ? 'individual_conceded' : 'individual_totals'
      const data = stats?.stats?.home?.[statType]?.[`${threshold}+`]
      if (!data) return null
      return { ...data, total_matches: stats?.stats?.home?.total_matches }
    },

    getAwayMatchTotal(game, threshold) {
      const stats = this.statsCache[game.away_team.abbrev]
      const data = stats?.stats?.away?.match_totals?.[`${threshold}+`]
      if (!data) return null
      return { ...data, total_matches: stats?.stats?.away?.total_matches }
    },

    getHomeMatchTotal(game, threshold) {
      const stats = this.statsCache[game.home_team.abbrev]
      const data = stats?.stats?.home?.match_totals?.[`${threshold}+`]
      if (!data) return null
      return { ...data, total_matches: stats?.stats?.home?.total_matches }
    },

    showDetails(game, location, type, threshold) {
      let data, teamName
      const statType = type === 'individual'
        ? (this.statsMode === 'conceded' ? 'individual_conceded' : 'individual_totals')
        : 'match_totals'

      if (location === 'away') {
        teamName = game.away_team.name_ru || game.away_team.abbrev
        const stats = this.statsCache[game.away_team.abbrev]
        data = stats?.stats?.away?.[statType]?.[`${threshold}+`]
      } else {
        teamName = game.home_team.name_ru || game.home_team.abbrev
        const stats = this.statsCache[game.home_team.abbrev]
        data = stats?.stats?.home?.[statType]?.[`${threshold}+`]
      }

      const typeLabel = type === 'individual'
        ? (this.statsMode === 'conceded' ? 'ИТ проп.' : 'ИТ')
        : 'Тотал'
      const locationLabel = location === 'away' ? 'выезд' : 'дом'

      this.detailsModal = {
        title: `${teamName} — ${typeLabel} ${threshold}+ (${locationLabel})`,
        matches: data?.matches || []
      }
    },

    openNewsModal(game) {
      this.newsModal = {
        homeTeam: game.home_team,
        awayTeam: game.away_team
      }
    },

    async syncData() {
      this.syncing = true
      this.error = null
      const league = this.selectedLeague

      try {
        // Sync triggers full refresh on backend
        await hockeyApi.syncGames(league)

        // Clear frontend cache for this league
        this.leagueData[league].loaded = false
        this.leagueData[league].games = []
        this.leagueData[league].statsCache = {}

        // Reload
        await this.loadStatus()
        await this.loadGames()
      } catch (err) {
        console.error('Failed to sync data:', err)
        this.error = 'Ошибка при обновлении данных'
      } finally {
        this.syncing = false
      }
    },

    onValueBetsStatsLoaded({ abbrev, stats }) {
      // Store stats loaded by ValueBets component in the global cache
      // Find which league this team belongs to
      for (const league of Object.keys(this.leagueData)) {
        this.leagueData[league].statsCache[abbrev] = stats
      }
    },

    // Lineups methods
    async loadLineupsMatches() {
      this.lineupsLoading = true
      this.lineupsAllMatches = []
      try {
        const response = await lineupsApi.getMatches(this.lineupsSelectedLeague, this.lineupsSelectedDay)
        if (response.success) {
          // Flatten all matches from all leagues into a single array
          const allMatches = []
          for (const [leagueName, matches] of Object.entries(response.leagues || {})) {
            for (const match of matches) {
              allMatches.push({
                ...match,
                leagueName,
                loading: true, // Start with loading=true since we'll load lineups automatically
                lineups: null
              })
            }
          }
          this.lineupsAllMatches = allMatches
          this.lineupsLoading = false

          // Auto-load lineups for all matches in parallel
          await this.loadAllMatchLineups()
        }
      } catch (error) {
        console.error('Error loading lineups matches:', error)
        this.lineupsLoading = false
      }
    },

    // Load lineups for all matches in parallel
    async loadAllMatchLineups() {
      const promises = this.lineupsAllMatches.map((match, idx) =>
        this.loadMatchLineupByIndex(idx)
      )
      await Promise.all(promises)
    },

    // Load lineup for a specific match by index
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
    },

    async loadMatchLineup(match) {
      // Find the match in our array and load by index
      const idx = this.lineupsAllMatches.findIndex(m => m.id === match.id)
      if (idx === -1) return
      await this.loadMatchLineupByIndex(idx)
    }
  },

  watch: {
    activeTab(newTab) {
      if (newTab === 'lineups' && this.lineupsAllMatches.length === 0) {
        this.loadLineupsMatches()
      }
    }
  }
}
</script>

<style scoped>
/* === ТАБЛИЦА МАТЧЕЙ - РАБОЧИЕ СТИЛИ === */
.games-table-container {
  overflow-x: auto;
  margin-top: 20px;
}

.games-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.games-table th {
  background-color: var(--bg-tertiary);
  padding: 10px 6px;
  text-align: center;
  font-weight: 600;
  border: 1px solid var(--border-color);
  white-space: nowrap;
}

.th-group {
  background-color: var(--bg-secondary) !important;
  font-size: 12px;
  color: var(--text-secondary);
}

.th-match {
  text-align: left;
  min-width: 380px;
}

.th-stat {
  width: 50px;
  font-size: 11px;
}

.game-row:hover {
  background-color: var(--bg-hover);
}

.games-table td {
  padding: 8px 6px;
  border: 1px solid var(--border-color);
}

.td-match {
  font-weight: 500;
}

.match-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.team-logo {
  width: 24px;
  height: 24px;
  object-fit: contain;
  flex-shrink: 0;
}

.team-away {
  color: var(--text-primary);
  width: 140px;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vs-divider {
  color: var(--text-muted);
  font-size: 14px;
  margin: 0 8px;
  flex-shrink: 0;
}

.team-home {
  color: var(--accent-blue);
  width: 140px;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.td-stat {
  text-align: center;
  padding: 4px !important;
}

.th-news {
  width: 40px;
}

.td-news {
  text-align: center;
  padding: 4px !important;
}

.btn-news {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-news:hover {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

/* Modal */
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

.modal-content {
  background: var(--gradient-premium);
  border: 1px solid var(--border-light);
  border-radius: 0;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-lg), 0 0 40px rgba(0, 0, 0, 0.6);
  position: relative;
}

.modal-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-blue);
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
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 24px;
  cursor: pointer;
}

.modal-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 16px 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.matches-list-modal {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.match-item-modal {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0;
  border-left: 2px solid transparent;
  transition: all 0.2s;
}

.match-item-modal:hover {
  background: rgba(37, 99, 235, 0.1);
  border-left-color: var(--accent-blue);
  transform: translateX(2px);
}

.match-date {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 80px;
}

.match-opponent {
  flex: 1;
  font-weight: 500;
}

.match-score {
  font-weight: 600;
  color: var(--accent-blue);
}

.match-total {
  font-size: 12px;
  color: var(--text-secondary);
}

.no-matches {
  text-align: center;
  color: var(--text-muted);
  padding: 20px;
}

.error-toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: var(--accent-red);
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1000;
}

.error-toast button {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
}

/* Stats mode switcher - same style as league-switcher */
.stats-mode-switcher {
  display: flex;
  gap: 2px;
  background-color: rgba(0, 0, 0, 0.4);
  padding: 4px;
  border-radius: 0;
  border: 1px solid var(--border-light);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
}

.mode-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
}

.mode-btn::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-blue);
  transform: scaleX(0);
  transition: transform 0.25s;
}

.mode-btn:hover {
  color: var(--text-primary);
  background-color: rgba(255, 255, 255, 0.05);
}

.mode-btn.active {
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.2) 0%, rgba(37, 99, 235, 0.1) 100%);
  color: var(--accent-blue-light);
  border-left: 2px solid var(--accent-blue);
  border-right: 2px solid var(--accent-blue);
}

.mode-btn.active::after {
  transform: scaleX(1);
}

/* Day switcher for lineups */
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

.lineups-legend {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 14px 18px;
  margin-top: 20px;
}

.lineups-legend h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-color {
  width: 14px;
  height: 14px;
}

.legend-color.yellow {
  background: #ffd700;
}

.legend-color.orange {
  background: #ffa500;
}

.legend-color.red {
  background: #ff4d4d;
}

.legend-color.gray {
  background: rgba(255, 255, 255, 0.3);
}

.empty-state-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 8px;
}

/* New Lineups Styles */
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

.match-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.btn-load-lineup {
  padding: 6px 14px;
  background: var(--accent-blue);
  border: none;
  color: white;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-load-lineup:hover {
  background: #1d4ed8;
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

.lineup-players-compact {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.player-category {
  padding: 8px;
  border-radius: 4px;
}

.player-category.yellow {
  background: rgba(255, 215, 0, 0.1);
  border-left: 3px solid #ffd700;
}

.player-category.orange {
  background: rgba(255, 165, 0, 0.1);
  border-left: 3px solid #ffa500;
}

.player-category.red {
  background: rgba(255, 77, 77, 0.1);
  border-left: 3px solid #ff4d4d;
}

.category-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
  color: var(--text-secondary);
}

.player-row-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 3px;
}

.player-row-compact.yellow {
  background: rgba(255, 215, 0, 0.15);
}

.player-row-compact.orange {
  background: rgba(255, 165, 0, 0.15);
}

.player-row-compact.red {
  background: rgba(255, 77, 77, 0.15);
}

.player-row-compact .player-name {
  flex: 1;
  font-weight: 500;
  color: var(--text-primary);
  min-width: 120px;
}

.player-row-compact .player-status {
  font-size: 10px;
  color: var(--text-muted);
  background: rgba(0,0,0,0.2);
  padding: 2px 6px;
  border-radius: 3px;
}

.player-row-compact .player-stats-compact {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.player-row-compact .player-stats-compact b {
  color: var(--accent-blue);
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

/* Row colors by player status */
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

@media (max-width: 768px) {
  .lineup-match-grid {
    grid-template-columns: 1fr;
  }

  .player-row-compact {
    flex-wrap: wrap;
  }

  .player-row-compact .player-name {
    min-width: 100%;
  }
}

</style>
