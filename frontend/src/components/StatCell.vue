<template>
  <div class="stat-cell" :class="probClass" @click="$emit('click')">
    <template v-if="data">
      <span class="count">{{ data.total_matches || data.count }}</span>
      <span class="ratio">{{ data.count }}/{{ data.total_matches || data.count }}</span>
      <span class="percent">{{ data.weighted_percentage }}%</span>
    </template>
    <template v-else>
      <span class="no-data">-</span>
    </template>
  </div>
</template>

<script>
export default {
  name: 'StatCell',
  props: {
    data: {
      type: Object,
      default: null
    }
  },
  emits: ['click'],
  computed: {
    probClass() {
      if (!this.data) return ''
      const pct = this.data.weighted_percentage
      if (pct >= 70) return 'prob-high'
      if (pct >= 50) return 'prob-medium'
      if (pct >= 30) return 'prob-low'
      return 'prob-very-low'
    }
  }
}
</script>

<style scoped>
.stat-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
  min-width: 40px;
}

.stat-cell:hover {
  background-color: var(--bg-hover);
}

.count {
  font-weight: 600;
  font-size: 13px;
}

.ratio {
  font-size: 10px;
  opacity: 0.7;
}

.percent {
  font-size: 10px;
  opacity: 0.8;
}

.no-data {
  color: var(--text-muted);
}

.prob-high {
  color: var(--accent-green);
}

.prob-medium {
  color: var(--accent-yellow);
}

.prob-low {
  color: #f97316;
}

.prob-very-low {
  color: var(--accent-red);
}
</style>
