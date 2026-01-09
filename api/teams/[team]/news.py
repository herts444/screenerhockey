"""GET /api/teams/[team]/news - Get team news from official website"""
from http.server import BaseHTTPRequestHandler
import json
import asyncio
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

# DEL team news sources
DEL_NEWS_SOURCES = {
    "MAN": {
        "name": "Adler Mannheim",
        "news_url": "https://www.adler-mannheim.de/aktuelles",
        "parser": "generic",
    },
    "AEV": {
        "name": "Augsburger Panther",
        "news_url": "https://www.aev-panther.de/panther/news.html",
        "parser": "generic",
    },
    "DRESDNER": {
        "name": "Dresdner Eislöwen",
        "news_url": "https://www.eisloewen.de/saison/news",
        "parser": "generic",
    },
    "RBM": {
        "name": "EHC Red Bull München",
        "news_url": "https://www.redbullmuenchen.de/de/news",
        "parser": "generic",
    },
    "EBB": {
        "name": "Eisbären Berlin",
        "news_url": "https://www.eisbaeren.de/aktuelle-nachrichten",
        "parser": "eisbaeren",
    },
    "ING": {
        "name": "ERC Ingolstadt",
        "news_url": "https://www.erc-ingolstadt.de/news",
        "parser": "generic",
    },
    "BHV": {
        "name": "Fischtown Pinguins",
        "news_url": "https://fischtown-pinguins.de/news/",
        "parser": "generic",
    },
    "WOB": {
        "name": "Grizzlys Wolfsburg",
        "news_url": "https://www.grizzlys.de/newsarchiv.html",
        "parser": "generic",
    },
    "IEC": {
        "name": "Iserlohn Roosters",
        "news_url": "https://iserlohn-roosters.de/saison/news/",
        "parser": "generic",
    },
    "KEC": {
        "name": "Kölner Haie",
        "news_url": "https://www.haie.de/news/",
        "parser": "generic",
    },
    "FRA": {
        "name": "Löwen Frankfurt",
        "news_url": "https://www.loewen-frankfurt.de/saison/aktuelles",
        "parser": "generic",
    },
    "NIT": {
        "name": "Nürnberg Ice Tigers",
        "news_url": "https://icetigers.de/news/",
        "parser": "generic",
    },
    "SWW": {
        "name": "Schwenninger Wild Wings",
        "news_url": "https://www.schwenninger-wildwings.de/aktuell",
        "parser": "generic",
    },
    "STR": {
        "name": "Straubing Tigers",
        "news_url": "https://www.straubing-tigers.de/category/news/",
        "parser": "wordpress",
    },
}

# Words that indicate junk/navigation items (not real news)
JUNK_WORDS = [
    "newsletter", "anmeldung", "registrierung", "liveticker", "ticker",
    "trainingszeiten", "training", "kontakt", "impressum", "datenschutz",
    "cookies", "shop", "tickets", "fanshop", "login", "mehr laden",
    "aktuelle nachrichten", "weitere", "alle news", "archiv"
]


def is_junk_title(title: str) -> bool:
    """Check if title is navigation/junk item, not real news"""
    title_lower = title.lower()
    # Too short titles are usually junk
    if len(title) < 15:
        return True
    # Check for junk words
    for word in JUNK_WORDS:
        if word in title_lower:
            return True
    return False

async def translate_text(text: str, client: httpx.AsyncClient) -> str:
    """Translate text from German to Russian using Google Translate API"""
    if not text or len(text.strip()) < 3:
        return text
    try:
        # Use Google Translate free API
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "de",
            "tl": "ru",
            "dt": "t",
            "q": text
        }
        response = await client.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            translated = "".join([part[0] for part in result[0] if part[0]])
            return translated
        return text
    except Exception:
        return text


def parse_german_date(date_str: str) -> str:
    """Parse German date formats to ISO format"""
    if not date_str:
        return ""

    date_str = date_str.strip()

    formats = [
        "%d.%m.%Y",
        "%d. %B %Y",
        "%d.%m.%Y, %H:%M",
        "%Y-%m-%d",
    ]

    german_months = {
        "Januar": "01", "Februar": "02", "März": "03", "April": "04",
        "Mai": "05", "Juni": "06", "Juli": "07", "August": "08",
        "September": "09", "Oktober": "10", "November": "11", "Dezember": "12"
    }

    for de_month, num in german_months.items():
        if de_month in date_str:
            date_str = date_str.replace(de_month, num)

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return date_str


async def parse_wordpress_news(html: str, base_url: str, client: httpx.AsyncClient) -> list:
    """Parse WordPress-based news pages (like Straubing Tigers)"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    for card in soup.select('article, .post, .entry, [class*="post"]')[:15]:
        try:
            title_el = card.select_one('h2, h3, .entry-title')
            link_el = card.select_one('a[href]')
            date_el = card.select_one('time, .entry-date, .posted-on')
            desc_el = card.select_one('.entry-content p, .entry-summary p, .excerpt')

            if not title_el:
                continue

            title = title_el.get_text(strip=True)

            # Skip junk
            if is_junk_title(title):
                continue

            link = link_el.get('href', '') if link_el else ''
            date = parse_german_date(date_el.get_text(strip=True) if date_el else '')
            excerpt = desc_el.get_text(strip=True)[:300] if desc_el else ''

            title_ru = await translate_text(title, client)

            articles.append({
                "title": title,
                "title_ru": title_ru,
                "link": link,
                "date": date,
            })
        except Exception:
            continue

    return articles


async def parse_eisbaeren_news(html: str, base_url: str, client: httpx.AsyncClient) -> list:
    """Parse Eisbären Berlin news - specific structure"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    # Look for news teasers with specific class
    for card in soup.select('.news-teaser, .teaser-news, article.news, .news-item')[:15]:
        try:
            title_el = card.select_one('h2, h3, .headline, .news-title, a')
            link_el = card.select_one('a[href*="news"]')
            date_el = card.select_one('.date, time, [class*="date"]')

            if not title_el:
                continue

            title = title_el.get_text(strip=True)

            # Skip junk
            if is_junk_title(title):
                continue

            link = link_el.get('href', '') if link_el else ''
            if link and not link.startswith('http'):
                link = base_url.rstrip('/') + link

            date = parse_german_date(date_el.get_text(strip=True) if date_el else '')

            title_ru = await translate_text(title, client)

            articles.append({
                "title": title,
                "title_ru": title_ru,
                "link": link,
                "date": date,
            })
        except Exception:
            continue

    return articles


async def parse_generic_news(html: str, base_url: str, client: httpx.AsyncClient) -> list:
    """Generic parser for news pages"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    selectors = [
        'article',
        '.news-item',
        '.news-teaser',
        '.teaser',
        '.post',
        '[class*="news-card"]',
        '[class*="newsitem"]',
        '.teaser-item',
        '.content-item',
    ]

    cards = []
    for sel in selectors:
        cards = soup.select(sel)[:15]
        if cards:
            break

    if not cards:
        links = soup.select('a[href*="news"], a[href*="aktuell"], a[href*="meldung"]')
        for link in links[:15]:
            parent = link.find_parent(['article', 'div', 'li'])
            if parent and parent not in cards:
                cards.append(parent)

    for card in cards[:15]:
        try:
            title_el = card.select_one('h2, h3, h4, .title, [class*="title"], [class*="headline"]')
            link_el = card.select_one('a[href]')
            date_el = card.select_one('time, .date, [class*="date"], [class*="datum"]')

            if not title_el:
                if link_el:
                    title = link_el.get_text(strip=True)
                else:
                    continue
            else:
                title = title_el.get_text(strip=True)

            if not title or len(title) < 5:
                continue

            # Skip junk
            if is_junk_title(title):
                continue

            link = link_el.get('href', '') if link_el else ''
            if link and not link.startswith('http'):
                link = base_url.rstrip('/') + '/' + link.lstrip('/')

            date = parse_german_date(date_el.get_text(strip=True) if date_el else '')

            title_ru = await translate_text(title, client)

            articles.append({
                "title": title,
                "title_ru": title_ru,
                "link": link,
                "date": date,
            })
        except Exception:
            continue

    return articles


async def fetch_team_news(team_abbrev: str, limit: int = 5) -> dict:
    """Fetch news for a DEL team"""
    source = DEL_NEWS_SOURCES.get(team_abbrev.upper())
    if not source:
        return {"error": f"Team {team_abbrev} not found in DEL"}

    news_url = source["news_url"]
    parser_type = source.get("parser", "generic")
    base_url = "/".join(news_url.split("/")[:3])

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = await client.get(news_url, headers=headers)
        response.raise_for_status()
        html = response.text

        if parser_type == "wordpress":
            articles = await parse_wordpress_news(html, base_url, client)
        elif parser_type == "eisbaeren":
            articles = await parse_eisbaeren_news(html, base_url, client)
        else:
            articles = await parse_generic_news(html, base_url, client)

    return {
        "team": team_abbrev.upper(),
        "team_name": source["name"],
        "articles": articles[:limit],
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        match = re.search(r'/api/teams/([^/]+)/news', self.path)
        if not match:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid path"}).encode())
            return

        team_abbrev = match.group(1).upper()
        league = params.get("league", ["DEL"])[0].upper()
        limit = int(params.get("limit", ["5"])[0])

        if league != "DEL":
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Only DEL league news is supported currently"}).encode())
            return

        try:
            result = asyncio.run(fetch_team_news(team_abbrev, limit))

            if "error" in result:
                self.send_response(404)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "s-maxage=300, stale-while-revalidate")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
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
