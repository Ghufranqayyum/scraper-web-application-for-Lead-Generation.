# facebook_scraper.py - Updated for web application

def run_facebook_scraper(value, scroll, task_id):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    import time
    import csv
    import re
    import os

    # --- Configuration ---
    EMAIL = ''
    PASSWORD = ''
    TARGET_URL = value
    SCROLL_COUNT = scroll
    CSV_FILE = f'facebook_results_{task_id}.csv'

    # --- Setup Chrome ---
    options = Options()
    options.add_argument("--disable-notifications")
   # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

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

    def facebook_login(email, password):
        driver.get("https://www.facebook.com")
        wait.until(EC.presence_of_element_located((By.ID, "email"))).send_keys(email)
        driver.find_element(By.ID, "pass").send_keys(password)
        driver.find_element(By.NAME, "login").click()
        time.sleep(5)

    def scroll_page():
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(SCROLL_COUNT):
            time.sleep(10)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"🌀 Scrolling... ({i + 1}/{SCROLL_COUNT})")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("⏹️ No more content to load.")
                break
            last_height = new_height

    def get_post_urls(driver):
        print("🔍 Collecting full post URLs...")
        time.sleep(5)
        anchors = driver.find_elements(By.XPATH,
                                       '//a[contains(@href, "/videos/") or contains(@href, "/posts/") or contains(@href, "/photo/")]')

        post_urls = set()
        for a in anchors:
            try:
                href = a.get_attribute("href")
                if href:
                    if "/photo/" not in href:
                        href = href.split("?")[0]
                    if any(s in href for s in
                           ["/groups/", "/watch/", "/live/", "/stories/"]) or "privacy_mutation_token" in href:
                        continue
                    if "/videos/" in href or "/posts/" in href or "/photo/" in href:
                        post_urls.add(href)
            except:
                continue

        return list(post_urls)

    def save_to_csv(data):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Post URL", "Contact", "Email"])
            for row in data:
                writer.writerow(row)

    # --- Main Execution ---
    try:
        facebook_login(EMAIL, PASSWORD)
        time.sleep(10)

        # Wait for manual action completion
        wait_for_flag(task_id)

        driver.get(TARGET_URL)
        time.sleep(10)
        driver.execute_script("document.body.style.zoom='67%'")

        scroll_page()
        post_urls = get_post_urls(driver)

        results = []
        for url in post_urls:
            try:
                print(f"🔗 Processing post: {url}")
                driver.get(url)
                time.sleep(10)

                # Extract basic info
                name = "Not Available"
                email = "Not Available"
                contact = "Not Available"

                # Try to extract name
                try:
                    name_el = driver.find_element(By.XPATH, '//h2//span//span')
                    name = name_el.text.strip()
                except:
                    pass

                # Try to extract profile info
                try:
                    poster_link = driver.find_element(By.XPATH, '//h2//span//a | //strong//a | //h3//a')
                    driver.execute_script("arguments[0].click();", poster_link)
                    time.sleep(10)

                    # Try to click on the post creator's profile
                    print("🔎 Attempting to click on poster's name to visit profile...")

                    # This XPath usually matches the poster name (can vary — adjust if needed)
                    poster_link = driver.find_element(By.XPATH, '//h2//span//a | //strong//a | //h3//a')
                    driver.execute_script("arguments[0].click();", poster_link)

                    time.sleep(10)  # Wait for profile to load
                    driver.execute_script("document.body.style.zoom='60%'")

                    elements = driver.find_elements(By.XPATH, '//a[.//span[text()="About"]]')
                    print(f"Found {len(elements)} About elements")

                    about_btn = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//a[.//span[contains(text(),"About")]]'))
                    )
                    from selenium.webdriver.common.action_chains import ActionChains

                    # Reliable scroll to element using ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(about_btn).perform()
                    time.sleep(10)

                    # Safer click via JS
                    driver.execute_script("arguments[0].click();", about_btn)
                    print("✅ Clicked on About tab.")

                    time.sleep(5)
                    driver.execute_script("document.body.style.zoom='50%'")

                    # Now extract email/contact as usual
                    about_page = driver.page_source
                    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', about_page)
                    if email_matches:
                        time.sleep(5)
                        email = email_matches[0]
                    import re

                    # Search in all elements that might contain the number
                    elements = driver.find_elements(By.XPATH,
                                                    '//body//*[contains(text(), "+9") or contains(text(), "03") or contains(text(), "(04")]')

                    contact = "Not Available"
                    for el in elements:
                        try:
                            text = el.text.strip()
                            match = re.search(r'(\+92|03)[0-9()\s-]{7,}', text)
                            if match:
                                contact = match.group(0)
                                break
                        except:
                            continue

                    email = email_matches[0] if email_matches else "Not Available"


                except Exception as e:
                    print(f"⚠️ Error extracting profile info: {e}")

                results.append([name, url, contact, email])
                print(f"✅ {name} | {email} | {contact}")

            except Exception as e:
                print(f"❌ Failed processing {url}: {e}")
                results.append(["Not Available", url, "Not Available", "Not Available"])

        save_to_csv(results)
        print(f"💾 Saved {len(results)} records to {CSV_FILE}")
        return CSV_FILE

    finally:
        driver.quit()


