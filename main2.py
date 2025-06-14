from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

url = "https://shopee.co.id/product/177400943/20493092581"

COOKIES_FILE = "shopee_cookies.json"

chrome_options = Options()
chrome_options.add_argument("--no-sandbox") 
chrome_options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36") 

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def load_cookies(driver, cookies_file):
    try:
    
        with open(cookies_file, "r") as f:
            cookies = json.load(f)

    
        driver.get("https://shopee.co.id")
        time.sleep(2) 

    
        for cookie in cookies:
            if "sameSite" in cookie:
                del cookie["sameSite"] 
            driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
        return True
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False

def manual_login(driver):
    try:
    
        driver.get("https://shopee.co.id/buyer/login")
        print("Please log in manually in the browser and solve any CAPTCHA. Press Enter when done...")
        input() 
        time.sleep(3) 

    
        if "buyer/login" not in driver.current_url:
            print("Manual login successful!")
            return True
        else:
            print("Manual login failed. Check credentials or CAPTCHA.")
            return False
    except Exception as e:
        print(f"Manual login error: {e}")
        return False

def check_login_status(driver):
    try:
    
        driver.get("https://shopee.co.id")
        time.sleep(3) 

    
        if "buyer/login" in driver.current_url:
            print("Login status: Not authenticated (redirected to login page)")
            return False

    
        try:
            profile_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/user/']"))
            )
            if profile_element:
                print("Login status: Authenticated")
                return True
        except:
            print("Login status: Not authenticated (profile element not found)")
            return False
    except Exception as e:
        print(f"Error checking login status: {e}")
        return False

def scrape_comments_per_page(driver, url, base_xpath_pattern, page_num):
    try:
        print(f"Scraping page {page_num}...")
    
        if page_num == 1:
            driver.get(url)
        time.sleep(5) 

    
        for _ in range(5): 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) 

    
        with open(f"page_source_page{page_num}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Page source saved to page_source_page{page_num}.html for debugging.")

        comments = []
        outer_indices = [1, 2, 3, 4, 5, 6] 
        inner_indices = [2, 3, 4]          

        base_xpath = '//*[@id="sll2-normal-pdp-main"]/div/div/div/div[2]/div[3]/div/div[1]/div[2]/div/div/div[2]/div/div[2]/section[1]/div/div/div[2]/div'

        for outer_idx in outer_indices:
            for inner_idx in inner_indices:
            
                if page_num == 1:
                    xpath = f"{base_xpath}/div[{outer_idx}]/div/div[3]/div[{inner_idx}]"
                else: 
                    xpath = f"{base_xpath}/div[{outer_idx}]/div[2]/div[4]/div[{inner_idx}]" if inner_idx in [2, 3, 4] else f"{base_xpath}/div[{outer_idx}]/div/div[3]/div[{inner_idx}]"
                try:
                
                    comment_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    comment_text = comment_element.text.strip()
                    if comment_text:
                        comments.append(comment_text)
                        print(f"Found comment at {xpath}: {comment_text}")
                    else:
                        print(f"No text found at {xpath}. Skipping.")
                except:
                    print(f"No comment found at {xpath}. Skipping.")

        if not comments:
            print(f"No comments found on page {page_num}. Check XPath indices in page_source_page{page_num}.html.")

        return comments

    except Exception as e:
        print(f"Scraping error on page {page_num}: {e}")
        return []

def scrape_comments_across_pages(driver, url, base_xpath_pattern):
    try:
        all_comments = []
        max_pages = 5 

        for page_num in range(1, max_pages + 1):
            comments = scrape_comments_per_page(driver, url, base_xpath_pattern, page_num)
            all_comments.extend(comments)

            if page_num < max_pages:
                try:
                    next_button_xpath = '//*[@id="sll2-normal-pdp-main"]/div/div/div/div[2]/div[3]/div/div[1]/div[2]/div/div/div[2]/div/div[2]/section[1]/div/div/div[2]/nav/button[8]'
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, next_button_xpath))
                    )
                    actions = ActionChains(driver)
                    actions.move_to_element(next_button).click().perform()
                    time.sleep(5) 
                except:
                    print(f"No next page found or reached the end at page {page_num}. Stopping.")
                    break

            if not comments and page_num > 1:
                print(f"No new comments found on page {page_num}. Stopping.")
                break

        if not all_comments:
            print("No comments found across pages. Check XPath indices in page_source files or login status.")

        return all_comments

    except Exception as e:
        print(f"General scraping error: {e}")
        return []

try:

    if load_cookies(driver, COOKIES_FILE) and check_login_status(driver):
        print("Proceeding with cookie-based authentication.")
    else:
        print("Cookie-based authentication failed. Falling back to manual login.")
        if not manual_login(driver):
            raise Exception("Login failed. Cannot proceed with scraping.")


    base_xpath_pattern = '//*[@id="sll2-normal-pdp-main"]/div/div/div/div[2]/div[3]/div/div[1]/div[2]/div/div/div[2]/div/div[2]/section[1]/div/div/div[2]/div/div[loopingthis]/div/div[3]/div[loopingthis]'
    comments = scrape_comments_across_pages(driver, url, base_xpath_pattern)


    for i, comment in enumerate(comments, 1):
        print(f"Comment {i}: {comment}")


    if comments:
        with open("shopee_comments.txt", "w", encoding="utf-8") as f:
            for comment in comments:
                f.write(comment + "\n")
        print("Comments saved to shopee_comments.txt")
    else:
        print("No comments were scraped.")

except Exception as e:
    print(f"General error: {e}")

finally:
    driver.quit()