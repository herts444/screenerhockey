<template>
  <div class="lineup-table">
    <div class="team-header">
      <h3>{{ team }}</h3>
      <span class="player-count">{{ totalPlayers }} игроков</span>
    </div>

    <!-- Leaders Active (Yellow) -->
    <div v-if="players.leaders_active?.length" class="player-group">
      <div class="group-header yellow">
        <span class="group-icon">🟡</span>
        <span class="group-title">Лидеры в составе</span>
        <span class="group-count">{{ players.leaders_active.length }}</span>
      </div>
      <div class="players-list">
        <div
          v-for="player in players.leaders_active"
          :key="player.name"
          class="player-row yellow"
        >
          <div class="player-name">{{ player.name }}</div>
          <div class="player-stats">
            <span class="stat" title="Матчи">{{ player.matches }} М</span>
            <span class="stat" title="Голы">{{ player.goals }} Г</span>
            <span class="stat" title="Передачи">{{ player.assists }} П</span>
            <span class="stat points" title="Очки">{{ player.points }} О</span>
            <span class="stat efficiency" title="Очков за матч">{{ player.efficiency.toFixed(2) }}/м</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Leaders Questionable (Orange) -->
    <div v-if="players.leaders_questionable?.length" class="player-group">
      <div class="group-header orange">
        <span class="group-icon">🟠</span>
        <span class="group-title">Лидеры под вопросом</span>
        <span class="group-subtitle">(не играли в последнем матче)</span>
        <span class="group-count">{{ players.leaders_questionable.length }}</span>
      </div>
      <div class="players-list">
        <div
          v-for="player in players.leaders_questionable"
          :key="player.name"
          class="player-row orange"
        >
          <div class="player-name">{{ player.name }}</div>
          <div class="player-status">{{ player.status }}</div>
          <div class="player-stats">
            <span class="stat" title="Матчи">{{ player.matches }} М</span>
            <span class="stat" title="Голы">{{ player.goals }} Г</span>
            <span class="stat" title="Передачи">{{ player.assists }} П</span>
            <span class="stat points" title="Очки">{{ player.points }} О</span>
            <span class="stat efficiency" title="Очков за матч">{{ player.efficiency.toFixed(2) }}/м</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Absent (Red) -->
    <div v-if="players.absent?.length" class="player-group">
      <div class="group-header red">
        <span class="group-icon">🔴</span>
        <span class="group-title">Отсутствуют</span>
        <span class="group-subtitle">(травма / не заявлены)</span>
        <span class="group-count">{{ players.absent.length }}</span>
      </div>
      <div class="players-list">
        <div
          v-for="player in players.absent"
          :key="player.name"
          class="player-row red"
        >
          <div class="player-name">{{ player.name }}</div>
          <div class="player-status">{{ player.status }}</div>
          <div class="player-stats">
            <span class="stat" title="Матчи">{{ player.matches }} М</span>
            <span class="stat" title="Голы">{{ player.goals }} Г</span>
            <span class="stat" title="Передачи">{{ player.assists }} П</span>
            <span class="stat points" title="Очки">{{ player.points }} О</span>
            <span class="stat efficiency" title="Очков за матч">{{ player.efficiency.toFixed(2) }}/м</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Others (No color) -->
    <div v-if="players.others?.length" class="player-group">
      <div class="group-header others">
        <span class="group-icon">⚪</span>
        <span class="group-title">Остальные игроки</span>
        <span class="group-count">{{ players.others.length }}</span>
      </div>
      <div class="players-list collapsed" :class="{ expanded: showOthers }">
        <div
          v-for="player in players.others"
          :key="player.name"
          class="player-row"
        >
          <div class="player-name">{{ player.name }}</div>
          <div class="player-stats">
            <span class="stat" title="Матчи">{{ player.matches }} М</span>
            <span class="stat" title="Голы">{{ player.goals }} Г</span>
            <span class="stat" title="Передачи">{{ player.assists }} П</span>
            <span class="stat points" title="Очки">{{ player.points }} О</span>
            <span class="stat efficiency" title="Очков за матч">{{ player.efficiency.toFixed(2) }}/м</span>
          </div>
        </div>
      </div>
      <button
        v-if="players.others?.length > 5"
        class="toggle-others"
        @click="showOthers = !showOthers"
      >
        {{ showOthers ? 'Скрыть' : `Показать всех (${players.others.length})` }}
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="isEmpty" class="empty-state">
      Нет данных об игроках
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'LineupTable',
  props: {
    team: {
      type: String,
      required: true
    },
    players: {
      type: Object,
      required: true,
      default: () => ({
        leaders_active: [],
        leaders_questionable: [],
        absent: [],
        others: []
      })
    },
    totalPlayers: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const showOthers = ref(false)

    const isEmpty = computed(() => {
      const p = props.players
      return !p.leaders_active?.length &&
             !p.leaders_questionable?.length &&
             !p.absent?.length &&
             !p.others?.length
    })

    return {
      showOthers,
      isEmpty
    }
  }
}
</script>

<style scoped>
.lineup-table {
  background: var(--card-bg, #1a1a2e);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.team-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #fff;
}

.player-count {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.875rem;
}

.player-group {
  margin-bottom: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  font-weight: 500;
}

.group-header.yellow {
  background: rgba(255, 215, 0, 0.15);
  border-left: 3px solid #ffd700;
}

.group-header.orange {
  background: rgba(255, 165, 0, 0.15);
  border-left: 3px solid #ffa500;
}

.group-header.red {
  background: rgba(255, 77, 77, 0.15);
  border-left: 3px solid #ff4d4d;
}

.group-header.others {
  background: rgba(255, 255, 255, 0.05);
  border-left: 3px solid rgba(255, 255, 255, 0.3);
}

.group-icon {
  font-size: 0.875rem;
}

.group-title {
  color: #fff;
  flex-grow: 1;
}

.group-subtitle {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.75rem;
  font-weight: normal;
}

.group-count {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.players-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.players-list.collapsed {
  max-height: 200px;
  overflow: hidden;
}

.players-list.expanded {
  max-height: none;
}

.player-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  transition: background 0.2s;
}

.player-row:hover {
  background: rgba(255, 255, 255, 0.08);
}

.player-row.yellow {
  background: rgba(255, 215, 0, 0.08);
}

.player-row.yellow:hover {
  background: rgba(255, 215, 0, 0.15);
}

.player-row.orange {
  background: rgba(255, 165, 0, 0.08);
}

.player-row.orange:hover {
  background: rgba(255, 165, 0, 0.15);
}

.player-row.red {
  background: rgba(255, 77, 77, 0.08);
}

.player-row.red:hover {
  background: rgba(255, 77, 77, 0.15);
}

.player-name {
  flex: 1;
  color: #fff;
  font-weight: 500;
  min-width: 150px;
}

.player-status {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.75rem;
  margin-right: 16px;
  min-width: 80px;
}

.player-stats {
  display: flex;
  gap: 12px;
  font-size: 0.875rem;
}

.stat {
  color: rgba(255, 255, 255, 0.7);
  min-width: 45px;
  text-align: right;
}

.stat.points {
  color: #4fc3f7;
  font-weight: 500;
}

.stat.efficiency {
  color: #81c784;
  font-weight: 600;
  min-width: 55px;
}

.toggle-others {
  width: 100%;
  padding: 8px;
  margin-top: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-others:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.empty-state {
  text-align: center;
  padding: 32px;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 768px) {
  .player-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .player-name {
    min-width: 100%;
  }

  .player-stats {
    flex-wrap: wrap;
    gap: 8px;
  }

  .stat {
    min-width: 40px;
  }
}
</style>
