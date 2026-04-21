import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def post_to_x(text):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 言語を英語に固定し、人間らしいブラウザに見せかける
    chrome_options.add_argument('--lang=en-US')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 60) # 待ち時間を1分に延長

    try:
        print("--- ログイン開始 ---")
        driver.get("https://x.com/login")
        
        print("1. ユーザー名入力待ち...")
        # Xのログイン欄は複数の候補があるため、一番確実な方法で指定
        u_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']")))
        u_field.send_keys(os.getenv("X_USER_ID"))
        u_field.send_keys(Keys.ENTER)
        time.sleep(7)

        # 追加認証（メール）のチェック
        if "email" in driver.page_source.lower() or "phone" in driver.page_source.lower():
            print("→ 追加認証が必要そうです。メールを入力します。")
            try:
                sub_input = driver.find_element(By.CSS_SELECTOR, "input[data-testid='ocfEnterTextNextButton']")
                sub_input.send_keys(os.getenv("X_EMAIL"))
                sub_input.send_keys(Keys.ENTER)
                time.sleep(5)
            except: pass

        print("2. パスワード入力待ち...")
        p_field = wait.until(EC.visibility_of_element_located((By.NAME, "password")))
        p_field.send_keys(os.getenv("X_PASSWORD"))
        p_field.send_keys(Keys.ENTER)
        time.sleep(10)

        print("3. 投稿準備...")
        driver.get("https://x.com/compose/tweet")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="tweetTextarea_0"]')))
        t_box.send_keys(text)
        
        print("4. 投稿実行...")
        btn = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetButton"]')
        btn.click()
        time.sleep(5)
        print("★投稿成功！")

    except Exception as e:
        print(f"!!! エラー発生地点: {driver.current_url}")
        print(f"!!! 詳細: {e}")
    finally:
        driver.quit()

# 他の関数（run_system, load_history等）は以前のままでOKです
