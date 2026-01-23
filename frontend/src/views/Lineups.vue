<template>
  <div class="lineups-page">
    <!-- Navigation Header -->
    <header class="header">
      <div class="header-row header-row-main">
        <div class="header-brand">
          <div class="logo">
            <span class="logo-text">Hockey Screener</span>
          </div>
          <nav class="main-nav">
            <router-link to="/" class="nav-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3v18h18"/>
                <path d="m19 9-5 5-4-4-3 3"/>
              </svg>
              Статистика
            </router-link>
            <router-link to="/lineups" class="nav-btn nav-btn-lineups">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              Составы
            </router-link>
          </nav>
        </div>
      </div>
    </header>

    <!-- Page Title -->
    <div class="page-header">
      <h1>Составы команд</h1>
      <p class="subtitle">Анализ составов и статус игроков</p>
    </div>

    <!-- League Selector -->
    <div class="league-selector">
      <button
        v-for="league in leagues"
        :key="league.code"
        :class="['league-btn', { active: selectedLeague === league.code }]"
        @click="selectLeague(league.code)"
      >
        {{ league.name_ru }}
      </button>
    </div>

    <!-- Day Selector -->
    <div class="day-selector">
      <button
        v-for="day in days"
        :key="day.offset"
        :class="['day-btn', { active: selectedDay === day.offset }]"
        @click="selectDay(day.offset)"
      >
        {{ day.label }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loadingMatches" class="loading-state">
      <div class="spinner"></div>
      <span>Загрузка матчей...</span>
    </div>

    <!-- Matches List -->
    <div v-else-if="Object.keys(matchesByLeague).length" class="matches-container">
      <div v-for="(matches, leagueName) in matchesByLeague" :key="leagueName" class="league-group">
        <h2 class="league-name">{{ leagueName }}</h2>
        <div class="matches-list">
          <div
            v-for="match in matches"
            :key="match.id"
            :class="['match-card', { selected: selectedMatch?.id === match.id }]"
            @click="selectMatch(match)"
          >
            <div class="match-teams">
              <span class="team home">{{ match.home }}</span>
              <span class="vs">vs</span>
              <span class="team away">{{ match.away }}</span>
            </div>
            <div class="match-action">
              <span v-if="selectedMatch?.id === match.id" class="selected-label">Выбран</span>
              <span v-else class="select-label">Выбрать</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Matches -->
    <div v-else-if="!loadingMatches" class="empty-state">
      <p>Нет матчей на выбранную дату</p>
    </div>

    <!-- Selected Match Lineups -->
    <div v-if="selectedMatch" class="lineups-container">
      <div class="lineups-header">
        <h2>{{ selectedMatch.home }} vs {{ selectedMatch.away }}</h2>
        <button class="close-btn" @click="selectedMatch = null">×</button>
      </div>

      <!-- Team Selector -->
      <div class="team-selector">
        <button
          :class="['team-btn', { active: viewMode === 'home' }]"
          @click="viewMode = 'home'; loadTeamLineup('home')"
        >
          {{ selectedMatch.home }}
        </button>
        <button
          :class="['team-btn', { active: viewMode === 'away' }]"
          @click="viewMode = 'away'; loadTeamLineup('away')"
        >
          {{ selectedMatch.away }}
        </button>
        <button
          :class="['team-btn both', { active: viewMode === 'both' }]"
          @click="viewMode = 'both'; loadBothLineups()"
        >
          Обе команды
        </button>
      </div>

      <!-- Loading Lineup -->
      <div v-if="loadingLineup" class="loading-state">
        <div class="spinner"></div>
        <span>Загрузка состава... (может занять до 30 сек)</span>
      </div>

      <!-- Lineup Tables -->
      <div v-else class="lineups-grid" :class="{ 'two-columns': viewMode === 'both' }">
        <LineupTable
          v-if="(viewMode === 'home' || viewMode === 'both') && homeLineup"
          :team="homeLineup.team"
          :players="homeLineup.players"
          :total-players="homeLineup.total_players"
        />
        <LineupTable
          v-if="(viewMode === 'away' || viewMode === 'both') && awayLineup"
          :team="awayLineup.team"
          :players="awayLineup.players"
          :total-players="awayLineup.total_players"
        />
      </div>
    </div>

    <!-- Legend -->
    <div class="legend">
      <h4>Обозначения:</h4>
      <div class="legend-items">
        <div class="legend-item">
          <span class="legend-color yellow"></span>
          <span>Лидеры в составе (>0.5 очков/матч, играл)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color orange"></span>
          <span>Лидеры под вопросом (>0.5 очков/матч, пропустил последний матч)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color red"></span>
          <span>Отсутствуют (травма/не заявлен)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color gray"></span>
          <span>Остальные игроки</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { lineupsApi } from '../services/api'
import LineupTable from '../components/LineupTable.vue'

export default {
  name: 'Lineups',
  components: {
    LineupTable
  },
  setup() {
    const leagues = ref([
      { code: 'KHL', name: 'KHL', name_ru: 'КХЛ' },
      { code: 'NHL', name: 'NHL', name_ru: 'НХЛ' },
      { code: 'AHL', name: 'AHL', name_ru: 'АХЛ' },
      { code: 'LIIGA', name: 'LIIGA', name_ru: 'Лиига' }
    ])

    const selectedLeague = ref('KHL')
    const selectedDay = ref(0)
    const selectedMatch = ref(null)
    const viewMode = ref('home')

    const matchesByLeague = ref({})
    const loadingMatches = ref(false)
    const loadingLineup = ref(false)

    const homeLineup = ref(null)
    const awayLineup = ref(null)
    const teamUrls = ref({ home: '', away: '' })

    // Generate days array
    const days = computed(() => {
      const result = [{ offset: 0, label: 'Сегодня' }]
      const today = new Date()

      for (let i = 1; i <= 7; i++) {
        const date = new Date(today)
        date.setDate(date.getDate() + i)
        const day = date.getDate().toString().padStart(2, '0')
        const month = (date.getMonth() + 1).toString().padStart(2, '0')
        result.push({ offset: i, label: `${day}/${month}` })
      }

      return result
    })

    const selectLeague = async (code) => {
      selectedLeague.value = code
      selectedMatch.value = null
      homeLineup.value = null
      awayLineup.value = null
      await loadMatches()
    }

    const selectDay = async (offset) => {
      selectedDay.value = offset
      selectedMatch.value = null
      homeLineup.value = null
      awayLineup.value = null
      await loadMatches()
    }

    const loadMatches = async () => {
      loadingMatches.value = true
      matchesByLeague.value = {}

      try {
        const response = await lineupsApi.getMatches(selectedLeague.value, selectedDay.value)

        if (response.success) {
          matchesByLeague.value = response.leagues || {}
        }
      } catch (error) {
        console.error('Error loading matches:', error)
      } finally {
        loadingMatches.value = false
      }
    }

    const selectMatch = async (match) => {
      selectedMatch.value = match
      homeLineup.value = null
      awayLineup.value = null
      viewMode.value = 'home'

      try {
        loadingLineup.value = true
        const response = await lineupsApi.getMatchLineup(match.url)

        if (response.success) {
          homeLineup.value = response.home
          awayLineup.value = response.away
        }
      } catch (error) {
        console.error('Error loading lineups:', error)
      } finally {
        loadingLineup.value = false
      }
    }

    const loadTeamLineup = async (type) => {
      // Already loaded from selectMatch
      if ((type === 'home' && homeLineup.value) || (type === 'away' && awayLineup.value)) {
        return
      }
    }

    const loadBothLineups = async () => {
      // Already loaded from selectMatch
    }

    onMounted(() => {
      loadMatches()
    })

    return {
      leagues,
      selectedLeague,
      selectedDay,
      selectedMatch,
      viewMode,
      days,
      matchesByLeague,
      loadingMatches,
      loadingLineup,
      homeLineup,
      awayLineup,
      selectLeague,
      selectDay,
      selectMatch,
      loadTeamLineup,
      loadBothLineups
    }
  }
}
</script>

<style scoped>
.lineups-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 2rem;
  color: #fff;
}

.subtitle {
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.league-selector {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.league-btn {
  padding: 10px 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1rem;
}

.league-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.league-btn.active {
  background: #4fc3f7;
  border-color: #4fc3f7;
  color: #000;
  font-weight: 600;
}

.day-selector {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.day-btn {
  padding: 8px 14px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.03);
  color: rgba(255, 255, 255, 0.6);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.day-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.day-btn.active {
  background: rgba(79, 195, 247, 0.2);
  border-color: #4fc3f7;
  color: #4fc3f7;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: rgba(255, 255, 255, 0.6);
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #4fc3f7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.matches-container {
  margin-bottom: 32px;
}

.league-group {
  margin-bottom: 24px;
}

.league-name {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.matches-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.match-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: var(--card-bg, #1a1a2e);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.match-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(79, 195, 247, 0.3);
}

.match-card.selected {
  background: rgba(79, 195, 247, 0.15);
  border-color: #4fc3f7;
}

.match-teams {
  display: flex;
  align-items: center;
  gap: 10px;
}

.team {
  color: #fff;
  font-weight: 500;
}

.vs {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.875rem;
}

.match-action {
  font-size: 0.75rem;
}

.select-label {
  color: rgba(255, 255, 255, 0.4);
}

.selected-label {
  color: #4fc3f7;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: rgba(255, 255, 255, 0.5);
}

.lineups-container {
  background: var(--card-bg, #1a1a2e);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
}

.lineups-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.lineups-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #fff;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 50%;
  font-size: 1.25rem;
  cursor: pointer;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 77, 77, 0.3);
}

.team-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.team-btn {
  flex: 1;
  min-width: 120px;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.team-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.team-btn.active {
  background: rgba(79, 195, 247, 0.2);
  border-color: #4fc3f7;
  color: #4fc3f7;
}

.team-btn.both {
  flex: 0.5;
}

.lineups-grid {
  display: grid;
  gap: 20px;
}

.lineups-grid.two-columns {
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
}

.legend {
  background: var(--card-bg, #1a1a2e);
  border-radius: 12px;
  padding: 16px 20px;
}

.legend h4 {
  margin: 0 0 12px 0;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
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
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
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

@media (max-width: 768px) {
  .lineups-page {
    padding: 12px;
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .league-btn {
    padding: 8px 14px;
    font-size: 0.875rem;
  }

  .matches-list {
    grid-template-columns: 1fr;
  }

  .lineups-grid.two-columns {
    grid-template-columns: 1fr;
  }

  .legend-items {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
