/**
 * Local team logo mapping
 * Uses locally stored SVG logos for better performance
 */

// NHL teams - use local SVG files (all 33 teams)
export const NHL_LOGOS = {
  'ANA': '/logos/ANA.svg',
  'ARI': '/logos/ARI.svg',
  'BOS': '/logos/BOS.svg',
  'BUF': '/logos/BUF.svg',
  'CGY': '/logos/CGY.svg',
  'CAR': '/logos/CAR.svg',
  'CHI': '/logos/CHI.svg',
  'COL': '/logos/COL.svg',
  'CBJ': '/logos/CBJ.svg',
  'DAL': '/logos/DAL.svg',
  'DET': '/logos/DET.svg',
  'EDM': '/logos/EDM.svg',
  'FLA': '/logos/FLA.svg',
  'LAK': '/logos/LAK.svg',
  'MIN': '/logos/MIN.svg',
  'MTL': '/logos/MTL.svg',
  'NSH': '/logos/NSH.svg',
  'NJD': '/logos/NJD.svg',
  'NYI': '/logos/NYI.svg',
  'NYR': '/logos/NYR.svg',
  'OTT': '/logos/OTT.svg',
  'PHI': '/logos/PHI.svg',
  'PIT': '/logos/PIT.svg',
  'SJS': '/logos/SJS.svg',
  'SEA': '/logos/SEA.svg',
  'STL': '/logos/STL.svg',
  'TBL': '/logos/TBL.svg',
  'TOR': '/logos/TOR.svg',
  'UTA': '/logos/UTA.svg',
  'VAN': '/logos/VAN.svg',
  'VGK': '/logos/VGK.svg',
  'WSH': '/logos/WSH.svg',
  'WPG': '/logos/WPG.svg',
}

// AHL teams - remote URLs (leaguestat CDN)
export const AHL_LOGO_IDS = {
  'ABB': '50013', 'BAK': '329', 'BEL': '50004', 'BRI': '316',
  'CGW': '50026', 'CLT': '311', 'CLE': '312', 'COA': '50025',
  'HFD': '304', 'LV': '50015', 'HER': '319', 'IA': '335',
  'LAV': '50003', 'LHV': '313', 'MB': '321', 'MIL': '330',
  'ONT': '333', 'PRO': '309', 'ROC': '305', 'RFD': '334',
  'SD': '50005', 'SJ': '328', 'SPR': '310', 'SYR': '315',
  'TEX': '331', 'TUC': '50006', 'UTC': '306', 'WBS': '314',
}

/**
 * Get logo URL for a team
 * Uses local logos for NHL, remote for other leagues
 */
export function getTeamLogo(abbrev, fallbackUrl = null) {
  if (!abbrev) return fallbackUrl

  const upperAbbrev = abbrev.toUpperCase()

  // Check NHL local logos first
  if (NHL_LOGOS[upperAbbrev]) {
    return NHL_LOGOS[upperAbbrev]
  }

  // Check AHL - use leaguestat CDN
  if (AHL_LOGO_IDS[upperAbbrev]) {
    return `https://assets.leaguestat.com/ahl/logos/${AHL_LOGO_IDS[upperAbbrev]}.png`
  }

  return fallbackUrl
}

export default { NHL_LOGOS, AHL_LOGO_IDS, getTeamLogo }
