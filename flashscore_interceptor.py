#!/usr/bin/env python3
"""
Selenium script to intercept Flashscore API requests.
Opens browser and captures all XHR/Fetch requests.

Run this script, browse flashscore.com/hockey/, click on different leagues,
then press Enter in the terminal to see captured API calls.
"""

import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def main():
    # Setup Chrome with DevTools Protocol enabled
    chrome_options = Options()
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    print("Starting Chrome browser...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    print("\n" + "="*60)
    print("Browser opened! Instructions:")
    print("1. Go to https://www.flashscore.com/hockey/")
    print("2. Click on leagues: KHL, Czech Extraliga, Denmark Metal Ligaen, Austria ICE")
    print("3. Click on 'Results' or 'Fixtures' tabs")
    print("4. When done, come back here and press ENTER")
    print("="*60 + "\n")

    # Navigate to flashscore hockey page
    driver.get("https://www.flashscore.com/hockey/")

    # Wait for user to browse
    input("\nPress ENTER when you're done browsing to see captured requests...\n")

    # Get all performance logs
    logs = driver.get_log('performance')

    api_requests = []

    for entry in logs:
        try:
            log = json.loads(entry['message'])['message']

            # Look for network requests
            if log['method'] == 'Network.requestWillBeSent':
                url = log['params']['request']['url']

                # Filter for API-like requests
                if any(keyword in url.lower() for keyword in ['feed', 'api', 'json', 'data', 'ajax', 'd.flashscore', 'cjs.flashscore']):
                    api_requests.append({
                        'url': url,
                        'method': log['params']['request']['method'],
                        'headers': log['params']['request'].get('headers', {})
                    })

            # Also check response bodies
            if log['method'] == 'Network.responseReceived':
                url = log['params']['response']['url']
                if any(keyword in url.lower() for keyword in ['feed', 'api', 'json', 'data']):
                    if url not in [r['url'] for r in api_requests]:
                        api_requests.append({
                            'url': url,
                            'method': 'GET',
                            'status': log['params']['response']['status']
                        })

        except Exception as e:
            continue

    # Print captured requests
    print("\n" + "="*60)
    print(f"CAPTURED API REQUESTS ({len(api_requests)} total):")
    print("="*60)

    # Deduplicate and print
    seen_urls = set()
    for req in api_requests:
        url = req['url']
        if url not in seen_urls:
            seen_urls.add(url)
            print(f"\nURL: {url}")
            print(f"Method: {req.get('method', 'N/A')}")
            if 'headers' in req and req['headers']:
                # Show important headers
                important_headers = ['x-fsign', 'x-token', 'authorization', 'x-api-key']
                for h in important_headers:
                    for key, val in req['headers'].items():
                        if h in key.lower():
                            print(f"Header {key}: {val}")

    # Save to file
    output_file = '/Users/mac/Documents/nhl/flashscore_requests.json'
    with open(output_file, 'w') as f:
        json.dump(list(seen_urls), f, indent=2)
    print(f"\n\nAll unique URLs saved to: {output_file}")

    # Keep browser open for manual inspection
    input("\nPress ENTER to close browser...")
    driver.quit()

if __name__ == "__main__":
    main()
