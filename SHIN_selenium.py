import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def post_to_x(text):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        # 1. まずXのドメインにアクセス（Cookieをセットするために必要）
        driver.get("https://x.com")
        time.sleep(5)

        # 2. 保存したCookie(auth_token)を直接ブラウザにセット
        cookie = os.getenv("X_COOKIE_AUTH")
        driver.add_cookie({"name": "auth_token", "value": cookie, "domain": ".x.com"})
        
        # 3. 再読み込みすると、すでにログインした状態になる
        driver.refresh()
        time.sleep(5)

        print("→ ログイン済みの状態で投稿画面へ移動します")
        driver.get("https://x.com/compose/tweet")
        
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0"]')))
        t_box.send_keys(text)
        
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="tweetButton"]')))
        btn.click()
        time.sleep(5)
        print("★投稿成功！")

    except Exception as e:
        print(f"!!! 失敗: {e}")
    finally:
        driver.quit()
