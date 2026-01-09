#!/usr/bin/env python3
"""
Fetch news from DEL team websites with full article content.
Saves to data/news_cache.json for API to read.
Run via GitHub Actions every hour.
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

# DEL team news sources
DEL_NEWS_SOURCES = {
    "MAN": {
        "name": "Adler Mannheim",
        "news_url": "https://www.adler-mannheim.de/aktuelles",
    },
    "AEV": {
        "name": "Augsburger Panther",
        "news_url": "https://www.aev-panther.de/panther/news.html",
    },
    "DRESDNER": {
        "name": "Dresdner Eislöwen",
        "news_url": "https://www.eisloewen.de/saison/news",
    },
    "RBM": {
        "name": "EHC Red Bull München",
        "news_url": "https://www.redbullmuenchen.de/de/news",
    },
    "EBB": {
        "name": "Eisbären Berlin",
        "news_url": "https://www.eisbaeren.de/aktuelle-nachrichten",
    },
    "ING": {
        "name": "ERC Ingolstadt",
        "news_url": "https://www.erc-ingolstadt.de/news",
    },
    "BHV": {
        "name": "Fischtown Pinguins",
        "news_url": "https://fischtown-pinguins.de/news/",
    },
    "WOB": {
        "name": "Grizzlys Wolfsburg",
        "news_url": "https://www.grizzlys.de/newsarchiv.html",
    },
    "IEC": {
        "name": "Iserlohn Roosters",
        "news_url": "https://iserlohn-roosters.de/saison/news/",
    },
    "KEC": {
        "name": "Kölner Haie",
        "news_url": "https://www.haie.de/news/",
    },
    "FRA": {
        "name": "Löwen Frankfurt",
        "news_url": "https://www.loewen-frankfurt.de/saison/aktuelles",
    },
    "NIT": {
        "name": "Nürnberg Ice Tigers",
        "news_url": "https://icetigers.de/news/",
    },
    "SWW": {
        "name": "Schwenninger Wild Wings",
        "news_url": "https://www.schwenninger-wildwings.de/aktuell",
    },
    "STR": {
        "name": "Straubing Tigers",
        "news_url": "https://www.straubing-tigers.de/category/news/",
    },
}

JUNK_WORDS = [
    "newsletter", "anmeldung", "registrierung", "liveticker", "ticker",
    "trainingszeiten", "kontakt", "impressum", "datenschutz",
    "cookies", "shop", "tickets", "fanshop", "login", "mehr laden",
    "aktuelle nachrichten", "weitere", "alle news", "archiv"
]


def is_junk_title(title: str) -> bool:
    """Check if title is junk"""
    title_lower = title.lower()
    if len(title) < 15:
        return True
    for word in JUNK_WORDS:
        if word in title_lower:
            return True
    return False


async def translate_text(text: str, client: httpx.AsyncClient) -> str:
    """Translate German to Russian"""
    if not text or len(text.strip()) < 3:
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "de", "tl": "ru", "dt": "t", "q": text}
        response = await client.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            return "".join([part[0] for part in result[0] if part[0]])
        return text
    except Exception:
        return text


def parse_german_date(date_str: str) -> str:
    """Parse German date to ISO format"""
    if not date_str:
        return ""

    date_str = date_str.strip()
    german_months = {
        "Januar": "01", "Februar": "02", "März": "03", "April": "04",
        "Mai": "05", "Juni": "06", "Juli": "07", "August": "08",
        "September": "09", "Oktober": "10", "November": "11", "Dezember": "12"
    }

    for de_month, num in german_months.items():
        if de_month in date_str:
            date_str = date_str.replace(de_month, num)

    for fmt in ["%d.%m.%Y", "%d. %B %Y", "%d.%m.%Y, %H:%M", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


async def fetch_article_content(url: str, client: httpx.AsyncClient) -> str:
    """Fetch full article content from URL"""
    try:
        response = await client.get(url, timeout=15.0)
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove scripts, styles, nav, footer
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # Try common article content selectors
        content_selectors = [
            'article .content', 'article .entry-content', '.article-content',
            '.news-content', '.post-content', '.single-content',
            'article p', '.content-main p', 'main p'
        ]

        content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                paragraphs = []
                for el in elements:
                    text = el.get_text(strip=True)
                    if text and len(text) > 30:
                        paragraphs.append(text)
                if paragraphs:
                    content = "\n\n".join(paragraphs[:10])  # Max 10 paragraphs
                    break

        # Limit content length
        if len(content) > 2000:
            content = content[:2000] + "..."

        return content
    except Exception as e:
        print(f"  Error fetching article: {e}")
        return ""


async def parse_news_list(html: str, base_url: str) -> list:
    """Parse news list page to get article links"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    # Try various selectors
    selectors = ['article', '.news-item', '.news-teaser', '.teaser', '.post']
    cards = []

    for sel in selectors:
        cards = soup.select(sel)[:10]
        if cards:
            break

    if not cards:
        links = soup.select('a[href*="news"], a[href*="aktuell"], a[href*="meldung"]')
        for link in links[:10]:
            parent = link.find_parent(['article', 'div', 'li'])
            if parent and parent not in cards:
                cards.append(parent)

    for card in cards[:5]:  # Only 5 articles per team
        try:
            title_el = card.select_one('h2, h3, h4, .title, [class*="title"], [class*="headline"]')
            link_el = card.select_one('a[href]')
            date_el = card.select_one('time, .date, [class*="date"]')

            title = title_el.get_text(strip=True) if title_el else (link_el.get_text(strip=True) if link_el else "")

            if not title or is_junk_title(title):
                continue

            link = link_el.get('href', '') if link_el else ''
            if link and not link.startswith('http'):
                link = base_url.rstrip('/') + '/' + link.lstrip('/')

            date = parse_german_date(date_el.get_text(strip=True) if date_el else '')

            articles.append({
                "title": title,
                "link": link,
                "date": date,
            })
        except Exception:
            continue

    return articles


async def fetch_team_news(team_abbrev: str, source: dict, client: httpx.AsyncClient) -> dict:
    """Fetch news for a single team with full content"""
    print(f"Fetching news for {team_abbrev}...")

    news_url = source["news_url"]
    base_url = "/".join(news_url.split("/")[:3])

    try:
        response = await client.get(news_url)
        response.raise_for_status()
        html = response.text

        # Get list of articles
        articles = await parse_news_list(html, base_url)

        # Fetch full content and translate for each article
        for article in articles:
            if article["link"]:
                print(f"  Fetching article {articles.index(article) + 1}...")
                content = await fetch_article_content(article["link"], client)
                article["content"] = content

                # Translate title and content
                article["title_ru"] = await translate_text(article["title"], client)
                if content:
                    article["content_ru"] = await translate_text(content[:1500], client)
                else:
                    article["content_ru"] = ""

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)

        return {
            "team": team_abbrev,
            "team_name": source["name"],
            "articles": articles,
            "updated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"  Error: {e}")
        return {
            "team": team_abbrev,
            "team_name": source["name"],
            "articles": [],
            "updated_at": datetime.utcnow().isoformat(),
            "error": str(e),
        }


async def main():
    """Main function to fetch all news"""
    print(f"Starting news fetch at {datetime.utcnow().isoformat()}")

    # Ensure data directory exists
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    cache_file = data_dir / "news_cache.json"

    # Load existing cache
    existing_cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                existing_cache = json.load(f)
        except Exception:
            pass

    all_news = {}

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    ) as client:
        for team_abbrev, source in DEL_NEWS_SOURCES.items():
            team_news = await fetch_team_news(team_abbrev, source, client)
            all_news[team_abbrev] = team_news

            # Delay between teams
            await asyncio.sleep(1)

    # Save to cache file
    cache_data = {
        "league": "DEL",
        "updated_at": datetime.utcnow().isoformat(),
        "teams": all_news,
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    print(f"News cache saved to {cache_file}")
    print(f"Finished at {datetime.utcnow().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
