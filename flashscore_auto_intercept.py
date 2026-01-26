#!/usr/bin/env python3
"""
Automated Selenium script to intercept Flashscore API requests.
Navigates to hockey leagues automatically and captures API calls.
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def main():
    # Setup Chrome with DevTools Protocol enabled
    chrome_options = Options()
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # Run headless for automation
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    print("Starting Chrome browser...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    driver.set_window_size(1400, 900)

    # List of league URLs to visit
    leagues = [
        ("https://www.flashscore.com/hockey/russia/khl/", "KHL"),
        ("https://www.flashscore.com/hockey/czech-republic/extraliga/", "Czech Extraliga"),
        ("https://www.flashscore.com/hockey/denmark/metal-ligaen/", "Denmark Metal Ligaen"),
        ("https://www.flashscore.com/hockey/austria/ice-hockey-league/", "Austria ICE"),
    ]

    all_api_requests = []

    for url, name in leagues:
        print(f"\n{'='*50}")
        print(f"Visiting: {name}")
        print(f"URL: {url}")
        print('='*50)

        try:
            driver.get(url)
            time.sleep(3)  # Wait for page to load

            # Try to click on Results tab
            try:
                results_tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='results']"))
                )
                results_tab.click()
                print(f"  Clicked Results tab")
                time.sleep(2)
            except:
                print(f"  Could not find Results tab")

            # Go back to main page and try Fixtures
            driver.get(url)
            time.sleep(2)

            try:
                fixtures_tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='fixtures']"))
                )
                fixtures_tab.click()
                print(f"  Clicked Fixtures tab")
                time.sleep(2)
            except:
                print(f"  Could not find Fixtures tab")

        except Exception as e:
            print(f"  Error: {e}")

    # Get all performance logs
    print("\n\nCollecting network logs...")
    logs = driver.get_log('performance')

    for entry in logs:
        try:
            log = json.loads(entry['message'])['message']

            # Look for network requests
            if log['method'] == 'Network.requestWillBeSent':
                url = log['params']['request']['url']
                headers = log['params']['request'].get('headers', {})

                # Filter for API-like requests
                if any(keyword in url.lower() for keyword in ['feed', '/x/', 'api', 'd.flashscore', 'cjs.flashscore', 'local-']):
                    all_api_requests.append({
                        'url': url,
                        'method': log['params']['request']['method'],
                        'headers': headers
                    })

        except Exception as e:
            continue

    # Print captured requests
    print("\n" + "="*60)
    print(f"CAPTURED API REQUESTS ({len(all_api_requests)} total):")
    print("="*60)

    # Deduplicate and analyze
    seen_urls = set()
    feed_requests = []

    for req in all_api_requests:
        url = req['url']
        if url not in seen_urls:
            seen_urls.add(url)

            # Highlight feed requests
            if '/feed/' in url or '/x/' in url:
                feed_requests.append(req)
                print(f"\n*** FEED REQUEST ***")
                print(f"URL: {url}")
                print(f"Method: {req.get('method', 'N/A')}")
                if 'headers' in req and req['headers']:
                    for key, val in req['headers'].items():
                        if key.lower().startswith('x-'):
                            print(f"  Header {key}: {val}")

    print("\n" + "="*60)
    print("SUMMARY - Feed URLs found:")
    print("="*60)
    for req in feed_requests:
        print(req['url'])

    # Save to file
    output_file = '/Users/mac/Documents/nhl/flashscore_requests.json'
    with open(output_file, 'w') as f:
        json.dump({
            'feed_requests': feed_requests,
            'all_urls': list(seen_urls)
        }, f, indent=2)
    print(f"\nResults saved to: {output_file}")

    driver.quit()
    print("\nDone!")

if __name__ == "__main__":
    main()
