
# x_scraper.py - Updated for web application

def run_x_scraper(tag, scroll, task_id):
    import re
    import time
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    from bs4 import BeautifulSoup
    import os

    def start_driver(headless=False):
        user_data_dir = os.path.join(os.getcwd(), f"x_scraper_profile_{task_id}")
        options = Options()

        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        #options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--profile-directory=Default")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def wait_for_flag(task_id):
        flag_file = f"flag_{task_id}.txt"
        print(f"🔐 Waiting for flag file: {flag_file}")
        while True:
            if os.path.exists(flag_file):
                with open(flag_file, "r") as f:
                    if f.read().strip().lower() == "done":
                        break
            time.sleep(1)
        print("✅ Signal received. Continuing with scraping...")

    # def collect_tweet_urls(driver, scroll_times):
    #     print("🔁 Scrolling to collect tweet URLs...")
    #     tweet_urls = set()
    #
    #     for _ in range(scroll_times):
    #         time.sleep(3)
    #         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #         time.sleep(10)
    #
    #         tweet_elements = driver.find_elements(By.XPATH, '//a[contains(@href, "/status/")]')
    #         for tweet in tweet_elements:
    #             try:
    #                 href = tweet.get_attribute("href")
    #                 if href and "/status/" in href:
    #                     href = href.split("?")[0].rstrip('/')
    #                     if href.endswith("/analytics"):
    #                         href = href.replace("/analytics", "")
    #                     if href.endswith("/media_tags"):
    #                         href = href.replace("/media_tags", "")
    #                     tweet_urls.add(href)
    #             except Exception:
    #                 continue
    #
    #     print(f"✅ Collected {len(tweet_urls)} tweet URLs.")
    #     return list(tweet_urls)

    def collect_tweet_urls(driver, scroll_times):
        print("🔁 Scrolling to collect tweet URLs...")
        tweet_urls = set()

        for _ in range(scroll_times):
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(10)

            tweet_elements = driver.find_elements(By.XPATH, '//a[contains(@href, "/status/")]')
            for tweet in tweet_elements:
                try:
                    href = tweet.get_attribute("href")
                    if href and "/status/" in href:
                        # Clean the URL and extract base tweet URL
                        clean_url = clean_tweet_url(href)
                        if clean_url:
                            tweet_urls.add(clean_url)
                except Exception:
                    continue

        print(f"✅ Collected {len(tweet_urls)} unique tweet URLs.")
        return list(tweet_urls)

    def clean_tweet_url(url):
        """
        Clean tweet URL to remove duplicates from multi-photo posts

        Examples:
        - https://twitter.com/user/status/123/photo/1 -> https://twitter.com/user/status/123
        - https://twitter.com/user/status/123/photo/2 -> https://twitter.com/user/status/123
        - https://twitter.com/user/status/123/video/1 -> https://twitter.com/user/status/123
        - https://twitter.com/user/status/123?s=20 -> https://twitter.com/user/status/123
        """
        if not url or "/status/" not in url:
            return None

        # Remove query parameters
        url = url.split("?")[0].rstrip('/')

        # Remove trailing slash
        url = url.rstrip('/')

        # Remove specific suffixes that cause duplicates
        suffixes_to_remove = [
            "/analytics",
            "/media_tags",
            "/retweets",
            "/quotes",
            "/likes",
            "/history"
        ]

        for suffix in suffixes_to_remove:
            if url.endswith(suffix):
                url = url.replace(suffix, "")

        # Remove photo/video indices (photo/1, photo/2, video/1, etc.)
        # Pattern: /photo/\d+ or /video/\d+
        url = re.sub(r'/photo/\d+$', '', url)
        url = re.sub(r'/video/\d+$', '', url)

        # Ensure it's a valid tweet status URL
        if re.match(r'https?://(?:twitter\.com|x\.com)/\w+/status/\d+$', url):
            return url

        return None

    def extract_user_info_from_tweet(driver, tweet_url):
        data = {
            "Name": "Unknown",
            "Tweet URL": tweet_url,
            "Email": "Not Available",
            "Contact": "Not Available"
        }

        try:
            if "/photo/" in tweet_url:
                tweet_url = tweet_url.split("/photo/")[0]

            driver.get(tweet_url)
            time.sleep(15)

            # Extract name
            try:
                data["Name"] = driver.find_element(By.XPATH, '//div[@data-testid="User-Name"]//span').text.strip()
            except:
                data["Name"] = "Not Available"

            # Extract email and contact from page
            try:
                full_page_text = driver.find_element(By.TAG_NAME, "body").text

                email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_page_text)
                if email_match:
                    data["Email"] = email_match.group(0)

                contact_match = re.search(r"((?:\+9\d{1,3}|\(?0\d{2,4}\)?) ?\d{3,4}(?: ?\d{3,4}){1,2})", full_page_text)
                if contact_match:
                    data["Contact"] = contact_match.group(1)
            except:
                pass

            print(f"✅ {data['Name']} | {data['Email']} | {data['Contact']}")

        except Exception as e:
            print(f"❌ Failed to process {tweet_url}: {e}")

        return data

    def save_to_csv(data, task_id):
        df = pd.DataFrame(data)
        filename = f"x_results_{task_id}.csv"
        df.to_csv(filename, index=False)
        print(f"📧 Results saved to: {filename}")
        return filename

    # Main execution
    print(f"📌 Scraping hashtag: #{tag}")
    driver = start_driver(headless=False)

    try:
        driver.get("https://x.com/login")
        wait_for_flag(task_id)

        driver.get(f"https://x.com/search?q=%23{tag}&src=typed_query")
        time.sleep(5)

        tweet_urls = collect_tweet_urls(driver, scroll_times=scroll)
        print(f"✅ Found {len(tweet_urls)} tweet URLs.")

        results = []
        for url in tweet_urls:
            print(f"🔍 Extracting from: {url}")
            info = extract_user_info_from_tweet(driver, url)
            results.append(info)
            time.sleep(15)

        filename = save_to_csv(results, task_id)
        return filename

    finally:
        driver.quit()