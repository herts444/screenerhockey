"""GET /api/odds - Get bookmaker odds from JetTon"""
from http.server import BaseHTTPRequestHandler
import json
import httpx
from urllib.parse import urlparse, parse_qs

BRAND_ID = '2467728453932290048'
BASE_URL = 'https://sp.btspcloud.xyz'

# JetTon team name to our abbreviation mapping
JETTON_TO_ABBREV = {
    # NHL
    'Anaheim Ducks': 'ANA',
    'Arizona Coyotes': 'ARI',
    'Boston Bruins': 'BOS',
    'Buffalo Sabres': 'BUF',
    'Calgary Flames': 'CGY',
    'Carolina Hurricanes': 'CAR',
    'Chicago Blackhawks': 'CHI',
    'Colorado Avalanche': 'COL',
    'Columbus Blue Jackets': 'CBJ',
    'Dallas Stars': 'DAL',
    'Detroit Red Wings': 'DET',
    'Edmonton Oilers': 'EDM',
    'Florida Panthers': 'FLA',
    'Los Angeles Kings': 'LAK',
    'Minnesota Wild': 'MIN',
    'Montreal Canadiens': 'MTL',
    'Nashville Predators': 'NSH',
    'New Jersey Devils': 'NJD',
    'New York Islanders': 'NYI',
    'New York Rangers': 'NYR',
    'Ottawa Senators': 'OTT',
    'Philadelphia Flyers': 'PHI',
    'Pittsburgh Penguins': 'PIT',
    'San Jose Sharks': 'SJS',
    'Seattle Kraken': 'SEA',
    'St. Louis Blues': 'STL',
    'Tampa Bay Lightning': 'TBL',
    'Toronto Maple Leafs': 'TOR',
    'Utah Mammoth': 'UTA',
    'Utah Hockey Club': 'UTA',
    'Vancouver Canucks': 'VAN',
    'Vegas Golden Knights': 'VGK',
    'Washington Capitals': 'WSH',
    'Winnipeg Jets': 'WPG',
    # AHL (codes match HockeyTech API)
    'Abbotsford Canucks': 'ABB',
    'Bakersfield Condors': 'BAK',
    'Belleville Senators': 'BEL',
    'Bridgeport Islanders': 'BRI',
    'Calgary Wranglers': 'CGY',
    'Charlotte Checkers': 'CLT',
    'Chicago Wolves': 'CHI',
    'Cleveland Monsters': 'CLE',
    'Coachella Valley Firebirds': 'CV',
    'Colorado Eagles': 'COL',
    'Grand Rapids Griffins': 'GR',
    'Hartford Wolf Pack': 'HFD',
    'Henderson Silver Knights': 'HSK',
    'Hershey Bears': 'HER',
    'Iowa Wild': 'IA',
    'Laval Rocket': 'LAV',
    'Lehigh Valley Phantoms': 'LV',
    'Manitoba Moose': 'MB',
    'Milwaukee Admirals': 'MIL',
    'Ontario Reign': 'ONT',
    'Providence Bruins': 'PRO',
    'Rochester Americans': 'ROC',
    'Rockford Icehogs': 'RFD',
    'San Diego Gulls': 'SD',
    'San Jose Barracuda': 'SJ',
    'Springfield Thunderbirds': 'SPR',
    'Syracuse Crunch': 'SYR',
    'Texas Stars': 'TEX',
    'Toronto Marlies': 'TOR',
    'Tucson Roadrunners': 'TUC',
    'Utica Comets': 'UTC',
    'Wilkes-Barre/Scranton Penguins': 'WBS',
    # DEL
    'Adler Mannheim': 'MAN',
    'Augsburger Panther': 'AEV',
    'ERC Ingolstadt': 'ING',
    'Fischtown Pinguins': 'BHV',
    'Grizzlys Wolfsburg': 'WOB',
    'Iserlohn Roosters': 'IEC',
    'Kolner Haie': 'KEC',
    'Lowen Frankfurt': 'FRA',
    'Nuremberg Ice Tigers': 'NIT',
    'Red Bull Munich': 'RBM',
    'Schwenninger Wild Wings': 'SWW',
    'Straubing Tigers': 'STR',
    'Eisbaren Berlin': 'EBB',
}

# JetTon tournament IDs
TOURNAMENTS = {
    'NHL': '1669818960062844928',
    'AHL': '1669819027318509568',
    'DEL': '1669818980447162368',
    'LIIGA': None,  # Need to find
    'KHL': '1669817284652306432',
}

# Market IDs
MARKETS = {
    'total': '18',           # Match total
    'team1_total': '19',     # Home team individual total
    'team2_total': '20',     # Away team individual total
    'winner': '1',           # 1X2
    'handicap': '16',        # Handicap
}


async def fetch_all_hockey_events():
    """Fetch all hockey events from JetTon"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get version info
        resp = await client.get(f'{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/en/0')
        data = resp.json()

        all_events = {}
        tournaments_data = {}

        # Fetch all chunks
        versions = data.get('top_events_versions', []) + data.get('rest_events_versions', [])
        for version in versions:
            try:
                resp = await client.get(f'{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/en/{version}')
                chunk = resp.json()
                if 'events' in chunk:
                    all_events.update(chunk['events'])
                if 'tournaments' in chunk:
                    tournaments_data.update(chunk['tournaments'])
            except:
                pass

        # Filter hockey events (sport_id = 4)
        hockey_events = {}
        for event_id, event in all_events.items():
            desc = event.get('desc', {})
            competitors = desc.get('competitors', [])
            if len(competitors) >= 2 and competitors[0].get('sport_id') == '4':
                # Skip outrights
                if any('winner' in c.get('name', '').lower() for c in competitors):
                    continue
                hockey_events[event_id] = event

        return hockey_events, tournaments_data


async def fetch_event_odds(event_id: str):
    """Fetch detailed odds for specific event"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f'{BASE_URL}/api/v4/prematch/brand/{BRAND_ID}/event/en/{event_id}'
        resp = await client.get(url)

        if resp.status_code != 200:
            return None

        data = resp.json()
        events = data.get('events', {})
        return events.get(event_id)


def parse_total_market(market_data):
    """Parse total market data into structured format"""
    if not market_data:
        return []

    totals = []
    for specifier, outcomes in market_data.items():
        # Parse specifier like "total=5.5"
        if 'total=' in specifier:
            try:
                line = float(specifier.split('=')[1])
                over_odds = outcomes.get('12', {}).get('k')
                under_odds = outcomes.get('13', {}).get('k')

                if over_odds and under_odds:
                    totals.append({
                        'line': line,
                        'over': float(over_odds),
                        'under': float(under_odds)
                    })
            except:
                pass

    # Sort by line
    totals.sort(key=lambda x: x['line'])
    return totals


def format_event(event_id: str, event_data: dict, tournaments: dict):
    """Format event data for API response"""
    desc = event_data.get('desc', {})
    competitors = desc.get('competitors', [])
    markets = event_data.get('markets', {})

    if len(competitors) < 2:
        return None

    tournament_id = desc.get('tournament', '')
    tournament_name = tournaments.get(tournament_id, {}).get('name', '')

    # Determine league
    league = None
    for league_code, tourn_id in TOURNAMENTS.items():
        if tourn_id == tournament_id:
            league = league_code
            break

    home_name = competitors[0].get('name', '')
    away_name = competitors[1].get('name', '')

    return {
        'event_id': event_id,
        'league': league,
        'tournament': tournament_name,
        'scheduled': desc.get('scheduled'),
        'home_team': {
            'id': competitors[0].get('id'),
            'name': home_name,
            'abbrev': JETTON_TO_ABBREV.get(home_name),
        },
        'away_team': {
            'id': competitors[1].get('id'),
            'name': away_name,
            'abbrev': JETTON_TO_ABBREV.get(away_name),
        },
        'odds': {
            'match_total': parse_total_market(markets.get('18')),
            'home_total': parse_total_market(markets.get('19')),
            'away_total': parse_total_market(markets.get('20')),
        },
        'has_individual_totals': '19' in markets or '20' in markets,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        import asyncio

        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        league = params.get('league', [None])[0]
        event_id = params.get('event_id', [None])[0]

        try:
            if event_id:
                # Fetch specific event with detailed odds
                event = asyncio.run(fetch_event_odds(event_id))
                if not event:
                    self.send_response(404)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Event not found"}).encode())
                    return

                result = format_event(event_id, event, {})

            else:
                # Fetch all hockey events
                events, tournaments = asyncio.run(fetch_all_hockey_events())

                results = []
                for eid, ev in events.items():
                    formatted = format_event(eid, ev, tournaments)
                    if formatted:
                        # Filter by league if specified
                        if league and formatted.get('league') != league.upper():
                            continue
                        results.append(formatted)

                # Sort by scheduled time
                results.sort(key=lambda x: x.get('scheduled', 0))
                result = {'events': results, 'count': len(results)}

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "s-maxage=60, stale-while-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
