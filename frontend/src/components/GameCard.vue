<template>
  <div
    class="game-card"
    :class="{ selected: isSelected }"
    @click="$emit('select', game)"
  >
    <div class="game-date">{{ formatDate(game.date) }}</div>
    <div class="game-teams">
      <div class="team-info">
        <img
          :src="game.away_team.logo_url"
          :alt="game.away_team.name"
          class="team-logo"
        >
        <span class="team-name">{{ game.away_team.name_ru || game.away_team.name }}</span>
      </div>
      <span class="vs-badge">@</span>
      <div class="team-info">
        <img
          :src="game.home_team.logo_url"
          :alt="game.home_team.name"
          class="team-logo"
        >
        <span class="team-name">{{ game.home_team.name_ru || game.home_team.name }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GameCard',
  props: {
    game: {
      type: Object,
      required: true
    },
    isSelected: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select'],
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return ''
      return dateStr
    }
  }
}
</script>
