<template>
  <div class="lineup-table">
    <div class="team-header">
      <h3>{{ team }}</h3>
    </div>

    <!-- Leaders Active (Yellow) -->
    <div v-if="players.leaders_active?.length" class="player-group">
      <div class="group-header yellow">Лидеры в составе</div>
      <table class="players-table">
        <thead>
          <tr>
            <th class="th-name">Игрок</th>
            <th class="th-stat">М</th>
            <th class="th-stat">Г</th>
            <th class="th-stat">П</th>
            <th class="th-stat">О</th>
            <th class="th-stat">О/М</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="player in players.leaders_active" :key="player.name" class="row-yellow">
            <td class="td-name">{{ player.name }}</td>
            <td class="td-stat">{{ player.matches }}</td>
            <td class="td-stat">{{ player.goals }}</td>
            <td class="td-stat">{{ player.assists }}</td>
            <td class="td-stat td-points">{{ player.points }}</td>
            <td class="td-stat td-efficiency">{{ player.efficiency?.toFixed(2) || '0.00' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Absent (Red) -->
    <div v-if="players.absent?.length" class="player-group">
      <div class="group-header red">Отсутствуют</div>
      <table class="players-table">
        <thead>
          <tr>
            <th class="th-name">Игрок</th>
            <th class="th-status">Статус</th>
            <th class="th-stat">О</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="player in displayedAbsent" :key="player.name" class="row-red">
            <td class="td-name">{{ player.name }}</td>
            <td class="td-status">{{ player.status || 'не заявлен' }}</td>
            <td class="td-stat td-points">{{ player.points }}</td>
          </tr>
        </tbody>
      </table>
      <button
        v-if="players.absent?.length > 5"
        class="toggle-btn"
        @click="showAllAbsent = !showAllAbsent"
      >
        {{ showAllAbsent ? 'Скрыть' : `+${players.absent.length - 5} ещё` }}
      </button>
    </div>

    <!-- Empty state -->
    <div v-if="isEmpty" class="empty-state">
      Нет данных
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
    const showAllAbsent = ref(false)

    const isEmpty = computed(() => {
      const p = props.players
      return !p.leaders_active?.length &&
             !p.leaders_questionable?.length &&
             !p.absent?.length &&
             !p.others?.length
    })

    const displayedAbsent = computed(() => {
      if (showAllAbsent.value || props.players.absent?.length <= 5) {
        return props.players.absent || []
      }
      return props.players.absent?.slice(0, 5) || []
    })

    return {
      showAllAbsent,
      isEmpty,
      displayedAbsent
    }
  }
}
</script>

<style scoped>
.lineup-table {
  background: var(--card-bg, #1a1a2e);
  border-radius: 8px;
  overflow: hidden;
}

.team-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.team-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #4fc3f7;
  font-weight: 600;
}

.player-group {
  margin-bottom: 0;
}

.group-header {
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.group-header.yellow {
  background: rgba(255, 215, 0, 0.15);
  color: #ffd700;
  border-left: 3px solid #ffd700;
}

.group-header.red {
  background: rgba(255, 77, 77, 0.15);
  color: #ff6b6b;
  border-left: 3px solid #ff4d4d;
}

.players-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.players-table thead {
  background: rgba(0, 0, 0, 0.3);
}

.players-table th {
  padding: 6px 8px;
  text-align: left;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.7rem;
  text-transform: uppercase;
}

.th-name {
  width: 50%;
  padding-left: 16px !important;
}

.th-stat {
  width: 10%;
  text-align: center !important;
}

.th-status {
  width: 30%;
  text-align: center !important;
}

.players-table td {
  padding: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.td-name {
  color: #fff;
  font-weight: 500;
  padding-left: 16px !important;
}

.td-stat {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
}

.td-points {
  color: #4fc3f7;
  font-weight: 600;
}

.td-efficiency {
  color: #81c784;
  font-weight: 600;
}

.td-status {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.75rem;
}

.row-yellow {
  background: rgba(255, 215, 0, 0.05);
}

.row-yellow:hover {
  background: rgba(255, 215, 0, 0.1);
}

.row-red {
  background: rgba(255, 77, 77, 0.05);
}

.row-red:hover {
  background: rgba(255, 77, 77, 0.1);
}

.toggle-btn {
  width: 100%;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.empty-state {
  text-align: center;
  padding: 24px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.875rem;
}
</style>
