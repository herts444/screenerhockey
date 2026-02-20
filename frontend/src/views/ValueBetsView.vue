<template>
  <div class="home-page">
    <header class="header">
      <AppNav />
    </header>

    <ValueBets
      :stats-cache="statsCache"
      @stats-loaded="onStatsLoaded"
    />
  </div>
</template>

<script>
import AppNav from '../components/AppNav.vue'
import ValueBets from '../components/ValueBets.vue'

export default {
  name: 'ValueBetsView',
  components: {
    AppNav,
    ValueBets
  },
  data() {
    return {
      statsCache: {}
    }
  },
  methods: {
    onStatsLoaded({ abbrev, stats }) {
      this.statsCache[abbrev] = stats
    }
  }
}
</script>
