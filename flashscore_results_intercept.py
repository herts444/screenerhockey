#!/usr/bin/env python3
"""
Intercept Flashscore Results page API calls
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
    chrome_options = Options()
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    print("Starting Chrome browser...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    driver.set_window_size(1400, 900)

    # Go directly to KHL results page
    results_urls = [
        ("https://www.flashscore.com/hockey/russia/khl/results/", "KHL Results"),
        ("https://www.flashscore.com/hockey/czech-republic/extraliga/results/", "Czech Results"),
    ]

    all_api_requests = []

    for url, name in results_urls:
        print(f"\nVisiting: {name} - {url}")

        try:
            driver.get(url)
            time.sleep(4)  # Wait for page load

            # Try to load more results
            try:
                show_more = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.event__more"))
                )
                show_more.click()
                print("  Clicked 'Show more'")
                time.sleep(3)
            except:
                print("  No 'Show more' button or already showing all")

        except Exception as e:
            print(f"  Error: {e}")

    # Get all performance logs
    print("\n\nCollecting network logs...")
    logs = driver.get_log('performance')

    for entry in logs:
        try:
            log = json.loads(entry['message'])['message']

            if log['method'] == 'Network.requestWillBeSent':
                url = log['params']['request']['url']
                headers = log['params']['request'].get('headers', {})

                if any(keyword in url.lower() for keyword in ['feed', '/x/', 'd.flashscore', 'flashscore.ninja']):
                    all_api_requests.append({
                        'url': url,
                        'method': log['params']['request']['method'],
                        'headers': headers
                    })

        except:
            continue

    # Print captured requests
    print("\n" + "="*60)
    print("FEED REQUESTS:")
    print("="*60)

    seen_urls = set()
    for req in all_api_requests:
        url = req['url']
        if url not in seen_urls and '/feed/' in url:
            seen_urls.add(url)
            print(f"\n{url}")
            if 'headers' in req:
                for key, val in req['headers'].items():
                    if key.lower().startswith('x-'):
                        print(f"  {key}: {val}")

    driver.quit()
    print("\nDone!")

if __name__ == "__main__":
    main()
