
# instagram_scraper.py - Updated for web application

def run_instagram_scraper(tag, scroll, task_id):
    import re
    import time
    import pandas as pd
    import os
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.wait import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager

    def start_driver(headless=False):
        user_data_dir = os.path.join(os.getcwd(), f"instagram_profile_data_{task_id}")
        options = Options()

        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        #options.add_argument("--headless")
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

    def scroll_on_hashtag(driver, scroll_times):
        post_urls = set()
        for i in range(scroll_times):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(15)

            fresh_links = driver.find_elements(By.XPATH, '//a[contains(@href, "/p/")]')
            for link in fresh_links:
                try:
                    href = link.get_attribute("href")
                    if href and "/p/" in href:
                        post_urls.add(href.split("?")[0])
                except:
                    continue

            print(f"🔁 Scroll {i + 1}/{scroll_times} — Posts found: {len(post_urls)}")

        return list(post_urls)

    def extract_info_from_post(driver, post_url):
        try:
            driver.get(post_url)
            time.sleep(10)
            driver.execute_script("document.body.style.zoom='67%'")

            data = {
                "Name": "Not Available",
                "Profile URL": "Not Available",
                "Post URL": post_url,
                "Email": "Not Available",
                "Contact": "Not Available"
            }

            # Extract profile information
            try:
                profile_page = driver.page_source
                email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', profile_page)
                if email_matches:
                    data["Email"] = email_matches[0]

                contact_matches = re.findall(r'(\+92|03)[0-9()\s-]{7,}', profile_page)
                if contact_matches:
                    data["Contact"] = contact_matches[0]
                try:
                    time.sleep(5)
                    bio_elem = driver.find_element(By.XPATH, '//section//div[contains(text(), "")]')
                    bio = bio_elem.text.strip()
                    # print(bio)
                    username = bio.strip().split()[0]  # first word from first line
                    data["Name"] = username
                    print(username)
                    profile_url = f"https://www.instagram.com/{username}/"
                    data["Profile URL"] = profile_url
                    full_text = username + "\n" + bio

                    if(data["Email"]=="Not Available"):
                        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text)
                        if email_match:
                            data["Email"] = email_match.group(0)

                        contact_match = re.search(r"((?:\+9\d{1,3}|\(?0\d{2,4}\)?) ?\d{3,4}(?: ?\d{3,4}){1,2})", full_text)
                        if contact_match:
                            data["Contact"] = contact_match.group(1)
                        print(" From Post Text")
                        print(data)
                    if (data["Email"] == "Not Available"):
                        driver.get(profile_url)
                        time.sleep(10)
                        driver.execute_script("document.body.style.zoom='67%'")
                        print(f"👤 Profile: {profile_url}")

                        profile_page = driver.page_source
                        email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', profile_page)
                        if email_matches:
                            data["Email"] = email_matches[0]

                        # Search in all elements that might contain the number
                        elements = driver.find_elements(By.XPATH,
                                                        '//body//*[contains(text(), "+9") or contains(text(), "03") or contains(text(), "(04")]')

                        contact = "Not Available"
                        for el in elements:
                            try:
                                text = el.text.strip()
                                match = re.search(r'(\+92|03)[0-9()\s-]{7,}', text)
                                if match:
                                    data["Contact"] = match.group(0)
                                    break
                            except:
                                continue
                        print(" From profile page")
                        print(data)


                except:
                    bio = ""


            except Exception as e:
                print(f"⚠️ Error extracting info: {e}")

            return data

        except Exception as e:
            print(f"⚠️ Error with {post_url}: {e}")
            return {
                "Name": "Error",
                "Profile URL": "Error",
                "Post URL": post_url,
                "Email": "Error",
                "Contact": "Error"
            }

    def save_to_csv(data, task_id):
        df = pd.DataFrame(data)
        filename = f"instagram_results_{task_id}.csv"
        df.to_csv(filename, index=False)
        return filename

    # Main execution
    print(f"🔍 Scraping Instagram for #{tag} with {scroll} scrolls")
    driver = start_driver(headless=False)

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        wait_for_flag(task_id)

        driver.get(f"https://www.instagram.com/explore/tags/{tag}/")
        time.sleep(5)

        post_urls = scroll_on_hashtag(driver, scroll_times=scroll)
        print(f"✅ Total posts collected: {len(post_urls)}")

        results = []
        for idx, post_url in enumerate(post_urls):
            print(f"🔍 [{idx + 1}/{len(post_urls)}] Processing: {post_url}")
            data = extract_info_from_post(driver, post_url)
            results.append(data)
            time.sleep(5)

        filename = save_to_csv(results, task_id)
        print(f"📁 Saved to: {filename}")
        return filename

    finally:
        driver.quit()
