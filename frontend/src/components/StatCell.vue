<template>
  <div class="stat-cell" :class="probClass" @click="$emit('click')">
    <template v-if="data">
      <div class="stat-main">
        <span class="count">{{ data.count }}/{{ data.total_matches || data.count }}</span>
      </div>
      <div class="stat-sub">
        <span class="percent">{{ simplePercentage }}%</span>
      </div>
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
    simplePercentage() {
      if (!this.data) return 0
      const total = this.data.total_matches || this.data.count || 1
      const count = this.data.count || 0
      return Math.round((count / total) * 100 * 10) / 10
    },
    probClass() {
      if (!this.data) return ''
      const pct = this.simplePercentage
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
  justify-content: center;
  cursor: pointer;
  padding: 6px 4px;
  border-radius: 0;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 50px;
  gap: 2px;
  position: relative;
}

.stat-cell:hover {
  background: rgba(37, 99, 235, 0.1);
  transform: scale(1.05);
}

.stat-cell::after {
  content: '';
  position: absolute;
  inset: 0;
  border: 1px solid currentColor;
  opacity: 0;
  transition: opacity 0.2s;
}

.stat-cell:hover::after {
  opacity: 0.2;
}

.stat-main {
  display: flex;
  align-items: center;
  gap: 4px;
}

.count {
  font-weight: 700;
  font-size: 12px;
  line-height: 1;
}

.stat-sub {
  display: flex;
  align-items: center;
}

.percent {
  font-size: 10px;
  font-weight: 600;
  opacity: 0.9;
  line-height: 1;
}

.no-data {
  color: var(--text-muted);
  font-size: 14px;
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
