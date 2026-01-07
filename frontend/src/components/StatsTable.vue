<template>
  <div class="team-stats">
    <div class="team-stats-header">
      {{ teamData.team?.name_ru || teamData.team?.name || 'Команда' }}
    </div>

    <!-- Individual Totals -->
    <div class="section-label">Индивидуальный тотал (шайбы команды)</div>
    <table class="stats-table">
      <thead>
        <tr>
          <th>Тотал</th>
          <th>Дом</th>
          <th>Выезд</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="threshold in individualThresholds" :key="'it-' + threshold">
          <td class="stat-label">{{ threshold }}+ шайб</td>
          <td>
            <div
              class="stat-value"
              @click="toggleDetails('home', 'individual', threshold)"
            >
              <span class="stat-count">{{ getStatCount('home', 'individual_totals', threshold + '+') }}</span>
              <span
                class="stat-percent"
                :class="getProbClass(getStatPercent('home', 'individual_totals', threshold + '+'))"
              >
                ({{ getStatPercent('home', 'individual_totals', threshold + '+') }}%)
              </span>
            </div>
            <div
              v-if="isExpanded('home', 'individual', threshold)"
              class="matches-list"
            >
              <div
                v-for="match in getMatches('home', 'individual_totals', threshold + '+')"
                :key="match.date + match.opponent"
                class="match-item"
              >
                <span class="match-item-date">{{ match.date }}</span>
                <span class="match-item-opponent">{{ match.opponent }}</span>
                <span class="match-item-score">{{ match.score }}</span>
              </div>
              <div v-if="!getMatches('home', 'individual_totals', threshold + '+').length" class="match-item">
                Нет матчей
              </div>
            </div>
          </td>
          <td>
            <div
              class="stat-value"
              @click="toggleDetails('away', 'individual', threshold)"
            >
              <span class="stat-count">{{ getStatCount('away', 'individual_totals', threshold + '+') }}</span>
              <span
                class="stat-percent"
                :class="getProbClass(getStatPercent('away', 'individual_totals', threshold + '+'))"
              >
                ({{ getStatPercent('away', 'individual_totals', threshold + '+') }}%)
              </span>
            </div>
            <div
              v-if="isExpanded('away', 'individual', threshold)"
              class="matches-list"
            >
              <div
                v-for="match in getMatches('away', 'individual_totals', threshold + '+')"
                :key="match.date + match.opponent"
                class="match-item"
              >
                <span class="match-item-date">{{ match.date }}</span>
                <span class="match-item-opponent">{{ match.opponent }}</span>
                <span class="match-item-score">{{ match.score }}</span>
              </div>
              <div v-if="!getMatches('away', 'individual_totals', threshold + '+').length" class="match-item">
                Нет матчей
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="stats-divider"></div>

    <!-- Match Totals -->
    <div class="section-label">Общий тотал матча</div>
    <table class="stats-table">
      <thead>
        <tr>
          <th>Тотал</th>
          <th>Дом</th>
          <th>Выезд</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="threshold in totalThresholds" :key="'mt-' + threshold">
          <td class="stat-label">{{ threshold }}+ голов</td>
          <td>
            <div
              class="stat-value"
              @click="toggleDetails('home', 'total', threshold)"
            >
              <span class="stat-count">{{ getStatCount('home', 'match_totals', threshold + '+') }}</span>
              <span
                class="stat-percent"
                :class="getProbClass(getStatPercent('home', 'match_totals', threshold + '+'))"
              >
                ({{ getStatPercent('home', 'match_totals', threshold + '+') }}%)
              </span>
            </div>
            <div
              v-if="isExpanded('home', 'total', threshold)"
              class="matches-list"
            >
              <div
                v-for="match in getMatches('home', 'match_totals', threshold + '+')"
                :key="match.date + match.opponent"
                class="match-item"
              >
                <span class="match-item-date">{{ match.date }}</span>
                <span class="match-item-opponent">{{ match.opponent }}</span>
                <span class="match-item-score">{{ match.score }} ({{ match.total }})</span>
              </div>
              <div v-if="!getMatches('home', 'match_totals', threshold + '+').length" class="match-item">
                Нет матчей
              </div>
            </div>
          </td>
          <td>
            <div
              class="stat-value"
              @click="toggleDetails('away', 'total', threshold)"
            >
              <span class="stat-count">{{ getStatCount('away', 'match_totals', threshold + '+') }}</span>
              <span
                class="stat-percent"
                :class="getProbClass(getStatPercent('away', 'match_totals', threshold + '+'))"
              >
                ({{ getStatPercent('away', 'match_totals', threshold + '+') }}%)
              </span>
            </div>
            <div
              v-if="isExpanded('away', 'total', threshold)"
              class="matches-list"
            >
              <div
                v-for="match in getMatches('away', 'match_totals', threshold + '+')"
                :key="match.date + match.opponent"
                class="match-item"
              >
                <span class="match-item-date">{{ match.date }}</span>
                <span class="match-item-opponent">{{ match.opponent }}</span>
                <span class="match-item-score">{{ match.score }} ({{ match.total }})</span>
              </div>
              <div v-if="!getMatches('away', 'match_totals', threshold + '+').length" class="match-item">
                Нет матчей
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Match counts -->
    <div class="stats-divider"></div>
    <div style="font-size: 12px; color: var(--text-secondary); text-align: center;">
      Дома: {{ teamData.stats?.home?.total_matches || 0 }} матчей |
      Выезд: {{ teamData.stats?.away?.total_matches || 0 }} матчей
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatsTable',
  props: {
    teamData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      individualThresholds: [2, 3, 4, 5, 6],
      totalThresholds: [5, 6, 7, 8],
      expanded: {}
    }
  },
  methods: {
    getStatCount(location, statType, threshold) {
      return this.teamData?.stats?.[location]?.[statType]?.[threshold]?.count ?? 0
    },

    getStatPercent(location, statType, threshold) {
      return this.teamData?.stats?.[location]?.[statType]?.[threshold]?.weighted_percentage ?? 0
    },

    getMatches(location, statType, threshold) {
      return this.teamData?.stats?.[location]?.[statType]?.[threshold]?.matches ?? []
    },

    getProbClass(percent) {
      if (percent >= 70) return 'prob-high'
      if (percent >= 40) return 'prob-medium'
      return 'prob-low'
    },

    toggleDetails(location, type, threshold) {
      const key = `${location}-${type}-${threshold}`
      this.expanded[key] = !this.expanded[key]
    },

    isExpanded(location, type, threshold) {
      const key = `${location}-${type}-${threshold}`
      return this.expanded[key]
    }
  }
}
</script>
