import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const hockeyApi = {
  // Get all teams
  async getTeams(league = 'NHL') {
    const response = await api.get('/teams', { params: { league } })
    return response.data
  },

  // Get upcoming games
  async getUpcomingGames(league = 'NHL', days = 7) {
    const response = await api.get('/schedule/upcoming', { params: { league, days } })
    return response.data
  },

  // Get team statistics
  async getTeamStats(teamAbbrev, league = 'NHL', lastN = 15) {
    const response = await api.get(`/teams/${teamAbbrev}/stats`, {
      params: { league, last_n: lastN }
    })
    return response.data
  },

  // Get match analysis for two teams
  async getMatchAnalysis(homeTeam, awayTeam, league = 'NHL', lastN = 15) {
    const response = await api.get('/match/analysis', {
      params: {
        home_team: homeTeam,
        away_team: awayTeam,
        league,
        last_n: lastN
      }
    })
    return response.data
  },

  // Sync teams from API
  async syncTeams(league = 'NHL') {
    const response = await api.post('/sync/teams', null, {
      params: { league }
    })
    return response.data
  },

  // Sync all games
  async syncGames(league = 'NHL', season = '20242025') {
    const response = await api.post('/sync/games', null, {
      params: { league, season }
    })
    return response.data
  },

  // Get system status
  async getStatus(league = 'NHL') {
    const response = await api.get('/status', { params: { league } })
    return response.data
  },

  // Get available leagues
  async getLeagues() {
    const response = await api.get('/leagues')
    return response.data
  }
}

// Backwards compatibility
export const nhlApi = hockeyApi

export default hockeyApi
