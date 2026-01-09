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
        "news_url": "https://www.eisbaeren.de/news",
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

# Words indicating non-sports news (ads, jobs, merchandise, etc.)
NON_SPORTS_WORDS = [
    "job", "stelle", "mitarbeiter", "karriere", "bewerbung",  # jobs
    "auktion", "versteigerung", "ersteigern", "gebot",  # auctions
    "trikot", "merchandise", "fanshop", "shop", "kaufen", "bestellen",  # merchandise
    "gewinnspiel", "verlosung", "gewinne",  # contests
    "sponsor", "partner", "werbung",  # sponsors
    "busreise", "fanreise", "anreise",  # travel
    "dauerkarte", "saisonkarte", "vvk", "vorverkauf",  # tickets
    "weihnacht", "silvester", "ostern",  # holidays (usually promotional)
    "rabatt", "aktion", "angebot", "sale",  # sales
    "catering", "gastronomie", "restaurant",  # food
    "parkplatz", "parken", "anfahrt",  # logistics
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


def is_non_sports_news(title: str, content: str = "") -> bool:
    """Check if news is not about sports (ads, jobs, merchandise, etc.)"""
    text = (title + " " + content).lower()

    # Sports keywords that indicate it's a real game news
    sports_keywords = [
        "spiel", "sieg", "niederlage", "tor", "punkt", "tabelle",
        "spieltag", "derby", "playoff", "meister", "saison",
        "trainer", "spieler", "lineup", "aufstellung", "verletzt",
        "interview", "vorbericht", "nachbericht", "analyse"
    ]

    # If contains sports keywords, it's likely sports news
    for kw in sports_keywords:
        if kw in text:
            return False

    # Check for non-sports words
    non_sports_count = sum(1 for word in NON_SPORTS_WORDS if word in text)
    if non_sports_count >= 2:
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

        # Remove scripts, styles, nav, footer, buttons
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'button', 'form']):
            tag.decompose()

        # Remove "read more" links and similar
        for el in soup.select('a.more-link, .read-more, .mehr-link, [class*="more"], .social-share, .sharing'):
            el.decompose()

        content = ""

        # Site-specific selectors
        if 'eisbaeren.de' in url:
            # Eisbären Berlin specific
            selectors = ['.news-detail-text', '.news-text', '.detail-text', '.text-content',
                        '.news-detail', 'article .text', '.content-text', 'main .text']
        elif 'eisloewen.de' in url:
            selectors = ['.entry-content', '.post-content', 'article .content']
        else:
            # Generic selectors
            selectors = [
                'article .content', 'article .entry-content', '.article-content',
                '.news-content', '.post-content', '.single-content', '.news-detail',
                '.entry-content', '.text-content', '.article-text',
                'article p', '.content-main p', 'main p'
            ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                paragraphs = []
                for el in elements:
                    # Get all paragraphs within the element
                    ps = el.find_all('p')
                    if ps:
                        for p in ps:
                            text = p.get_text(strip=True)
                            if text and len(text) > 20:
                                paragraphs.append(text)
                    else:
                        # If no <p> tags, get text directly
                        text = el.get_text(strip=True)
                        if text and len(text) > 30:
                            paragraphs.append(text)

                if paragraphs:
                    content = "\n\n".join(paragraphs[:15])  # Max 15 paragraphs
                    break

        # If still no content, try getting all <p> tags from main/article
        if not content:
            main_content = soup.select_one('main, article, .content, #content')
            if main_content:
                paragraphs = []
                for p in main_content.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 30:
                        # Skip junk
                        if any(junk in text.lower() for junk in ['cookie', 'datenschutz', 'impressum', 'newsletter']):
                            continue
                        paragraphs.append(text)
                if paragraphs:
                    content = "\n\n".join(paragraphs[:15])

        # Clean up content
        content = content.replace('...Подробнее', '').replace('...Mehr', '')
        if content.endswith('Подробнее'):
            content = content[:-9].rstrip()
        if content.endswith('Mehr'):
            content = content[:-4].rstrip()

        # Limit content length
        if len(content) > 3000:
            content = content[:3000] + "..."

        return content
    except Exception as e:
        print(f"  Error fetching article: {e}")
        return ""


async def parse_eisbaeren_berlin(html: str, base_url: str) -> list:
    """Special parser for Eisbären Berlin website"""
    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    # Try finding news items by various patterns
    news_items = soup.select('.news-teaser, .teaser-item, article, .post')
    if not news_items:
        # Try finding by link patterns
        news_items = soup.select('a[href*="/news/"], a[href*="/nachrichten/"]')

    for item in news_items[:10]:
        try:
            if item.name == 'a':
                link = item.get('href', '')
                title = item.get_text(strip=True)
            else:
                link_el = item.select_one('a[href]')
                title_el = item.select_one('h2, h3, h4, .title, .headline')
                link = link_el.get('href', '') if link_el else ''
                title = title_el.get_text(strip=True) if title_el else ''

            if not title or is_junk_title(title):
                continue

            if link and not link.startswith('http'):
                link = base_url.rstrip('/') + '/' + link.lstrip('/')

            articles.append({"title": title, "link": link, "date": ""})

            if len(articles) >= 5:
                break
        except Exception:
            continue

    return articles


async def parse_news_list(html: str, base_url: str, team_abbrev: str = "") -> list:
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

    for card in cards[:10]:  # Check more cards to filter later
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

        # Use special parser for Eisbären Berlin
        if team_abbrev == "EBB":
            articles = await parse_eisbaeren_berlin(html, base_url)
        else:
            articles = await parse_news_list(html, base_url, team_abbrev)

        # Fetch full content, filter and translate
        filtered_articles = []
        for article in articles:
            if article["link"]:
                print(f"  Fetching article {articles.index(article) + 1}...")
                content = await fetch_article_content(article["link"], client)
                article["content"] = content

                # Filter out non-sports news
                if is_non_sports_news(article["title"], content):
                    print(f"    Skipped (non-sports): {article['title'][:40]}...")
                    continue

                # Translate title and content
                article["title_ru"] = await translate_text(article["title"], client)
                if content:
                    article["content_ru"] = await translate_text(content[:2500], client)
                else:
                    article["content_ru"] = ""

                filtered_articles.append(article)

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)

                # Limit to 5 sports news per team
                if len(filtered_articles) >= 5:
                    break

        return {
            "team": team_abbrev,
            "team_name": source["name"],
            "articles": filtered_articles,
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
