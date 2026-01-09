import axios from 'axios'

// Use environment variable for API URL, fallback to relative path for dev proxy
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
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

  // Refresh data (for serverless, just returns success - data is always fresh)
  async syncGames(league = 'NHL') {
    // In serverless mode, data is fetched fresh from APIs
    // This method exists for backwards compatibility
    return { success: true, message: "Data refreshed from source APIs" }
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
  },

  // Get team news
  async getTeamNews(teamAbbrev, league = 'DEL', limit = 5) {
    const response = await api.get(`/teams/${teamAbbrev}/news`, {
      params: { league, limit }
    })
    return response.data
  }
}

// Backwards compatibility
export const nhlApi = hockeyApi

export default hockeyApi
