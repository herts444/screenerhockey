<template>
  <div class="stats-section">
    <div class="match-header">
      <div class="match-team">
        <img
          :src="awayTeam?.logo_url"
          :alt="awayTeam?.name"
          class="match-team-logo"
        >
        <span class="match-team-name">{{ awayTeam?.name_ru || awayTeam?.name }}</span>
        <span style="font-size: 12px; color: var(--text-secondary);">Гости</span>
      </div>
      <span class="match-vs">VS</span>
      <div class="match-team">
        <img
          :src="homeTeam?.logo_url"
          :alt="homeTeam?.name"
          class="match-team-logo"
        >
        <span class="match-team-name">{{ homeTeam?.name_ru || homeTeam?.name }}</span>
        <span style="font-size: 12px; color: var(--text-secondary);">Хозяева</span>
      </div>
    </div>

    <div class="filter-bar">
      <div class="filter-group">
        <span class="filter-label">Последние матчи:</span>
        <select v-model.number="lastN" class="filter-select" @change="$emit('filter-change', lastN)">
          <option :value="10">10</option>
          <option :value="15">15</option>
          <option :value="20">20</option>
          <option :value="25">25</option>
          <option :value="30">30</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>Загрузка статистики...</span>
    </div>

    <div v-else class="stats-grid">
      <StatsTable :team-data="analysis?.away_team || {}" />
      <StatsTable :team-data="analysis?.home_team || {}" />
    </div>
  </div>
</template>

<script>
import StatsTable from './StatsTable.vue'

export default {
  name: 'MatchAnalysis',
  components: {
    StatsTable
  },
  props: {
    analysis: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['filter-change'],
  data() {
    return {
      lastN: 15
    }
  },
  computed: {
    homeTeam() {
      return this.analysis?.home_team?.team
    },
    awayTeam() {
      return this.analysis?.away_team?.team
    }
  }
}
</script>
