"""Script to download all NHL team logos locally"""
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

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'logos')


async def download_logo(client, abbrev, url):
    """Download a single logo"""
    try:
        resp = await client.get(url)
        if resp.status_code == 200:
            ext = 'svg' if '.svg' in url else 'png'
            filepath = os.path.join(OUTPUT_DIR, f'{abbrev}.{ext}')
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            print(f'Downloaded: {abbrev}')
            return True
    except Exception as e:
        print(f'Failed {abbrev}: {e}')
    return False


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [download_logo(client, abbrev, url) for abbrev, url in NHL_TEAMS.items()]
        results = await asyncio.gather(*tasks)

    success = sum(results)
    print(f'\nDownloaded {success}/{len(NHL_TEAMS)} logos')


if __name__ == '__main__':
    asyncio.run(main())
