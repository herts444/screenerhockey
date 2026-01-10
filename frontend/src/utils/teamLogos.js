/**
 * Local team logo mapping
 * Uses locally stored SVG logos for better performance
 */

// NHL teams - use local SVG files
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

/**
 * Get logo URL for a team
 * Falls back to remote URL if local not available
 */
export function getTeamLogo(abbrev, fallbackUrl = null) {
  if (!abbrev) return fallbackUrl

  const localLogo = NHL_LOGOS[abbrev.toUpperCase()]
  if (localLogo) return localLogo

  return fallbackUrl
}

export default { NHL_LOGOS, getTeamLogo }
