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
    chrome_options.add_argument('--lang=en-US')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        print("--- 接続開始 ---")
        driver.get("https://x.com")
        time.sleep(5)

        auth_token = os.getenv("X_COOKIE_AUTH")
        driver.add_cookie({"name": "auth_token", "value": auth_token, "domain": ".x.com"})
        
        print("→ 投稿画面へ移動")
        driver.get("https://x.com/compose/post")
        time.sleep(10)

        print("→ 投稿内容を入力中...")
        t_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        
        # 文字を入力
        t_box.send_keys(text)
        time.sleep(3)
        
        print("→ キーボード操作(Ctrl+Enter)で投稿を実行...")
        # ボタンを探さず、入力欄に対して「投稿ショートカットキー」を送信します
        t_box.send_keys(Keys.CONTROL, Keys.ENTER)
        
        print("→ 完了待機中（15秒）...")
        time.sleep(15)
        
        if "compose/post" not in driver.current_url:
            print("★投稿成功！画面が正常に遷移しました。")
        else:
            print("!!! 警告: まだ投稿画面です。別の方法でクリックを試みます。")
            btn = driver.find_element(By.XPATH, '//div[@data-testid="tweetButtonInline"] | //button[@data-testid="tweetButton"]')
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(10)

    except Exception as e:
        print(f"!!! 失敗理由: {e}")
    finally:
        driver.quit()

# run_system はそのまま（検証用）で大丈夫です
