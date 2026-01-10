"""Script to download all team logos locally"""
import os
import httpx
import asyncio

# NHL team logos from official API
NHL_TEAMS = {
    'ANA': 'https://assets.nhle.com/logos/nhl/svg/ANA_dark.svg',
    'ARI': 'https://assets.nhle.com/logos/nhl/svg/ARI_dark.svg',
    'BOS': 'https://assets.nhle.com/logos/nhl/svg/BOS_dark.svg',
    'BUF': 'https://assets.nhle.com/logos/nhl/svg/BUF_dark.svg',
    'CGY': 'https://assets.nhle.com/logos/nhl/svg/CGY_dark.svg',
    'CAR': 'https://assets.nhle.com/logos/nhl/svg/CAR_dark.svg',
    'CHI': 'https://assets.nhle.com/logos/nhl/svg/CHI_dark.svg',
    'COL': 'https://assets.nhle.com/logos/nhl/svg/COL_dark.svg',
    'CBJ': 'https://assets.nhle.com/logos/nhl/svg/CBJ_dark.svg',
    'DAL': 'https://assets.nhle.com/logos/nhl/svg/DAL_dark.svg',
    'DET': 'https://assets.nhle.com/logos/nhl/svg/DET_dark.svg',
    'EDM': 'https://assets.nhle.com/logos/nhl/svg/EDM_dark.svg',
    'FLA': 'https://assets.nhle.com/logos/nhl/svg/FLA_dark.svg',
    'LAK': 'https://assets.nhle.com/logos/nhl/svg/LAK_dark.svg',
    'MIN': 'https://assets.nhle.com/logos/nhl/svg/MIN_dark.svg',
    'MTL': 'https://assets.nhle.com/logos/nhl/svg/MTL_dark.svg',
    'NSH': 'https://assets.nhle.com/logos/nhl/svg/NSH_dark.svg',
    'NJD': 'https://assets.nhle.com/logos/nhl/svg/NJD_dark.svg',
    'NYI': 'https://assets.nhle.com/logos/nhl/svg/NYI_dark.svg',
    'NYR': 'https://assets.nhle.com/logos/nhl/svg/NYR_dark.svg',
    'OTT': 'https://assets.nhle.com/logos/nhl/svg/OTT_dark.svg',
    'PHI': 'https://assets.nhle.com/logos/nhl/svg/PHI_dark.svg',
    'PIT': 'https://assets.nhle.com/logos/nhl/svg/PIT_dark.svg',
    'SJS': 'https://assets.nhle.com/logos/nhl/svg/SJS_dark.svg',
    'SEA': 'https://assets.nhle.com/logos/nhl/svg/SEA_dark.svg',
    'STL': 'https://assets.nhle.com/logos/nhl/svg/STL_dark.svg',
    'TBL': 'https://assets.nhle.com/logos/nhl/svg/TBL_dark.svg',
    'TOR': 'https://assets.nhle.com/logos/nhl/svg/TOR_dark.svg',
    'UTA': 'https://assets.nhle.com/logos/nhl/svg/UTA_dark.svg',
    'VAN': 'https://assets.nhle.com/logos/nhl/svg/VAN_dark.svg',
    'VGK': 'https://assets.nhle.com/logos/nhl/svg/VGK_dark.svg',
    'WSH': 'https://assets.nhle.com/logos/nhl/svg/WSH_dark.svg',
    'WPG': 'https://assets.nhle.com/logos/nhl/svg/WPG_dark.svg',
}

# AHL team logos - using lscluster (alternative CDN)
AHL_TEAMS = {
    'ABB': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50013.png',
    'BAK': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/329.png',
    'BEL': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50004.png',
    'BRI': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/316.png',
    'CGW': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50026.png',
    'CLT': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/311.png',
    'CLE': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/312.png',
    'COA': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50025.png',
    'HFD': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/304.png',
    'LV': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50015.png',
    'HER': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/319.png',
    'IA': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/335.png',
    'LAV': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50003.png',
    'LHV': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/313.png',
    'MB': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/321.png',
    'MIL': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/330.png',
    'ONT': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/333.png',
    'PRO': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/309.png',
    'ROC': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/305.png',
    'RFD': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/334.png',
    'SD': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50005.png',
    'SJ': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/328.png',
    'SPR': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/310.png',
    'SYR': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/315.png',
    'TEX': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/331.png',
    'TUC': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/50006.png',
    'UTC': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/306.png',
    'WBS': 'https://lscluster.hockeytech.com/download.php?file_path=img/logos/314.png',
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'logos')


async def download_logo(client, abbrev, url, league=''):
    """Download a single logo"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = await client.get(url, follow_redirects=True, headers=headers)
        if resp.status_code == 200 and len(resp.content) > 100:
            ext = 'svg' if '.svg' in url else 'png'
            filepath = os.path.join(OUTPUT_DIR, f'{abbrev}.{ext}')
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            print(f'Downloaded: {league} {abbrev}')
            return True
        else:
            print(f'Failed {league} {abbrev}: status={resp.status_code}, size={len(resp.content)}')
    except Exception as e:
        print(f'Failed {league} {abbrev}: {e}')
    return False


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Download NHL logos
        print("=== NHL ===")
        nhl_tasks = [download_logo(client, abbrev, url, 'NHL') for abbrev, url in NHL_TEAMS.items()]
        nhl_results = await asyncio.gather(*nhl_tasks)
        print(f'NHL: {sum(nhl_results)}/{len(NHL_TEAMS)}')

        # Download AHL logos
        print("\n=== AHL ===")
        ahl_tasks = [download_logo(client, abbrev, url, 'AHL') for abbrev, url in AHL_TEAMS.items()]
        ahl_results = await asyncio.gather(*ahl_tasks)
        print(f'AHL: {sum(ahl_results)}/{len(AHL_TEAMS)}')

    total = sum(nhl_results) + sum(ahl_results)
    total_teams = len(NHL_TEAMS) + len(AHL_TEAMS)
    print(f'\n=== TOTAL: {total}/{total_teams} logos downloaded ===')


if __name__ == '__main__':
    asyncio.run(main())
