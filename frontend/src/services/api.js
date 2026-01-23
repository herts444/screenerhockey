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

  // Get system status (hardcoded - endpoint removed)
  async getStatus(league = 'NHL') {
    return {
      status: 'ok',
      league,
      cache_loaded: true
    }
  },

  // Get available leagues (hardcoded - endpoint removed)
  async getLeagues() {
    return {
      leagues: [
        { code: 'NHL', name: 'NHL', name_ru: 'НХЛ', cached: true },
        { code: 'AHL', name: 'AHL', name_ru: 'АХЛ', cached: true },
        { code: 'LIIGA', name: 'Liiga', name_ru: 'Лиига', cached: true },
        { code: 'KHL', name: 'KHL', name_ru: 'КХЛ', cached: true }
      ]
    }
  },

  // Get team news (removed - returns empty)
  async getTeamNews(teamAbbrev, league = 'DEL', limit = 5) {
    return { news: [] }
  },

  // Get bookmaker odds from JetTon
  async getOdds(league = null) {
    const params = league ? { league } : {}
    const response = await api.get('/odds', { params })
    return response.data
  },

  // Get detailed odds for specific event
  async getEventOdds(eventId) {
    const response = await api.get('/odds', { params: { event_id: eventId } })
    return response.data
  }
}

// Lineups API methods
export const lineupsApi = {
  // Get matches list for a league and day
  async getMatches(league = 'KHL', day = 0) {
    const response = await api.get('/lineups/matches', { params: { league, day } })
    return response.data
  },

  // Get lineup for a match (both teams)
  async getMatchLineup(matchUrl) {
    const response = await api.get('/lineups/lineup', { params: { type: 'match', url: matchUrl } })
    return response.data
  },

  // Get lineup for a single team
  async getTeamLineup(teamUrl) {
    const response = await api.get('/lineups/lineup', { params: { type: 'team', url: teamUrl } })
    return response.data
  }
}

// Backwards compatibility
export const nhlApi = hockeyApi

// Export raw axios instance for direct use
export { api }

export default hockeyApi
